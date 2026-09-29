"""
Test Phone-to-Vehicle Alignment with different yaw modes and evaluate INS propagation
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def align_vectors_rodrigues(v_from, v_to):
    a = v_from / np.linalg.norm(v_from)
    b = v_to / np.linalg.norm(v_to)
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    if s < 1e-12:
        return np.eye(3) if c > 0 else -np.eye(3)
    vx = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0]
    ])
    return np.eye(3) + vx + (vx @ vx) * (1.0 / (1.0 + c))

def compute_alignment_matrix(df, n_samples=30, yaw_mode="leveling_only"):
    # 1. Leveling from initial gravity
    fx = df.loc[:n_samples, "ax"].mean()
    fy = df.loc[:n_samples, "ay"].mean()
    fz = df.loc[:n_samples, "az"].mean()
    
    f_mean = np.array([fx, fy, fz])
    z_target = np.array([0.0, 0.0, 1.0])
    R_level = align_vectors_rodrigues(f_mean, z_target)
    
    # 2. Yaw alignment
    psi = 0.0
    if yaw_mode == "motion_acceleration":
        # Check acceleration during initial acceleration
        # Transform linear accelerations by R_level
        lin_a = df[["lin_ax", "lin_ay", "lin_az"]].to_numpy()
        a_level = (R_level @ lin_a.T).T # shape (N, 3)
        # Find samples where speed > 2 and dv/dt > 0.5
        v = df["gps_speed_kmh"].to_numpy() # verified m/s
        dt = df["dt_s"].to_numpy()
        valid_dt = np.where(dt > 0, dt, 0.1)
        dv = np.diff(v, prepend=v[0]) / valid_dt
        acc_mask = (v > 2.0) & (dv > 0.5) & (dv < 4.0)
        if np.sum(acc_mask) > 10:
            a_fwd = np.mean(a_level[acc_mask, 0])
            a_lat = np.mean(a_level[acc_mask, 1])
            psi = np.arctan2(a_lat, a_fwd)
    elif yaw_mode == "initial_course":
        moving = df[df["gps_speed_kmh"] > 2.0]
        if len(moving) > 0 and "gt_heading_deg" in moving:
            gt_h0 = moving["gt_heading_deg"].iloc[0]
            # Android sensor orientation yaw
            phone_yaw0 = df.loc[:n_samples, "phone_yaw_deg"].mean()
            psi = np.deg2rad(phone_yaw0 - gt_h0)
            
    # Rotation around Z by psi:
    # We want to rotate by -psi so that forward aligns with X_v
    c = np.cos(psi)
    s = np.sin(psi)
    R_yaw = np.array([
        [c, s, 0.0],
        [-s, c, 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    R_b_v = R_yaw @ R_level
    return R_b_v, R_level, psi

for seq in ["S-Vta1a", "S-Vta2"]:
    df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / f"{seq}_preprocessed.csv")
    print(f"\n==========================================")
    print(f"Sequence: {seq}")
    print(f"==========================================")
    for mode in ["leveling_only", "motion_acceleration", "initial_course"]:
        R, R_lvl, psi = compute_alignment_matrix(df, yaw_mode=mode)
        det = np.linalg.det(R)
        ortho = np.allclose(R @ R.T, np.eye(3), atol=1e-7)
        print(f"Mode: {mode:22s} | psi={np.rad2deg(psi):6.2f}° | Det={det:.6f} | Ortho={ortho}")
