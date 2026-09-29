"""
Prototype INS Dead Reckoning integration test
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_prototype_ins(seq_name: str, use_android_lin_acc: bool = True, yaw_init_mode: str = "sensor_yaw"):
    df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / f"{seq_name}_preprocessed.csv")
    
    N = len(df)
    print(f"\n=======================================================")
    print(f"RUNNING PROTOTYPE INS: {seq_name} ({N} samples)")
    print(f"Config: use_android_lin_acc={use_android_lin_acc}, yaw_init_mode={yaw_init_mode}")
    print(f"=======================================================")
    
    # 1. Initial alignment from initial N0 samples
    N0 = min(30, N)
    fx0 = df.loc[:N0, "ax"].mean()
    fy0 = df.loc[:N0, "ay"].mean()
    fz0 = df.loc[:N0, "az"].mean()
    
    pitch0 = np.arctan2(-fx0, np.sqrt(fy0**2 + fz0**2))
    roll0 = np.arctan2(fy0, fz0)
    
    if yaw_init_mode == "sensor_yaw":
        # Convert Android phone yaw (0=North, 90=East, clockwise) to ENU math yaw (0=East, 90=North, counter-clockwise)
        # In Android: azimuth is degrees clockwise from magnetic North.
        # In ENU math: 0 is East (+X), 90 is North (+Y), counter-clockwise.
        # So: enu_yaw = 90 - azimuth (or equivalent)
        azimuth_deg = df.loc[:N0, "phone_yaw_deg"].mean()
        yaw0 = np.deg2rad(90.0 - azimuth_deg)
    elif yaw_init_mode == "gt_heading":
        # Initial ground truth heading
        moving = df[df["gps_speed_kmh"] > 1.0]
        if len(moving) > 0:
            gt_h0 = moving["gt_heading_deg"].iloc[0]
        else:
            gt_h0 = 0.0
        yaw0 = np.deg2rad(90.0 - gt_h0)
    else:
        yaw0 = 0.0
        
    print(f"Initial Attitude: roll0={np.rad2deg(roll0):.2f}°, pitch0={np.rad2deg(pitch0):.2f}°, yaw0={np.rad2deg(yaw0):.2f}°")
    
    # Initialize quaternion from roll0, pitch0, yaw0
    cr = np.cos(roll0 / 2.0); sr = np.sin(roll0 / 2.0)
    cp = np.cos(pitch0 / 2.0); sp = np.sin(pitch0 / 2.0)
    cy = np.cos(yaw0 / 2.0); sy = np.sin(yaw0 / 2.0)
    q = np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ])
    q = q / np.linalg.norm(q)
    
    # Preallocate output arrays
    p = np.zeros((N, 3)) # East, North, Up
    v = np.zeros((N, 3)) # East, North, Up
    rpy = np.zeros((N, 3)) # Roll, Pitch, Yaw
    quats = np.zeros((N, 4))
    a_nav = np.zeros((N, 3))
    
    # Initial state
    p[0] = [df["east_m"].iloc[0], df["north_m"].iloc[0], df["up_m"].iloc[0]] # [0, 0, 0]
    v[0] = [0.0, 0.0, 0.0]
    quats[0] = q
    rpy[0] = [roll0, pitch0, yaw0]
    
    dt = df["dt_s"].to_numpy()
    
    # Sensor streams
    if use_android_lin_acc:
        acc_b = df[["lin_ax", "lin_ay", "lin_az"]].to_numpy()
    else:
        acc_b = df[["ax", "ay", "az"]].to_numpy()
        
    # Gyro streams (pitch=wx, roll=wy, yaw=wz)
    gyro_b = np.column_stack([
        df["gyro_pitch"].to_numpy(),
        df["gyro_roll"].to_numpy(),
        df["gyro_yaw"].to_numpy(),
    ])
    
    g_nav = np.array([0.0, 0.0, -9.80665])
    
    for k in range(N - 1):
        del_t = dt[k+1] if dt[k+1] > 0 else 0.100
        
        # 1. Orientation update using gyroscope
        wb = gyro_b[k]
        theta_vec = wb * del_t
        theta = np.linalg.norm(theta_vec)
        
        if theta > 1e-12:
            dq = np.array([
                np.cos(theta / 2.0),
                (np.sin(theta / 2.0) / theta) * theta_vec[0],
                (np.sin(theta / 2.0) / theta) * theta_vec[1],
                (np.sin(theta / 2.0) / theta) * theta_vec[2],
            ])
        else:
            dq = np.array([1.0, 0.5 * theta_vec[0], 0.5 * theta_vec[1], 0.5 * theta_vec[2]])
            
        # Quaternion multiply: q_new = q * dq
        pw, px, py, pz = q
        qw, qx, qy, qz = dq
        q_new = np.array([
            pw*qw - px*qx - py*qy - pz*qz,
            pw*qx + px*qw + py*qz - pz*qy,
            pw*qy - px*qz + py*qw + pz*qx,
            pw*qz + px*qy - py*qx + pz*qw,
        ])
        q = q_new / np.linalg.norm(q_new)
        quats[k+1] = q
        
        # Euler angles
        qw, qx, qy, qz = q
        sinr_cosp = 2.0 * (qw * qx + qy * qz)
        cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        sinp = 2.0 * (qw * qy - qz * qx)
        pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))
        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        rpy[k+1] = [roll, pitch, yaw]
        
        # 2. Rotation matrix body to navigation
        R_b_n = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)],
        ])
        
        # 3. Transform acceleration to ENU
        if use_android_lin_acc:
            acc_nav = R_b_n @ acc_b[k]
        else:
            acc_nav = R_b_n @ acc_b[k] + g_nav
            
        a_nav[k] = acc_nav
        
        # 4. Velocity integration (Euler/trapezoidal)
        v[k+1] = v[k] + acc_nav * del_t
        
        # 5. Position integration
        p[k+1] = p[k] + 0.5 * (v[k] + v[k+1]) * del_t

    # Final sample acceleration
    a_nav[-1] = a_nav[-2]
    
    # Errors vs Ground Truth
    gt_e = df["east_m"].to_numpy()
    gt_n = df["north_m"].to_numpy()
    gt_u = df["up_m"].to_numpy()
    
    err_2d = np.sqrt((p[:, 0] - gt_e)**2 + (p[:, 1] - gt_n)**2)
    err_3d = np.sqrt((p[:, 0] - gt_e)**2 + (p[:, 1] - gt_n)**2 + (p[:, 2] - gt_u)**2)
    
    cum_dist_verified = df["cum_distance_m"].iloc[-1]
    
    print("\n--- MEASURED RESULTS ---")
    print(f"Final 2D Position Error:   {err_2d[-1]:.2f} m ({err_2d[-1]/1000.0:.2f} km)")
    print(f"Final 3D Position Error:   {err_3d[-1]:.2f} m ({err_3d[-1]/1000.0:.2f} km)")
    print(f"Mean 2D Position Error:    {np.mean(err_2d):.2f} m")
    print(f"Position 2D RMSE:          {np.sqrt(np.mean(err_2d**2)):.2f} m")
    print(f"Max 2D Position Error:     {np.max(err_2d):.2f} m")
    print(f"Drift % of Verified Dist:  {(err_2d[-1] / cum_dist_verified) * 100:.2f}%")
    print(f"Final Estimated Velocity:  East={v[-1, 0]:.2f}, North={v[-1, 1]:.2f}, Up={v[-1, 2]:.2f} m/s")
    print(f"Final Estimated Position:  East={p[-1, 0]:.2f}, North={p[-1, 1]:.2f}, Up={p[-1, 2]:.2f} m")
    print(f"Ground Truth Final Pos:    East={gt_e[-1]:.2f}, North={gt_n[-1]:.2f}, Up={gt_u[-1]:.2f} m")

if __name__ == "__main__":
    run_prototype_ins("S-Vta1a", use_android_lin_acc=True, yaw_init_mode="sensor_yaw")
    run_prototype_ins("S-Vta1a", use_android_lin_acc=False, yaw_init_mode="sensor_yaw")
    run_prototype_ins("S-Vta2", use_android_lin_acc=True, yaw_init_mode="sensor_yaw")
    run_prototype_ins("S-Vta2", use_android_lin_acc=False, yaw_init_mode="sensor_yaw")
