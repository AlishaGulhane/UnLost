import pandas as pd
import numpy as np

def check_acc_directions(seq):
    df = pd.read_csv(f"data/processed/{seq}_preprocessed.csv")
    
    # Speed is in gps_speed_kmh (which we verified is actually in m/s!)
    v = df["gps_speed_kmh"].to_numpy()
    dt = df["dt_s"].to_numpy()
    valid_dt = np.where(dt > 0, dt, 0.1)
    dv_dt = np.diff(v, prepend=v[0]) / valid_dt
    
    # Filter moving acceleration
    moving = (v > 2.0) & (np.abs(dv_dt) < 5.0)
    
    print(f"=== {seq} Acceleration Axis Correlation with dv/dt ===")
    for col in ["ax", "ay", "az", "lin_ax", "lin_ay", "lin_az"]:
        corr = np.corrcoef(dv_dt[moving], df.loc[moving, col])[0, 1]
        print(f"  Corr(dv/dt, {col}): {corr:.4f}")

if __name__ == "__main__":
    check_acc_directions("S-Vta1a")
    check_acc_directions("S-Vta2")
