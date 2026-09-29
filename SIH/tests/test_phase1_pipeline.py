"""
Unit and Integration Tests for Phase 1: IO-VNBD Data Pipeline
"""

from pathlib import Path
import numpy as np
import pytest

from src.iovnbd import (
    CANONICAL_PHONE_FIELDS,
    GRAVITY_STANDARD,
    NOMINAL_IMU_HZ,
    SMARTPHONE_RAW_COLUMNS,
    WGS84_A,
    IOVNBDLoader,
    NavigationPreprocessor,
    enu_to_geodetic,
    geodetic_to_enu,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = PROJECT_ROOT / "data" / "raw" / "S-Vta1a.csv"


def test_constants_and_schemas():
    assert len(SMARTPHONE_RAW_COLUMNS) == 24
    assert len(CANONICAL_PHONE_FIELDS) == 24
    assert NOMINAL_IMU_HZ == 10.0
    assert np.isclose(GRAVITY_STANDARD, 9.80665, atol=1e-4)
    assert np.isclose(WGS84_A, 6378137.0, atol=1e-1)


def test_geodetic_enu_roundtrip():
    # Test known coordinates (e.g. Coventry, UK area)
    lat0, lon0, alt0 = 52.40166, -1.50529, 147.5
    test_lats = np.array([52.40166, 52.40500, 52.41000, 52.39500])
    test_lons = np.array([-1.50529, -1.50000, -1.49500, -1.51000])
    test_alts = np.array([147.5, 150.0, 160.0, 140.0])

    east, north, up = geodetic_to_enu(test_lats, test_lons, test_alts, lat0, lon0, alt0)

    # Origin should project to (0, 0, 0)
    assert np.isclose(east[0], 0.0, atol=1e-3)
    assert np.isclose(north[0], 0.0, atol=1e-3)
    assert np.isclose(up[0], 0.0, atol=1e-3)

    # Roundtrip conversion
    lat_rt, lon_rt, alt_rt = enu_to_geodetic(east, north, up, lat0, lon0, alt0)

    assert np.allclose(test_lats, lat_rt, atol=1e-9)
    assert np.allclose(test_lons, lon_rt, atol=1e-9)
    assert np.allclose(test_alts, alt_rt, atol=1e-4)


def test_dataset_loader():
    assert SAMPLE_FILE.is_file(), f"Test file {SAMPLE_FILE} missing!"

    loader = IOVNBDLoader(data_dir=SAMPLE_FILE.parent)
    df, meta = loader.load_smartphone_sequence(SAMPLE_FILE)

    assert meta.total_samples > 20000
    assert meta.duration_s > 2000.0 # > 33 minutes
    assert np.isclose(meta.effective_hz, 10.0, atol=0.2)
    assert len(df.columns) >= 24

    # Timestamp monotonicity
    assert (df["time_ms"].diff().dropna() >= 0).all()
    assert (df["elapsed_s"].diff().dropna() >= 0).all()

    # Accelerometer and Gyroscope values exist and are reasonable
    assert df["ax"].notna().all()
    assert df["ay"].notna().all()
    assert df["az"].notna().all()
    assert df["gyro_yaw"].notna().all()


def test_preprocessor():
    loader = IOVNBDLoader(data_dir=SAMPLE_FILE.parent)
    df, _ = loader.load_smartphone_sequence(SAMPLE_FILE)

    preprocessor = NavigationPreprocessor(target_hz=10.0)
    df_proc = preprocessor.preprocess_sequence(df, apply_lowpass=False)

    # Check that ENU coordinates exist
    assert "east_m" in df_proc.columns
    assert "north_m" in df_proc.columns
    assert "up_m" in df_proc.columns

    # Origin should be near zero
    assert np.isclose(df_proc["east_m"].iloc[0], 0.0, atol=1e-2)
    assert np.isclose(df_proc["north_m"].iloc[0], 0.0, atol=1e-2)

    # Linear acceleration (gravity subtracted)
    assert "lin_ax" in df_proc.columns
    assert "lin_ay" in df_proc.columns
    assert "lin_az" in df_proc.columns

    # Total specific force magnitude around 1g (~9.81 m/s^2)
    mean_acc = df_proc["acc_norm"].mean()
    assert 9.0 < mean_acc < 11.5, f"Unexpected mean acceleration: {mean_acc}"


def test_sequence_splitting():
    loader = IOVNBDLoader(data_dir=SAMPLE_FILE.parent)
    df, _ = loader.load_smartphone_sequence(SAMPLE_FILE)

    train_df, val_df, test_df = loader.split_sequence(df, 0.7, 0.15)
    total_len = len(df)

    assert len(train_df) + len(val_df) + len(test_df) == total_len
    # Temporal order maintained
    assert train_df["elapsed_s"].iloc[-1] <= val_df["elapsed_s"].iloc[0]
    assert val_df["elapsed_s"].iloc[-1] <= test_df["elapsed_s"].iloc[0]
