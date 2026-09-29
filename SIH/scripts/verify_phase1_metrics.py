"""
Script to independently verify Phase 1 Distance and Speed Metrics
from raw and preprocessed IO-VNBD data.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.iovnbd import IOVNBDLoader, NavigationPreprocessor, geodetic_to_enu

def inspect_sequence(seq_name: str):
    raw_path = PROJECT_ROOT / "data" / "raw" / f"{seq_name}.csv"
    proc_path = PROJECT_ROOT / "data" / "processed" / f"{seq_name}_preprocessed.csv"
    
    print("=" * 80)
    print(f"VERIFYING METRICS FOR SEQUENCE: {seq_name}")
    print("=" * 80)
    
    # 1. Read raw CSV directly with latin1 / replace to inspect actual column names and first rows
    df_raw_direct = pd.read_csv(raw_path, encoding="latin1", low_memory=False)
    print(f"Raw CSV shape: {df_raw_direct.shape}")
    print("Raw column names:")
    for i, col in enumerate(df_raw_direct.columns):
        print(f"  Col {i:2d}: {repr(col)}")
        
    speed_col_name = [c for c in df_raw_direct.columns if "SPEED" in c.upper()][0]
    lat_col_name = [c for c in df_raw_direct.columns if "LAT" in c.upper()][0]
    lon_col_name = [c for c in df_raw_direct.columns if "LONG" in c.upper()][0]
    time_col_name = [c for c in df_raw_direct.columns if "TIME" in c.upper()][0]
    
    speed_raw = pd.to_numeric(df_raw_direct[speed_col_name], errors="coerce")
    time_raw = pd.to_numeric(df_raw_direct[time_col_name], errors="coerce")
    lat_raw = pd.to_numeric(df_raw_direct[lat_col_name], errors="coerce")
    lon_raw = pd.to_numeric(df_raw_direct[lon_col_name], errors="coerce")
    
    duration_s = (time_raw.dropna().iloc[-1] - time_raw.dropna().iloc[0]) / 1000.0
    print(f"\nRaw Duration: {duration_s:.2f} s ({duration_s/60.0:.2f} min)")
    print(f"Raw Speed column: {repr(speed_col_name)}")
    print(f"Raw Speed describe:\n{speed_raw.describe()}")
    
    # 2. Check using IOVNBDLoader and Preprocessor
    loader = IOVNBDLoader(data_dir=PROJECT_ROOT / "data" / "raw")
    df_loaded, meta = loader.load_smartphone_sequence(raw_path)
    
    print("\n--- LOADER & PREPROCESSOR INSPECTION ---")
    print(f"Loaded samples: {len(df_loaded)}")
    print(f"Reported metadata max speed: {meta.speed_kmh_max:.4f}")
    
    preprocessor = NavigationPreprocessor(target_hz=10.0)
    df_proc = preprocessor.preprocess_sequence(df_loaded)
    
    # 3. Analyze GPS Position Changes & Speed
    # Let's inspect step distances
    dt = df_proc["dt_s"].to_numpy()
    step_dist = df_proc["step_distance_m"].to_numpy()
    cum_dist = df_proc["cum_distance_m"].to_numpy()
    total_cum_dist_m = cum_dist[-1]
    
    # Velocity derived from GPS coordinates: v_coord = step_distance / dt
    v_from_coords_mps = np.where(dt > 0, step_dist / dt, 0.0)
    
    # Reported speed column in df_loaded:
    speed_col_vals = df_loaded["gps_speed_kmh"].to_numpy()
    
    print(f"\n--- DISTANCE AND SPEED VALUES ---")
    print(f"Total Cumulative Distance (from ENU diff sum): {total_cum_dist_m:.2f} m ({total_cum_dist_m/1000.0:.3f} km)")
    print(f"Net Displacement (Start to End): {np.sqrt(df_proc['east_m'].iloc[-1]**2 + df_proc['north_m'].iloc[-1]**2):.2f} m")
    
    print(f"\nSpeed Column in CSV ({speed_col_name}):")
    print(f"  Min:  {np.nanmin(speed_col_vals):.4f}")
    print(f"  Mean: {np.nanmean(speed_col_vals):.4f}")
    print(f"  Max:  {np.nanmax(speed_col_vals):.4f}")
    
    # Check if Speed Column is m/s or km/h!
    # If speed_col is in m/s:
    dist_if_mps = np.sum(np.nan_to_num(speed_col_vals * dt))
    print(f"Integral of speed * dt (assuming speed column is m/s): {dist_if_mps:.2f} m ({dist_if_mps/1000.0:.3f} km)")
    
    # If speed_col is in km/h:
    dist_if_kmh = np.sum(np.nan_to_num((speed_col_vals / 3.6) * dt))
    print(f"Integral of speed * dt (assuming speed column is km/h): {dist_if_kmh:.2f} m ({dist_if_kmh/1000.0:.3f} km)")
    
    print(f"\nSpeed derived from GPS Coordinates (step_distance / dt):")
    print(f"  Min:  {np.nanmin(v_from_coords_mps):.4f} m/s ({np.nanmin(v_from_coords_mps)*3.6:.4f} km/h)")
    print(f"  Mean: {np.nanmean(v_from_coords_mps):.4f} m/s ({np.nanmean(v_from_coords_mps)*3.6:.4f} km/h)")
    print(f"  Max:  {np.nanmax(v_from_coords_mps):.4f} m/s ({np.nanmax(v_from_coords_mps)*3.6:.4f} km/h)")
    
    # Let's inspect a few rows where speed is positive
    pos_speed = df_loaded[df_loaded["gps_speed_kmh"] > 0]
    print(f"\nNumber of samples with positive speed: {len(pos_speed)} / {len(df_loaded)}")
    print("Sample comparison of speed column vs coordinate diff speed (first 10 moving samples):")
    sample_idx = pos_speed.index[:10]
    for idx in sample_idx:
        sp = df_loaded.loc[idx, "gps_speed_kmh"]
        st = df_proc.loc[idx, "step_distance_m"]
        delt = df_proc.loc[idx, "dt_s"]
        v_coord = st / delt if delt > 0 else 0
        print(f"  Idx {idx:5d}: Speed col = {sp:6.2f} | Step dist = {st:6.2f} m | dt = {delt:.3f} s | Coord v = {v_coord:6.2f} m/s ({v_coord*3.6:6.2f} km/h) | Ratio col/coord = {sp/v_coord if v_coord > 0 else 0:.3f}")

    # Check GPS update frequency: how often does lat/lon actually change?
    lat_changes = np.sum(np.diff(df_proc["lat"].to_numpy()) != 0)
    print(f"\nUnique GPS lat updates count: {lat_changes} out of {len(df_proc)} samples")
    print(f"Ratio of updates: {lat_changes / len(df_proc):.4f} (indicating approx {lat_changes / duration_s:.2f} Hz GPS fix rate)")

if __name__ == "__main__":
    inspect_sequence("S-Vta1a")
    inspect_sequence("S-Vta2")
