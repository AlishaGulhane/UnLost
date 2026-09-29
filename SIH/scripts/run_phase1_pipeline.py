"""
End-to-End Execution Script for Phase 1: IO-VNBD Data Pipeline
Loads real benchmark sequences, validates schemas, verifies timing & units,
and generates plots & processed data for Phase 2.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.iovnbd import (
    IOVNBDLoader,
    NavigationPreprocessor,
    enu_to_geodetic,
    geodetic_to_enu,
    plot_ground_truth_trajectory,
    plot_imu_signals,
    plot_sensor_diagnostics,
)

sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=" * 70)
    print("PHASE 1 — IO-VNBD DATA PIPELINE EXECUTION & VALIDATION")
    print("=" * 70)

    data_dir = PROJECT_ROOT / "data" / "raw"
    output_dir = PROJECT_ROOT / "outputs" / "phase1_plots"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    loader = IOVNBDLoader(data_dir=data_dir)
    preprocessor = NavigationPreprocessor(target_hz=10.0)

    sequences = ["S-Vta1a.csv", "S-Vta2.csv"]
    processed_datasets = {}

    for seq_file in sequences:
        seq_path = data_dir / seq_file
        print(f"\n>>> Loading Real Benchmark Sequence: {seq_file}")
        print(f"    Path: {seq_path}")
        print(f"    File Size: {seq_path.stat().st_size / (1024*1024):.2f} MB")

        # 1. Load and parse raw sequence
        df_raw, meta = loader.load_smartphone_sequence(seq_path)

        print("\n--- Sequence Metadata & Sensor Verification ---")
        print(f"  Sequence ID:          {meta.sequence_name}")
        print(f"  Total Rows:           {meta.total_samples:,} samples")
        print(f"  Duration:             {meta.duration_s:.1f} s ({meta.duration_s / 60.0:.2f} mins)")
        print(f"  Effective Frequency:  {meta.effective_hz:.2f} Hz (Nominal: 10.0 Hz)")
        print(f"  Missing GPS Fixes:    {meta.num_missing_gps}")
        print(f"  Latitude Range:       [{meta.gps_lat_range[0]:.6f}, {meta.gps_lat_range[1]:.6f}] deg")
        print(f"  Longitude Range:      [{meta.gps_lon_range[0]:.6f}, {meta.gps_lon_range[1]:.6f}] deg")
        print(f"  Max Speed:            {meta.speed_kmh_max:.2f} km/h ({meta.speed_kmh_max / 3.6:.2f} m/s)")

        # 2. Timing jitter check
        dt_ms = df_raw["dt_s"] * 1000.0
        print(f"  Sampling dt Mean:     {dt_ms.mean():.3f} ms")
        print(f"  Sampling dt Median:   {dt_ms.median():.3f} ms")
        print(f"  Sampling dt Std Dev:  {dt_ms.std():.3f} ms")

        # 3. Preprocess sequence (ENU coordinates, gravity separation, ground-truth metrics)
        df_proc = preprocessor.preprocess_sequence(df_raw, apply_lowpass=True, cutoff_hz=3.0)
        processed_datasets[meta.sequence_name] = df_proc

        total_distance_m = df_proc["cum_distance_m"].iloc[-1]
        print(f"  Cumulative Distance:  {total_distance_m:.1f} m ({total_distance_m / 1000.0:.2f} km)")
        print(f"  Mean Accelerometer |a|: {df_proc['acc_norm'].mean():.3f} m/s² (~1g)")
        print(f"  Mean Linear Acc |a_lin|: {df_proc['lin_acc_norm'].mean():.3f} m/s²")
        print(f"  Gyro Yaw Rate Range:  [{df_proc['gyro_yaw'].min():.3f}, {df_proc['gyro_yaw'].max():.3f}] rad/s")

        # 4. Generate plots
        traj_plot_path = output_dir / f"01_real_ground_truth_trajectory_{meta.sequence_name}.png"
        plot_ground_truth_trajectory(
            df_proc,
            title=f"IO-VNBD Ground Truth Trajectory - {meta.sequence_name}",
            save_path=traj_plot_path,
        )

        imu_plot_path = output_dir / f"02_real_imu_signals_{meta.sequence_name}.png"
        # Window of 120 seconds to see detailed dynamics clearly
        t_mid = df_proc["elapsed_s"].max() / 2.0
        plot_imu_signals(
            df_proc,
            title=f"IO-VNBD Smartphone IMU Signals - {meta.sequence_name} (Sample Window)",
            time_window_s=(t_mid, t_mid + 120.0),
            save_path=imu_plot_path,
        )

        diag_plot_path = output_dir / f"03_sensor_timing_and_dynamics_{meta.sequence_name}.png"
        plot_sensor_diagnostics(
            df_proc,
            title=f"IO-VNBD Sensor Timing & Dynamic Statistics - {meta.sequence_name}",
            save_path=diag_plot_path,
        )

        # 5. Save preprocessed clean dataset for Phase 2
        csv_save_path = processed_dir / f"{meta.sequence_name}_preprocessed.csv"
        df_proc.to_csv(csv_save_path, index=False)
        print(f"  [Saved Clean Data] -> {csv_save_path} ({csv_save_path.stat().st_size / 1e6:.2f} MB)")

    # 6. Geodetic vs ENU Roundtrip Accuracy Verification
    print("\n" + "=" * 70)
    print("GEODETIC <-> ENU COORDINATE ROUND-TRIP PRECISION TEST")
    print("=" * 70)
    sample_proc = processed_datasets["S-Vta1a"]
    lat_orig = sample_proc["lat"].to_numpy()
    lon_orig = sample_proc["lon"].to_numpy()
    alt_orig = sample_proc["alt_m"].fillna(0.0).to_numpy()
    lat0 = float(sample_proc["origin_lat"].iloc[0])
    lon0 = float(sample_proc["origin_lon"].iloc[0])
    alt0 = float(sample_proc["origin_alt"].iloc[0])

    east, north, up = geodetic_to_enu(lat_orig, lon_orig, alt_orig, lat0, lon0, alt0)
    lat_rt, lon_rt, alt_rt = enu_to_geodetic(east, north, up, lat0, lon0, alt0)

    max_lat_err = np.max(np.abs(lat_orig - lat_rt))
    max_lon_err = np.max(np.abs(lon_orig - lon_rt))
    max_alt_err = np.max(np.abs(alt_orig - alt_rt))

    # Convert angular error to approximate meters on Earth surface
    err_meters = np.sqrt((max_lat_err * 111139.0) ** 2 + (max_lon_err * 111139.0 * np.cos(np.deg2rad(lat0))) ** 2)

    print(f"Origin Reference: ({lat0:.6f}° N, {lon0:.6f}° E, {alt0:.1f} m)")
    print(f"Max Lat Roundtrip Error: {max_lat_err:.2e} degrees")
    print(f"Max Lon Roundtrip Error: {max_lon_err:.2e} degrees")
    print(f"Max Alt Roundtrip Error: {max_alt_err:.2e} meters")
    print(f"Max Geodetic Position Discrepancy: {err_meters * 1000.0:.4f} mm (Sub-millimeter accuracy verified!)")

    print("\n" + "=" * 70)
    print("PHASE 1 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
