"""
Phase 2 Execution Pipeline: Classical Strapdown INS Dead Reckoning
Propagates S-Vta1a and S-Vta2, verifies numerical sanity,
evaluates pure INS drift against ground truth, and generates diagnostic plots.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.navigation import (
    INSConfig,
    InertialDeadReckoning,
    compute_ins_metrics,
    plot_orientation_profiles,
    plot_position_error_vs_distance,
    plot_position_error_vs_time,
    plot_trajectory_comparison,
    plot_velocity_comparison,
)

sys.stdout.reconfigure(encoding="utf-8")


def run_phase2():
    print("=" * 80)
    print("PHASE 2: PURE CLASSICAL INS / DEAD RECKONING BASELINE EXECUTION")
    print("=" * 80)

    data_dir = PROJECT_ROOT / "data" / "processed"
    output_plot_dir = PROJECT_ROOT / "outputs" / "phase2_plots"
    output_plot_dir.mkdir(parents=True, exist_ok=True)

    sequences = ["S-Vta1a", "S-Vta2"]
    ins_results = {}
    metrics_summary = {}

    for seq in sequences:
        input_csv = data_dir / f"{seq}_preprocessed.csv"
        if not input_csv.is_file():
            raise FileNotFoundError(f"Missing preprocessed dataset: {input_csv}")

        print(f"\n>>> Running Pure Classical INS Propagation for: {seq}")
        print(f"    Input file: {input_csv}")
        df_preprocessed = pd.read_csv(input_csv)

        n_samples = len(df_preprocessed)
        duration_s = float(df_preprocessed["elapsed_s"].iloc[-1])
        verified_dist_m = float(df_preprocessed["cum_distance_m"].iloc[-1])
        print(f"    Samples: {n_samples:,} | Duration: {duration_s:.1f} s ({duration_s/60.0:.2f} min)")
        print(f"    Independently Verified Travelled Distance: {verified_dist_m:.1f} m ({verified_dist_m/1000.0:.2f} km)")

        # Configure pure INS: strapdown propagation using accelerometer & gyroscope
        config = INSConfig(
            use_android_linear_acc=True,
            gravity_magnitude=9.80665,
            integration_method="trapezoidal",
            initial_alignment_samples=30,
            yaw_initialization_mode="sensor_yaw",
        )
        ins = InertialDeadReckoning(config=config)

        # Propagate sequence
        df_ins = ins.propagate_sequence(df_preprocessed)
        ins_results[seq] = df_ins

        # --- Numerical Sanity Checks ---
        print("\n    [Performing Numerical Sanity Checks]")
        # 1. No unexpected NaNs or Infs
        numeric_cols = [c for c in df_ins.columns if df_ins[c].dtype in (np.float64, np.float32, np.int64)]
        nan_counts = df_ins[numeric_cols].isna().sum().sum()
        inf_counts = np.isinf(df_ins[numeric_cols].to_numpy()).sum()
        assert nan_counts == 0, f"Found {nan_counts} unexpected NaN values in INS output!"
        assert inf_counts == 0, f"Found {inf_counts} unexpected Inf values in INS output!"
        print("    ✓ No NaN or Infinite values detected across all columns")

        # 2. Monotonic timestamps
        assert (df_ins["time_ms"].diff().dropna() >= 0).all(), "Timestamps are not strictly non-decreasing!"
        assert (df_ins["elapsed_s"].diff().dropna() >= 0).all(), "Elapsed time is not monotonic!"
        print("    ✓ Timestamps remain strictly monotonic")

        # 3. Output length matches input
        assert len(df_ins) == n_samples, f"Output length mismatch: {len(df_ins)} vs {n_samples}"
        print(f"    ✓ Output sample count ({len(df_ins):,}) matches preprocessed input exactly")

        # 4. Position starts at origin
        assert np.isclose(df_ins["ins_east_m"].iloc[0], 0.0, atol=1e-3), "East origin does not start at 0!"
        assert np.isclose(df_ins["ins_north_m"].iloc[0], 0.0, atol=1e-3), "North origin does not start at 0!"
        assert np.isclose(df_ins["ins_up_m"].iloc[0], 0.0, atol=1e-3), "Up origin does not start at 0!"
        print("    ✓ Position strictly starts from origin (0, 0, 0)")

        # 5. Quaternion normalization
        quat_norms = np.sqrt(
            df_ins["ins_qw"]**2 + df_ins["ins_qx"]**2 + df_ins["ins_qy"]**2 + df_ins["ins_qz"]**2
        )
        max_quat_dev = float(np.max(np.abs(quat_norms - 1.0)))
        assert max_quat_dev < 1e-5, f"Quaternion norm deviates from unity by {max_quat_dev:.2e}"
        print(f"    ✓ Quaternion unit norm maintained throughout (max deviation: {max_quat_dev:.2e})")

        # 6. Finite velocity and position
        assert np.all(np.isfinite(df_ins[["ins_east_m", "ins_north_m", "ins_up_m"]].to_numpy()))
        assert np.all(np.isfinite(df_ins[["ins_ve_mps", "ins_vn_mps", "ins_vu_mps"]].to_numpy()))
        print("    ✓ Velocities and positions remain finite throughout entire duration")

        # Calculate quantitative metrics
        metrics = compute_ins_metrics(df_ins, total_distance_m=verified_dist_m)
        metrics_summary[seq] = metrics

        print("\n--- Quantitative Pure INS Performance Metrics ---")
        print(f"  Final 2D Position Error:   {metrics['final_pos_error_2d_m']:.2f} m ({metrics['final_pos_error_2d_m']/1000.0:.2f} km)")
        print(f"  Final 3D Position Error:   {metrics['final_pos_error_3d_m']:.2f} m ({metrics['final_pos_error_3d_m']/1000.0:.2f} km)")
        print(f"  Position 2D RMSE:          {metrics['pos_rmse_2d_m']:.2f} m ({metrics['pos_rmse_2d_m']/1000.0:.2f} km)")
        print(f"  Mean 2D Position Error:    {metrics['mean_pos_error_2d_m']:.2f} m ({metrics['mean_pos_error_2d_m']/1000.0:.2f} km)")
        print(f"  Max 2D Position Error:     {metrics['max_pos_error_2d_m']:.2f} m ({metrics['max_pos_error_2d_m']/1000.0:.2f} km)")
        print(f"  Drift % of Verified Dist:  {metrics['drift_pct_of_distance']:.2f}%")
        print(f"  Mean Velocity Error:       {metrics.get('mean_vel_error_mps', 0.0):.2f} m/s")
        print(f"  Max Velocity Error:        {metrics.get('max_vel_error_mps', 0.0):.2f} m/s")
        print(f"  Mean Heading Error:        {metrics.get('mean_heading_error_deg', 0.0):.2f}°")

        # Save INS output CSV
        out_csv_path = data_dir / f"{seq}_ins.csv"
        df_ins.to_csv(out_csv_path, index=False)
        print(f"\n  [Saved INS Output CSV] -> {out_csv_path} ({out_csv_path.stat().st_size / 1e6:.2f} MB)")

        # --- Generate Required Visualizations ---
        print("\n  [Generating Phase 2 Diagnostic Visualizations]")
        p1 = output_plot_dir / f"01_trajectory_comparison_{seq}.png"
        plot_trajectory_comparison(df_ins, sequence_name=seq, save_path=p1)

        p2 = output_plot_dir / f"02_position_error_vs_time_{seq}.png"
        plot_position_error_vs_time(df_ins, sequence_name=seq, save_path=p2)

        p3 = output_plot_dir / f"03_drift_vs_distance_{seq}.png"
        plot_position_error_vs_distance(df_ins, sequence_name=seq, save_path=p3)

        p4 = output_plot_dir / f"04_velocity_comparison_{seq}.png"
        plot_velocity_comparison(df_ins, sequence_name=seq, save_path=p4)

        p5 = output_plot_dir / f"05_orientation_profiles_{seq}.png"
        plot_orientation_profiles(df_ins, sequence_name=seq, save_path=p5)

    print("\n" + "=" * 80)
    print("PHASE 2 SUMMARY COMPARISON TABLE")
    print("=" * 80)
    summary_df = pd.DataFrame(metrics_summary).T
    cols_to_show = [
        "final_pos_error_2d_m",
        "pos_rmse_2d_m",
        "mean_pos_error_2d_m",
        "max_pos_error_2d_m",
        "drift_pct_of_distance",
        "mean_vel_error_mps",
        "max_vel_error_mps",
        "mean_heading_error_deg",
    ]
    print(summary_df[cols_to_show].to_string())
    print("\nPhase 2 INS propagation and ground truth comparison completed successfully!")


if __name__ == "__main__":
    run_phase2()
