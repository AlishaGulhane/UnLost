"""
Phase 3 Exploratory Analysis: Phone-to-Vehicle Alignment
Inspects gravity leveling, longitudinal acceleration, and yaw alignment on real IO-VNBD data.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def analyze_sequence_alignment(seq_name: str):
    csv_path = PROJECT_ROOT / "data" / "processed" / f"{seq_name}_preprocessed.csv"
    df = pd.read_csv(csv_path)
    
    print("=" * 80)
    print(f"ALIGNMENT ANALYSIS FOR: {seq_name} ({len(df)} samples)")
    print("=" * 80)
    
    # 1. Stationary leveling: first 50 samples
    n_stat = 50
    fx0 = df.loc[:n_stat, "ax"].mean()
    fy0 = df.loc[:n_stat, "ay"].mean()
    fz0 = df.loc[:n_stat, "az"].mean()
    g_norm = np.sqrt(fx0**2 + fy0**2 + fz0**2)
    
    print(f"Stationary specific force (first {n_stat} samples):")
    print(f"  fx0={fx0:.4f}, fy0={fy0:.4f}, fz0={fz0:.4f} m/s^2 (norm={g_norm:.4f})")
    
    # Unit vertical vector in phone body frame
    z_b = np.array([fx0, fy0, fz0]) / g_norm
    print(f"  Unit vertical vector z_b: [{z_b[0]:.4f}, {z_b[1]:.4f}, {z_b[2]:.4f}]")
    
    # Pitch and roll angles
    pitch_level = np.arctan2(-fx0, np.sqrt(fy0**2 + fz0**2))
    roll_level = np.arctan2(fy0, fz0)
    print(f"  Leveling angles: pitch={np.rad2deg(pitch_level):.2f}°, roll={np.rad2deg(roll_level):.2f}°")
    
    # 2. Horizontal acceleration during vehicle motion
    # Use verified speed (in gps_speed_kmh, which is m/s)
    speed_mps = df["gps_speed_kmh"].to_numpy()
    dt = df["dt_s"].to_numpy()
    valid_dt = np.where(dt > 0, dt, 0.1)
    acc_forward_gt = np.diff(speed_mps, prepend=speed_mps[0]) / valid_dt
    
    # Filter moving, accelerating samples
    accel_mask = (speed_mps > 2.0) & (acc_forward_gt > 0.5) & (acc_forward_gt < 4.0)
    print(f"\nNumber of significant positive acceleration samples (>0.5 m/s^2): {np.sum(accel_mask)}")
    
    # Let's inspect linear acceleration components in body frame during acceleration
    ax_lin = df.loc[accel_mask, "lin_ax"].to_numpy()
    ay_lin = df.loc[accel_mask, "lin_ay"].to_numpy()
    az_lin = df.loc[accel_mask, "lin_az"].to_numpy()
    
    mean_ax_accel = np.mean(ax_lin)
    mean_ay_accel = np.mean(ay_lin)
    mean_az_accel = np.mean(az_lin)
    print(f"Mean linear acceleration during forward acceleration:")
    print(f"  lin_ax: {mean_ax_accel:.4f} m/s^2")
    print(f"  lin_ay: {mean_ay_accel:.4f} m/s^2")
    print(f"  lin_az: {mean_az_accel:.4f} m/s^2")
    
    # Ratio / angle in xy body plane
    body_yaw_angle = np.arctan2(mean_ay_accel, mean_ax_accel)
    print(f"Horizontal acceleration principal angle: {np.rad2deg(body_yaw_angle):.2f}° relative to body X-axis")
    
    # Correlation with GT longitudinal acceleration
    all_moving = speed_mps > 1.0
    for col in ["lin_ax", "lin_ay", "lin_az"]:
        corr = np.corrcoef(acc_forward_gt[all_moving], df.loc[all_moving, col])[0, 1]
        print(f"  Correlation(gt_forward_acc, {col}): {corr:.4f}")

    # Inspect phone orientation relative to vehicle
    print("\nAndroid phone orientation (mean over all samples):")
    print(f"  phone_yaw_deg:   {df['phone_yaw_deg'].mean():.2f}°")
    print(f"  phone_pitch_deg: {df['phone_pitch_deg'].mean():.2f}°")
    print(f"  phone_roll_deg:  {df['phone_roll_deg'].mean():.2f}°")

if __name__ == "__main__":
    analyze_sequence_alignment("S-Vta1a")
    analyze_sequence_alignment("S-Vta2")
