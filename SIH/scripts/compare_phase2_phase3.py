"""
Compare Phase 2 (Body-Frame INS) vs Phase 3 (Aligned Vehicle-Frame INS)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.navigation.alignment import PhoneToVehicleAlignment, AlignmentConfig
from src.navigation.ins import INSConfig, InertialDeadReckoning, compute_ins_metrics

def compare():
    for seq in ["S-Vta1a", "S-Vta2"]:
        raw_csv = PROJECT_ROOT / "data" / "processed" / f"{seq}_preprocessed.csv"
        df = pd.read_csv(raw_csv)
        verified_dist = float(df["cum_distance_m"].iloc[-1])
        
        print("\n" + "=" * 80)
        print(f"EVALUATING: {seq} (Verified Distance: {verified_dist/1000.0:.2f} km)")
        print("=" * 80)
        
        # 1. Phase 2: Phone-frame INS baseline
        ins_p2 = InertialDeadReckoning(INSConfig(use_android_linear_acc=True, yaw_initialization_mode="sensor_yaw"))
        df_p2 = ins_p2.propagate_sequence(df)
        m_p2 = compute_ins_metrics(df_p2, total_distance_m=verified_dist)
        
        # 2. Phase 3: Phone-to-Vehicle Alignment
        # Try leveling only and motion acceleration
        for yaw_mode in ["leveling_only", "motion_acceleration"]:
            aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode=yaw_mode))
            R_b_v, info = aligner.estimate_rotation(df)
            df_aligned = aligner.transform_signals(df, R_b_v)
            
            # Run INS on vehicle frame
            # Temporary manual setup: map veh_* columns to lin_a and gyro
            df_ins_veh = df_aligned.copy()
            df_ins_veh["lin_ax"] = df_aligned["veh_lin_ax"]
            df_ins_veh["lin_ay"] = df_aligned["veh_lin_ay"]
            df_ins_veh["lin_az"] = df_aligned["veh_lin_az"]
            df_ins_veh["gyro_pitch"] = df_aligned["veh_gyro_x"]
            df_ins_veh["gyro_roll"] = df_aligned["veh_gyro_y"]
            df_ins_veh["gyro_yaw"] = df_aligned["veh_gyro_z"]
            
            ins_p3 = InertialDeadReckoning(INSConfig(use_android_linear_acc=True, yaw_initialization_mode="sensor_yaw"))
            df_p3 = ins_p3.propagate_sequence(df_ins_veh)
            m_p3 = compute_ins_metrics(df_p3, total_distance_m=verified_dist)
            
            print(f"\n--- Phase 3 (Yaw Mode: {yaw_mode}) ---")
            print(f"R_b_v info: roll_tilt={info['roll_tilt_deg']:.2f}°, pitch_tilt={info['pitch_tilt_deg']:.2f}°, yaw_align={info['yaw_align_deg']:.2f}°")
            print(f"Phase 2 Final 2D Error: {m_p2['final_pos_error_2d_m']/1000.0:.2f} km | Drift: {m_p2['drift_pct_of_distance']:.1f}% | RMSE: {m_p2['pos_rmse_2d_m']/1000.0:.2f} km")
            print(f"Phase 3 Final 2D Error: {m_p3['final_pos_error_2d_m']/1000.0:.2f} km | Drift: {m_p3['drift_pct_of_distance']:.1f}% | RMSE: {m_p3['pos_rmse_2d_m']/1000.0:.2f} km")
            diff = m_p3['final_pos_error_2d_m'] - m_p2['final_pos_error_2d_m']
            print(f"Delta Error (P3 - P2): {diff/1000.0:+.2f} km")

if __name__ == "__main__":
    compare()
