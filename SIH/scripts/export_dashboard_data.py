"""
Pre-generates static JSON and JS data assets for the IDR-NAV Dashboard.
Extracts real Ground Truth, Phase 2, and Phase 3 trajectories and metrics
from preprocessed and aligned benchmark CSV files.
"""

import json
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
)

def generate_dashboard_assets():
    print("Generating dashboard data assets from real benchmark outputs...")
    
    data_dir = PROJECT_ROOT / "data" / "processed"
    dash_dir = PROJECT_ROOT / "dashboard" / "data"
    dash_dir.mkdir(parents=True, exist_ok=True)
    
    sequences = ["S-Vta1a", "S-Vta2"]
    out_payload = {}
    
    descriptions = {
        "S-Vta1a": "Driver E (Aggressive) — Mixed UK Motorways & Arterial Roundabouts",
        "S-Vta2": "Independent Test Run — Suburban & Urban Transit Network",
    }
    
    downsample_factors = {
        "S-Vta1a": 25, # ~1,027 points (from 25,676)
        "S-Vta2": 11,  # ~1,000 points (from 10,991)
    }

    for seq in sequences:
        preproc_csv = data_dir / f"{seq}_preprocessed.csv"
        ins_p2_csv = data_dir / f"{seq}_ins.csv"
        aligned_csv = data_dir / f"{seq}_aligned.csv"
        
        df_raw = pd.read_csv(preproc_csv)
        df_p2 = pd.read_csv(ins_p2_csv)
        df_aligned = pd.read_csv(aligned_csv)
        
        verified_dist_m = float(df_raw["cum_distance_m"].iloc[-1])
        duration_s = float(df_raw["elapsed_s"].iloc[-1])
        
        # Compute Phase 3 INS
        aligner = PhoneToVehicleAlignment(AlignmentConfig(initial_samples=30, yaw_mode="leveling_only"))
        R_b_v, info = aligner.estimate_rotation(df_raw)
        
        df_ins_input = df_aligned.copy()
        df_ins_input["lin_ax"] = df_aligned["veh_lin_ax"]
        df_ins_input["lin_ay"] = df_aligned["veh_lin_ay"]
        df_ins_input["lin_az"] = df_aligned["veh_lin_az"]
        df_ins_input["gyro_pitch"] = df_aligned["veh_gyro_x"]
        df_ins_input["gyro_roll"] = df_aligned["veh_gyro_y"]
        df_ins_input["gyro_yaw"] = df_aligned["veh_gyro_z"]
        
        ins_p3 = InertialDeadReckoning(INSConfig(use_android_linear_acc=True, yaw_initialization_mode="sensor_yaw"))
        df_p3 = ins_p3.propagate_sequence(df_ins_input)
        
        m_p2 = compute_ins_metrics(df_p2, total_distance_m=verified_dist_m)
        m_p3 = compute_ins_metrics(df_p3, total_distance_m=verified_dist_m)
        
        step = downsample_factors[seq]
        idx_sampled = np.arange(0, len(df_raw), step)
        if idx_sampled[-1] != len(df_raw) - 1:
            idx_sampled = np.append(idx_sampled, len(df_raw) - 1)
            
        time_s = df_raw["elapsed_s"].iloc[idx_sampled].to_numpy()
        time_min = time_s / 60.0
        
        gt_e = df_raw["east_m"].iloc[idx_sampled].to_numpy()
        gt_n = df_raw["north_m"].iloc[idx_sampled].to_numpy()
        
        p2_e = df_p2["ins_east_m"].iloc[idx_sampled].to_numpy()
        p2_n = df_p2["ins_north_m"].iloc[idx_sampled].to_numpy()
        p2_err = df_p2["pos_error_2d_m"].iloc[idx_sampled].to_numpy() / 1000.0
        
        p3_e = df_p3["ins_east_m"].iloc[idx_sampled].to_numpy()
        p3_n = df_p3["ins_north_m"].iloc[idx_sampled].to_numpy()
        p3_err = df_p3["pos_error_2d_m"].iloc[idx_sampled].to_numpy() / 1000.0
        
        dist_km = df_raw["cum_distance_m"].iloc[idx_sampled].to_numpy() / 1000.0
        speed_kmh = df_raw["gps_speed_kmh"].iloc[idx_sampled].to_numpy() * 3.6
        
        out_payload[seq] = {
            "name": seq,
            "description": descriptions[seq],
            "metrics": {
                "duration_min": round(duration_s / 60.0, 2),
                "duration_s": round(duration_s, 1),
                "total_samples": len(df_raw),
                "distance_km": round(verified_dist_m / 1000.0, 2),
                "distance_m": round(verified_dist_m, 1),
                "peak_speed_kmh": round(float(df_raw["gps_speed_kmh"].max() * 3.6), 2),
                "mean_speed_kmh": round(float(df_raw["gps_speed_kmh"].mean() * 3.6), 2),
                "roll_tilt_deg": round(info["roll_tilt_deg"], 2),
                "pitch_tilt_deg": round(info["pitch_tilt_deg"], 2),
                "det_R": round(info["det_R"], 6),
                "ortho_error": float(f"{info['ortho_error']:.2e}"),
                "p2_final_err_km": round(m_p2["final_pos_error_2d_m"] / 1000.0, 2),
                "p3_final_err_km": round(m_p3["final_pos_error_2d_m"] / 1000.0, 2),
                "p2_rmse_km": round(m_p2["pos_rmse_2d_m"] / 1000.0, 2),
                "p3_rmse_km": round(m_p3["pos_rmse_2d_m"] / 1000.0, 2),
                "p2_drift_pct": round(m_p2["drift_pct_of_distance"], 1),
                "p3_drift_pct": round(m_p3["drift_pct_of_distance"], 1),
                "delta_final_km": round((m_p3["final_pos_error_2d_m"] - m_p2["final_pos_error_2d_m"]) / 1000.0, 2),
                "delta_rmse_km": round((m_p3["pos_rmse_2d_m"] - m_p2["pos_rmse_2d_m"]) / 1000.0, 2),
            },
            "trajectory": {
                "time_s": [round(float(v), 2) for v in time_s],
                "time_min": [round(float(v), 2) for v in time_min],
                "gt_east_m": [round(float(v), 1) for v in gt_e],
                "gt_north_m": [round(float(v), 1) for v in gt_n],
                "p2_east_m": [round(float(v), 1) for v in p2_e],
                "p2_north_m": [round(float(v), 1) for v in p2_n],
                "p3_east_m": [round(float(v), 1) for v in p3_e],
                "p3_north_m": [round(float(v), 1) for v in p3_n],
                "p2_err_km": [round(float(v), 2) for v in p2_err],
                "p3_err_km": [round(float(v), 2) for v in p3_err],
                "distance_km": [round(float(v), 2) for v in dist_km],
                "speed_kmh": [round(float(v), 1) for v in speed_kmh],
            }
        }
        print(f"  Processed {seq}: {len(time_s)} sampled points.")

    # Save to JSON
    json_path = dash_dir / "dashboard_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"Wrote JSON to: {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")
    
    # Save to JS (failsafe for local file:// execution without CORS)
    js_path = dash_dir / "dashboard_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.IDR_DATA = " + json.dumps(out_payload, indent=2) + ";\n")
    print(f"Wrote JS to: {js_path} ({js_path.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    generate_dashboard_assets()
