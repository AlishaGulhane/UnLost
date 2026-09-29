"""
Unit and Integration Tests for Phase 3: Phone-to-Vehicle Alignment (R_b^v)
Validates SO(3) properties, gravity leveling, signal transformations,
NaN/Inf robustness, and execution on real IO-VNBD benchmark sequences.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.navigation import (
    AlignmentConfig,
    PhoneToVehicleAlignment,
    align_vectors_rodrigues,
    validate_rotation_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_VTA1A = PROJECT_ROOT / "data" / "processed" / "S-Vta1a_preprocessed.csv"
REAL_VTA2 = PROJECT_ROOT / "data" / "processed" / "S-Vta2_preprocessed.csv"


def test_identity_rotation():
    """Verify that identical vectors produce an exact identity rotation matrix."""
    v = np.array([0.0, 0.0, 9.81])
    R = align_vectors_rodrigues(v, v)
    assert np.allclose(R, np.eye(3), atol=1e-10)
    assert np.isclose(np.linalg.det(R), 1.0, atol=1e-10)
    assert np.allclose(R @ v, v, atol=1e-10)


def test_known_rotation():
    """Verify known 90-degree rotations around coordinate axes."""
    # Rotate +X into +Y (90 degree rotation around +Z)
    vx = np.array([1.0, 0.0, 0.0])
    vy = np.array([0.0, 1.0, 0.0])
    R_z = align_vectors_rodrigues(vx, vy)
    assert np.allclose(R_z @ vx, vy, atol=1e-10)
    assert np.isclose(np.linalg.det(R_z), 1.0, atol=1e-10)
    assert np.allclose(R_z @ R_z.T, np.eye(3), atol=1e-10)

    # Rotate +Z into +X (90 degree rotation around +Y)
    vz = np.array([0.0, 0.0, 1.0])
    R_y = align_vectors_rodrigues(vz, vx)
    assert np.allclose(R_y @ vz, vx, atol=1e-10)
    assert np.isclose(np.linalg.det(R_y), 1.0, atol=1e-10)


def test_so3_validity():
    """Verify SO(3) validation function for valid and invalid matrices."""
    # Valid orthogonal matrix with det = +1
    theta = 0.35
    R_valid = np.array([
        [np.cos(theta), -np.sin(theta), 0.0],
        [np.sin(theta), np.cos(theta), 0.0],
        [0.0, 0.0, 1.0],
    ])
    is_valid, ortho_err, det_err = validate_rotation_matrix(R_valid)
    assert is_valid
    assert ortho_err < 1e-10
    assert det_err < 1e-10

    # Reflection matrix (det = -1, not in SO(3))
    R_reflection = np.diag([1.0, 1.0, -1.0])
    is_valid_ref, _, _ = validate_rotation_matrix(R_reflection)
    assert not is_valid_ref

    # Non-orthogonal matrix
    R_non_ortho = np.array([[1.0, 0.5, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    is_valid_no, _, _ = validate_rotation_matrix(R_non_ortho)
    assert not is_valid_no


def test_gravity_direction_leveling():
    """Verify that arbitrary tilted specific force vectors are leveled to strictly point along +Z."""
    test_forces = [
        np.array([-0.05, -0.02, 9.81]),  # Quasi-flat (S-Vta1a)
        np.array([-1.50, -2.20, 9.40]),  # Tilted mount (S-Vta2)
        np.array([3.00, -4.00, 8.00]),   # Highly tilted phone
    ]
    z_target = np.array([0.0, 0.0, 1.0])

    for f_in in test_forces:
        R_level = align_vectors_rodrigues(f_in, z_target)
        f_leveled = R_level @ f_in
        expected_mag = np.linalg.norm(f_in)

        # X and Y components should be zero (within machine precision)
        assert np.isclose(f_leveled[0], 0.0, atol=1e-9)
        assert np.isclose(f_leveled[1], 0.0, atol=1e-9)
        # Z component should carry the full magnitude
        assert np.isclose(f_leveled[2], expected_mag, atol=1e-9)
        # Strict SO(3) check
        assert np.allclose(R_level @ R_level.T, np.eye(3), atol=1e-10)
        assert np.isclose(np.linalg.det(R_level), 1.0, atol=1e-10)


def test_nan_inf_handling():
    """Verify safe fallback for degenerate zero or near-zero inputs."""
    zero_vec = np.zeros(3)
    target = np.array([0.0, 0.0, 1.0])
    R_deg = align_vectors_rodrigues(zero_vec, target)
    assert np.allclose(R_deg, np.eye(3), atol=1e-10)
    assert not np.isnan(R_deg).any()
    assert not np.isinf(R_deg).any()


def test_non_overwriting_raw_signals():
    """Verify that transform_signals preserves all raw columns and appends veh_* columns."""
    df_dummy = pd.DataFrame({
        "time_ms": [0, 100, 200],
        "elapsed_s": [0.0, 0.1, 0.2],
        "dt_s": [0.1, 0.1, 0.1],
        "ax": [0.1, 0.2, 0.3],
        "ay": [0.4, 0.5, 0.6],
        "az": [9.8, 9.8, 9.8],
        "lin_ax": [0.1, 0.2, 0.3],
        "lin_ay": [0.4, 0.5, 0.6],
        "lin_az": [0.0, 0.0, 0.0],
        "grav_x": [0.0, 0.0, 0.0],
        "grav_y": [0.0, 0.0, 0.0],
        "grav_z": [9.8, 9.8, 9.8],
        "gyro_pitch": [0.01, 0.02, 0.03],
        "gyro_roll": [0.04, 0.05, 0.06],
        "gyro_yaw": [0.07, 0.08, 0.09],
    })

    R_dummy = np.eye(3)
    aligner = PhoneToVehicleAlignment()
    df_transformed = aligner.transform_signals(df_dummy, R_dummy)

    # Raw columns still intact
    for col in df_dummy.columns:
        assert col in df_transformed.columns
        assert np.allclose(df_transformed[col], df_dummy[col])

    # Transformed columns exist
    veh_cols = [
        "veh_ax", "veh_ay", "veh_az",
        "veh_lin_ax", "veh_lin_ay", "veh_lin_az",
        "veh_grav_x", "veh_grav_y", "veh_grav_z",
        "veh_gyro_x", "veh_gyro_y", "veh_gyro_z",
    ]
    for vcol in veh_cols:
        assert vcol in df_transformed.columns
        assert not df_transformed[vcol].isna().any()


def test_short_real_data_alignment():
    """Verify alignment execution on a slice of real S-Vta1a benchmark data."""
    assert REAL_VTA1A.is_file(), f"Real file {REAL_VTA1A} missing!"
    df_real = pd.read_csv(REAL_VTA1A).iloc[:200].copy()

    aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode="leveling_only"))
    R_b_v, info = aligner.estimate_rotation(df_real)

    assert info["is_valid_so3"] == 1.0
    assert abs(info["det_R"] - 1.0) < 1e-6
    assert info["ortho_error"] < 1e-6

    df_aligned = aligner.transform_signals(df_real, R_b_v)
    assert len(df_aligned) == 200
    assert "veh_ax" in df_aligned.columns
    assert "veh_lin_ax" in df_aligned.columns
    assert "veh_gyro_z" in df_aligned.columns


def test_full_svta1a_alignment():
    """Verify full-sequence alignment on S-Vta1a."""
    assert REAL_VTA1A.is_file()
    df_full = pd.read_csv(REAL_VTA1A)

    aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode="leveling_only"))
    R_b_v, info = aligner.estimate_rotation(df_full)

    assert abs(info["det_R"] - 1.0) < 1e-6
    assert info["ortho_error"] < 1e-6
    # S-Vta1a phone is nearly level (< 0.5 deg tilt)
    assert abs(info["roll_tilt_deg"]) < 1.0
    assert abs(info["pitch_tilt_deg"]) < 1.0

    df_aligned = aligner.transform_signals(df_full, R_b_v)
    assert len(df_aligned) == len(df_full)
    assert not df_aligned["veh_ax"].isna().any()
    assert not np.isinf(df_aligned["veh_ax"]).any()


def test_full_svta2_alignment():
    """Verify full-sequence alignment on S-Vta2."""
    assert REAL_VTA2.is_file()
    df_full = pd.read_csv(REAL_VTA2)

    aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode="leveling_only"))
    R_b_v, info = aligner.estimate_rotation(df_full)

    assert abs(info["det_R"] - 1.0) < 1e-6
    assert info["ortho_error"] < 1e-6
    # S-Vta2 phone has notable mount tilt (roll tilt ~10-13 deg)
    assert abs(info["roll_tilt_deg"]) > 5.0

    df_aligned = aligner.transform_signals(df_full, R_b_v)
    assert len(df_aligned) == len(df_full)
    assert not df_aligned["veh_ax"].isna().any()
    assert not np.isinf(df_aligned["veh_ax"]).any()
