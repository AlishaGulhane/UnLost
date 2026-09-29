import pandas as pd
import numpy as np

def inspect(seq):
    df = pd.read_csv(f"data/processed/{seq}_preprocessed.csv")
    print(f"=== {seq} ===")
    print("Gravity mean vector (m/s^2):")
    print(f"  grav_x: {df['grav_x'].mean():.3f} (std: {df['grav_x'].std():.3f})")
    print(f"  grav_y: {df['grav_y'].mean():.3f} (std: {df['grav_y'].std():.3f})")
    print(f"  grav_z: {df['grav_z'].mean():.3f} (std: {df['grav_z'].std():.3f})")

    print("\nAccelerometer mean vector (m/s^2):")
    print(f"  ax: {df['ax'].mean():.3f} (std: {df['ax'].std():.3f})")
    print(f"  ay: {df['ay'].mean():.3f} (std: {df['ay'].std():.3f})")
    print(f"  az: {df['az'].mean():.3f} (std: {df['az'].std():.3f})")

    print("\nGyroscope mean vector (rad/s):")
    print(f"  gyro_yaw (Z):   {df['gyro_yaw'].mean():.5f} (range: [{df['gyro_yaw'].min():.3f}, {df['gyro_yaw'].max():.3f}])")
    print(f"  gyro_pitch (X): {df['gyro_pitch'].mean():.5f} (range: [{df['gyro_pitch'].min():.3f}, {df['gyro_pitch'].max():.3f}])")
    print(f"  gyro_roll (Y):  {df['gyro_roll'].mean():.5f} (range: [{df['gyro_roll'].min():.3f}, {df['gyro_roll'].max():.3f}])")

    print("\nAndroid Orientation Euler angles (deg):")
    print(f"  phone_yaw_deg:   mean={df['phone_yaw_deg'].mean():.2f}, range=[{df['phone_yaw_deg'].min():.2f}, {df['phone_yaw_deg'].max():.2f}]")
    print(f"  phone_pitch_deg: mean={df['phone_pitch_deg'].mean():.2f}, range=[{df['phone_pitch_deg'].min():.2f}, {df['phone_pitch_deg'].max():.2f}]")
    print(f"  phone_roll_deg:  mean={df['phone_roll_deg'].mean():.2f}, range=[{df['phone_roll_deg'].min():.2f}, {df['phone_roll_deg'].max():.2f}]")

    print("\nGround Truth Heading (deg):")
    print(f"  gt_heading_deg:  mean={df['gt_heading_deg'].mean():.2f}, range=[{df['gt_heading_deg'].min():.2f}, {df['gt_heading_deg'].max():.2f}]")

    # Initial 50 samples (stationary or start of sequence)
    print("\nInitial 50 samples averages:")
    print("  ax, ay, az:", df.loc[:50, ['ax', 'ay', 'az']].mean().to_dict())
    print("  grav_x, grav_y, grav_z:", df.loc[:50, ['grav_x', 'grav_y', 'grav_z']].mean().to_dict())
    print("  phone yaw, pitch, roll:", df.loc[:50, ['phone_yaw_deg', 'phone_pitch_deg', 'phone_roll_deg']].mean().to_dict())
    print("  gt heading:", df.loc[:50, 'gt_heading_deg'].dropna().mean())
    print("\n")

if __name__ == "__main__":
    inspect("S-Vta1a")
    inspect("S-Vta2")
