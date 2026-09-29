"""
Phase 3 Execution Pipeline: Phone-to-Vehicle Alignment (R_b^v)
Estimates SO(3) alignment, transforms IMU streams to vehicle chassis frame (FLU),
generates aligned datasets, executes vehicle-frame INS, compares Phase 2 vs Phase 3,
and produces diagnostic visualizations.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.navigation import (
    AlignmentConfig,
    INSConfig,
    InertialDeadReckoning,
    PhoneToVehicleAlignment,
    compute_ins_metrics,
    plot_alignment_signals,
    plot_phase2_vs_phase3_error,
    plot_phase2_vs_phase3_trajectory,
    validate_rotation_matrix,
)

sys.stdout.reconfigure(encoding="utf-8")


def run_phase3():
    print("=" * 80)
    print("PHASE 3: PHONE-TO-VEHICLE ALIGNMENT (R_b^v) & VEHICLE-FRAME INS EXECUTION")
    print("=" * 80)

    data_dir = PROJECT_ROOT / "data" / "processed"
    output_plot_dir = PROJECT_ROOT / "outputs" / "phase3_plots"
    output_plot_dir.mkdir(parents=True, exist_ok=True)

    sequences = ["S-Vta1a", "S-Vta2"]
    comparison_records = []

    for seq in sequences:
        preproc_csv = data_dir / f"{seq}_preprocessed.csv"
        ins_p2_csv = data_dir / f"{seq}_ins.csv"
        if not preproc_csv.is_file():
            raise FileNotFoundError(f"Missing preprocessed dataset: {preproc_csv}")

        print(f"\n>>> Processing Sequence: {seq}")
        df_raw = pd.read_csv(preproc_csv)
        verified_dist_m = float(df_raw["cum_distance_m"].iloc[-1])
        duration_s = float(df_raw["elapsed_s"].iloc[-1])
        print(f"    Samples: {len(df_raw):,} | Duration: {duration_s:.1f} s ({duration_s/60.0:.2f} min)")
        print(f"    Verified Trajectory Distance: {verified_dist_m:.1f} m ({verified_dist_m/1000.0:.2f} km)")

        # 1. Estimate Phone-to-Vehicle Alignment (R_b^v)
        # We use leveling_only mode as the primary defensible alignment (gravity-based roll/pitch leveling)
        # to ensure zero uncalibrated horizontal acceleration leakage.
        aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode="leveling_only"))
        R_b_v, info = aligner.estimate_rotation(df_raw)

        print("\n--- Estimated Alignment Matrix R_b^v ---")
        print(f"  Roll Tilt:         {info['roll_tilt_deg']:+.2f}°")
        print(f"  Pitch Tilt:        {info['pitch_tilt_deg']:+.2f}°")
        print(f"  Yaw Alignment:     {info['yaw_align_deg']:+.2f}°")
        print(f"  Determinant:       {info['det_R']:.6f} (Target: 1.000000)")
        print(f"  Orthogonality Err: {info['ortho_error']:.2e}")
        print("  Rotation Matrix R_b^v:")
        for row in R_b_v:
            print(f"    [{row[0]:+8.5f}, {row[1]:+8.5f}, {row[2]:+8.5f}]")

        # SO(3) validation check
        is_so3, o_err, d_err = validate_rotation_matrix(R_b_v)
        assert is_so3, f"R_b_v failed SO(3) validation! ortho_err={o_err}, det_err={d_err}"
        print("  ✓ SO(3) Lie Group validation PASSED: R^T R = I, det(R) = +1")

        # 2. Transform sensor signals to Vehicle Frame
        df_aligned = aligner.transform_signals(df_raw, R_b_v)
        aligned_csv_path = data_dir / f"{seq}_aligned.csv"
        df_aligned.to_csv(aligned_csv_path, index=False)
        print(f"\n  [Saved Aligned Dataset CSV] -> {aligned_csv_path} ({aligned_csv_path.stat().st_size / 1e6:.2f} MB)")

        # Sanity check: verify leveled gravity
        f_raw_init = df_raw.loc[:30, ["ax", "ay", "az"]].mean().to_numpy()
        f_veh_init = df_aligned.loc[:30, ["veh_ax", "veh_ay", "veh_az"]].mean().to_numpy()
        print(f"  Initial Raw Specific Force:     [{f_raw_init[0]:.3f}, {f_raw_init[1]:.3f}, {f_raw_init[2]:.3f}] m/s²")
        print(f"  Initial Vehicle Specific Force: [{f_veh_init[0]:.3f}, {f_veh_init[1]:.3f}, {f_veh_init[2]:.3f}] m/s²")
        assert np.isclose(f_veh_init[0], 0.0, atol=1e-1), "Vehicle X specific force should be ~0 at rest"
        assert np.isclose(f_veh_init[1], 0.0, atol=1e-1), "Vehicle Y specific force should be ~0 at rest"
        assert np.isclose(f_veh_init[2], np.linalg.norm(f_raw_init), atol=1e-1), "Vehicle Z should carry full gravity"
        print("  ✓ Leveled gravity strictly directed along Vehicle Up (+Z) axis")

        # 3. Propagate INS using Vehicle-Frame Signals
        # Prepare DataFrame for vehicle-frame INS
        df_ins_input = df_aligned.copy()
        df_ins_input["lin_ax"] = df_aligned["veh_lin_ax"]
        df_ins_input["lin_ay"] = df_aligned["veh_lin_ay"]
        df_ins_input["lin_az"] = df_aligned["veh_lin_az"]
        df_ins_input["gyro_pitch"] = df_aligned["veh_gyro_x"]
        df_ins_input["gyro_roll"] = df_aligned["veh_gyro_y"]
        df_ins_input["gyro_yaw"] = df_aligned["veh_gyro_z"]

        ins_engine = InertialDeadReckoning(INSConfig(use_android_linear_acc=True, yaw_initialization_mode="sensor_yaw"))
        df_p3_ins = ins_engine.propagate_sequence(df_ins_input)
        m_p3 = compute_ins_metrics(df_p3_ins, total_distance_m=verified_dist_m)

        # 4. Load Phase 2 results for direct comparison
        if ins_p2_csv.is_file():
            df_p2_ins = pd.read_csv(ins_p2_csv)
            m_p2 = compute_ins_metrics(df_p2_ins, total_distance_m=verified_dist_m)
        else:
            # Fallback: compute Phase 2 on raw
            ins_p2 = InertialDeadReckoning(INSConfig(use_android_linear_acc=True, yaw_initialization_mode="sensor_yaw"))
            df_p2_ins = ins_p2.propagate_sequence(df_raw)
            m_p2 = compute_ins_metrics(df_p2_ins, total_distance_m=verified_dist_m)

        # Print comparison for this sequence
        print("\n--- Quantitative Comparison: Phase 2 vs Phase 3 ---")
        print(f"  Phase 2 Final 2D Error:    {m_p2['final_pos_error_2d_m']/1000.0:.2f} km | Drift: {m_p2['drift_pct_of_distance']:.1f}% | RMSE: {m_p2['pos_rmse_2d_m']/1000.0:.2f} km")
        print(f"  Phase 3 Final 2D Error:    {m_p3['final_pos_error_2d_m']/1000.0:.2f} km | Drift: {m_p3['drift_pct_of_distance']:.1f}% | RMSE: {m_p3['pos_rmse_2d_m']/1000.0:.2f} km")
        delta_final = (m_p3['final_pos_error_2d_m'] - m_p2['final_pos_error_2d_m']) / 1000.0
        delta_rmse = (m_p3['pos_rmse_2d_m'] - m_p2['pos_rmse_2d_m']) / 1000.0
        print(f"  Delta Final Error (P3-P2): {delta_final:+.2f} km")
        print(f"  Delta 2D RMSE (P3-P2):     {delta_rmse:+.2f} km")

        comparison_records.append({
            "Sequence": seq,
            "P2_Final_Err_km": m_p2['final_pos_error_2d_m'] / 1000.0,
            "P3_Final_Err_km": m_p3['final_pos_error_2d_m'] / 1000.0,
            "Delta_Final_km": delta_final,
            "P2_RMSE_km": m_p2['pos_rmse_2d_m'] / 1000.0,
            "P3_RMSE_km": m_p3['pos_rmse_2d_m'] / 1000.0,
            "Delta_RMSE_km": delta_rmse,
            "P2_Drift_Pct": m_p2['drift_pct_of_distance'],
            "P3_Drift_Pct": m_p3['drift_pct_of_distance'],
            "P2_Mean_Vel_mps": m_p2.get('mean_vel_error_mps', 0.0),
            "P3_Mean_Vel_mps": m_p3.get('mean_vel_error_mps', 0.0),
        })

        # 5. Generate Phase 3 Visualizations
        print("\n  [Generating Phase 3 Diagnostic Plots]")
        t_mid = df_aligned["elapsed_s"].max() / 2.0
        p1 = output_plot_dir / f"01_aligned_sensor_signals_{seq}.png"
        plot_alignment_signals(df_aligned, sequence_name=seq, time_window_s=(t_mid, t_mid + 120.0), save_path=p1)

        p2 = output_plot_dir / f"02_phase2_vs_phase3_trajectory_{seq}.png"
        plot_phase2_vs_phase3_trajectory(df_p2_ins, df_p3_ins, sequence_name=seq, save_path=p2)

        p3 = output_plot_dir / f"03_phase2_vs_phase3_error_{seq}.png"
        plot_phase2_vs_phase3_error(df_p2_ins, df_p3_ins, sequence_name=seq, save_path=p3)

    # Summary table
    print("\n" + "=" * 80)
    print("PHASE 2 VS PHASE 3 SUMMARY TABLE")
    print("=" * 80)
    summary_df = pd.DataFrame(comparison_records)
    print(summary_df.to_string(index=False))

    print("\n" + "=" * 80)
    print("PHASE 3 EXECUTION & VALIDATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_phase3()
