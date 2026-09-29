import pandas as pd
import numpy as np

def check_gyro_correlations(seq):
    df = pd.read_csv(f"data/processed/{seq}_preprocessed.csv")
    
    # Calculate ground truth yaw rate (rad/s)
    # gt_heading is in radians or degrees? In preprocessor: gt_heading_deg and gt_heading_rad
    # Need to handle angle unwrap
    gt_head = np.unwrap(np.deg2rad(df["gt_heading_deg"].fillna(0).to_numpy()))
    dt = df["dt_s"].to_numpy()
    valid_dt = np.where(dt > 0, dt, 0.1)
    gt_yaw_rate = np.diff(gt_head, prepend=gt_head[0]) / valid_dt
    
    # Filter only when vehicle is moving (speed > 1 m/s)
    moving = df["gps_speed_kmh"] > 1.0
    
    print(f"=== {seq} Gyro Correlation with GT Yaw Rate ===")
    for col in ["gyro_yaw", "gyro_pitch", "gyro_roll"]:
        corr = np.corrcoef(gt_yaw_rate[moving], df.loc[moving, col])[0, 1]
        print(f"  Corr(gt_yaw_rate, {col}): {corr:.4f}")

    # Also check phone orientation yaw vs gt heading
    phone_yaw_rad = np.unwrap(np.deg2rad(df["phone_yaw_deg"].to_numpy()))
    corr_head = np.corrcoef(gt_head[moving], phone_yaw_rad[moving])[0, 1]
    print(f"  Corr(gt_heading, phone_yaw_deg): {corr_head:.4f}")
    
    # Check phone orientation initial values
    print(f"  Initial GT heading (deg): {df['gt_heading_deg'].dropna().iloc[0]:.2f}")
    print(f"  Initial Phone yaw (deg): {df['phone_yaw_deg'].iloc[0]:.2f}")
    print(f"  Initial Phone pitch (deg): {df['phone_pitch_deg'].iloc[0]:.2f}")
    print(f"  Initial Phone roll (deg): {df['phone_roll_deg'].iloc[0]:.2f}")

if __name__ == "__main__":
    check_gyro_correlations("S-Vta1a")
    check_gyro_correlations("S-Vta2")
