import pandas as pd
import numpy as np
import sys

sys.stdout.reconfigure(encoding="utf-8")

def inspect_file(filepath):
    print("=" * 60)
    print(f"Inspecting: {filepath}")
    df = pd.read_csv(filepath, encoding_errors="replace")
    print(f"Total Rows: {len(df)}, Total Columns: {df.shape[1]}")
    
    # Clean column names (strip whitespace and non-ascii)
    cleaned_cols = [c.strip().encode("ascii", "ignore").decode("ascii") for c in df.columns]
    print("\nColumns:")
    for i, (orig, clean) in enumerate(zip(df.columns, cleaned_cols)):
        print(f"  [{i:2d}] {clean:<35} (Orig: {repr(orig[:30])})")
        
    # Check timestamps (column index 7: TIME SINCE START (ms))
    t_ms = pd.to_numeric(df.iloc[:, 7], errors="coerce")
    dt_ms = t_ms.diff()
    print("\nTime Since Start (ms) Stats:")
    print(f"  Min t_ms: {t_ms.min()}, Max t_ms: {t_ms.max()}, Duration: {(t_ms.max()-t_ms.min())/1000/60:.2f} mins")
    print("Sampling interval (dt) in ms:")
    print(f"  Mean: {dt_ms.mean():.2f} ms (~{1000/dt_ms.mean():.1f} Hz)")
    print(f"  Median: {dt_ms.median():.2f} ms (~{1000/dt_ms.median():.1f} Hz)")
    print(f"  Min dt: {dt_ms.min():.2f} ms, Max dt: {dt_ms.max():.2f} ms, Std: {dt_ms.std():.2f} ms")
    
    # Check GPS columns (lat: 0, lon: 1, speed: 3)
    lat = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    lon = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    spd_kmh = pd.to_numeric(df.iloc[:, 3], errors="coerce")
    print("\nGPS Stats:")
    print(f"  Lat range: [{lat.min():.6f}, {lat.max():.6f}]")
    print(f"  Lon range: [{lon.min():.6f}, {lon.max():.6f}]")
    print(f"  Speed (km/h) range: [{spd_kmh.min():.2f}, {spd_kmh.max():.2f}], Mean: {spd_kmh.mean():.2f} km/h")
    
    # Check IMU columns (ax: 9, ay: 10, az: 11, gx: 15, gy: 16, gz: 17)
    ax = pd.to_numeric(df.iloc[:, 9], errors="coerce")
    ay = pd.to_numeric(df.iloc[:, 10], errors="coerce")
    az = pd.to_numeric(df.iloc[:, 11], errors="coerce")
    print("\nAccelerometer (m/s^2) Stats:")
    print(f"  ax: mean={ax.mean():.3f}, std={ax.std():.3f}, range=[{ax.min():.3f}, {ax.max():.3f}]")
    print(f"  ay: mean={ay.mean():.3f}, std={ay.std():.3f}, range=[{ay.min():.3f}, {ay.max():.3f}]")
    print(f"  az: mean={az.mean():.3f}, std={az.std():.3f}, range=[{az.min():.3f}, {az.max():.3f}]")
    norm_a = np.sqrt(ax**2 + ay**2 + az**2)
    print(f"  |a| magnitude mean: {norm_a.mean():.3f} m/s^2 (~1g = 9.81 m/s^2)")

    gy = pd.to_numeric(df.iloc[:, 15], errors="coerce")
    gp = pd.to_numeric(df.iloc[:, 16], errors="coerce")
    gr = pd.to_numeric(df.iloc[:, 17], errors="coerce")
    print("\nGyroscope (rad/s) Stats:")
    print(f"  yaw: mean={gy.mean():.4f}, std={gy.std():.4f}, range=[{gy.min():.4f}, {gy.max():.4f}]")
    print(f"  pitch: mean={gp.mean():.4f}, std={gp.std():.4f}, range=[{gp.min():.4f}, {gp.max():.4f}]")
    print(f"  roll: mean={gr.mean():.4f}, std={gr.std():.4f}, range=[{gr.min():.4f}, {gr.max():.4f}]")

if __name__ == "__main__":
    inspect_file("data/raw/S-Vta1a.csv")
    inspect_file("data/raw/S-Vta2.csv")
