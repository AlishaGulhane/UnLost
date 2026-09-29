import pandas as pd
import numpy as np

def test_initial_alignment(seq):
    df = pd.read_csv(f"data/processed/{seq}_preprocessed.csv")
    
    # Average first N samples (e.g. 20 samples = 2 seconds)
    N = 20
    fx = df.loc[:N, 'ax'].mean()
    fy = df.loc[:N, 'ay'].mean()
    fz = df.loc[:N, 'az'].mean()
    
    # Pitch and Roll from gravity
    pitch0 = np.arctan2(-fx, np.sqrt(fy**2 + fz**2))
    roll0 = np.arctan2(fy, fz)
    
    print(f"=== Initial Alignment for {seq} (first {N} samples) ===")
    print(f"Mean specific force: fx={fx:.4f}, fy={fy:.4f}, fz={fz:.4f} m/s^2")
    print(f"Estimated Roll0:  {np.rad2deg(roll0):.2f}° ({roll0:.4f} rad)")
    print(f"Estimated Pitch0: {np.rad2deg(pitch0):.2f}° ({pitch0:.4f} rad)")
    
    # Magnetometer:
    mx = df.loc[:N, 'mag_x'].mean()
    my = df.loc[:N, 'mag_y'].mean()
    mz = df.loc[:N, 'mag_z'].mean()
    print(f"Magnetometer: mx={mx:.2f}, my={my:.2f}, mz={mz:.2f} uT")
    
    # Android phone yaw
    phone_yaw0 = df.loc[:N, 'phone_yaw_deg'].mean()
    print(f"Android sensor orientation Yaw0: {phone_yaw0:.2f}°")
    
    # Ground truth initial heading (when vehicle begins moving)
    # Find first sample where speed > 2 m/s
    moving_idx = df[df['gps_speed_kmh'] > 2.0].index
    if len(moving_idx) > 0:
        first_moving = moving_idx[0]
        gt_h0 = df.loc[first_moving:first_moving+10, 'gt_heading_deg'].mean()
        print(f"GT initial moving heading (sample {first_moving}): {gt_h0:.2f}°")
    
    # Check GPS bearing column if present
    if 'gps_bearing_deg' in df:
        gps_b0 = df.loc[:N, 'gps_bearing_deg'].mean()
        print(f"GPS bearing column initial: {gps_b0:.2f}°")

if __name__ == "__main__":
    test_initial_alignment("S-Vta1a")
    test_initial_alignment("S-Vta2")
