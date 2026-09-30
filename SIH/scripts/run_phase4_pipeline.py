
import pandas as pd
import numpy as np
import os
import sys

from ai_models import SpeedEstimator, MotionDetector
from ekf import EKF, GNSSStateMachine
from map_matching import MapMatcher

def run_pipeline():
    print("==================================================")
    print("PHASE 4: INTELLIGENT DEAD RECKONING PIPELINE")
    print("==================================================")
    
    data_path = r"C:\Users\alish\Documents\SIH Dead reckoning\SIH\data\processed\S-Vta1a_preprocessed.csv"
    ins_path = r"C:\Users\alish\Documents\SIH Dead reckoning\SIH\data\processed\S-Vta1a_ins.csv"
    pbf_path = r"C:\Users\alish\Documents\SIH Dead reckoning\SIH\western-zone-260928.osm.pbf"
    
    df = pd.read_csv(data_path)
    df_ins = pd.read_csv(ins_path)
    
    # 1. Train AI Speed Model on Valid GNSS segments
    speed_est = SpeedEstimator(window_size=50)
    acc_seq = df[["ax", "ay", "az"]].to_numpy()
    gyro_seq = df[["gyro_pitch", "gyro_roll", "gyro_yaw"]].to_numpy()
    
    # Ground truth speed for training
    if "gps_speed_kmh" in df:
        gt_speed_mps = df["gps_speed_kmh"].to_numpy() / 3.6
        speed_est.train(acc_seq, gyro_seq, gt_speed_mps)
        
    ai_speed_preds, ai_speed_conf = speed_est.predict_batch(acc_seq, gyro_seq)
    df["ai_speed_mps"] = ai_speed_preds
    df["ai_speed_conf"] = ai_speed_conf
    
    # 2. Motion Detection
    md = MotionDetector()
    acc_nav_seq = df_ins[["ins_acc_east", "ins_acc_north", "ins_acc_up"]].to_numpy()
    motion_states = md.detect_batch(acc_nav_seq, gyro_seq)
    df["motion_state"] = motion_states
    
    # 3. EKF and GNSS State Machine
    dt_arr = df["dt_s"].to_numpy()
    gnss_valid = (~df["gps_speed_kmh"].isna()).to_numpy()
    
    gnss_sm = GNSSStateMachine()
    
    pos_e = np.zeros(len(df))
    pos_n = np.zeros(len(df))
    states = []
    
    # Init EKF
    ekf = None
    
    for i in range(len(df)):
        dt = dt_arr[i]
        is_gnss = gnss_valid[i]
        state = gnss_sm.update(is_gnss, dt)
        states.append(state)
        
        if ekf is None:
            if is_gnss:
                ekf = EKF(dt)
                ekf.x[0] = df_ins["gt_east_m"].iloc[i]
                ekf.x[1] = df_ins["gt_north_m"].iloc[i]
                pos_e[i] = ekf.x[0]
                pos_n[i] = ekf.x[1]
            continue
            
        ekf.dt = dt
        ekf.predict(acc_nav_seq[i, 0], acc_nav_seq[i, 1])
        
        # Velocity update
        h = df_ins["ins_yaw_deg"].iloc[i] * np.pi / 180.0
        v_e = ai_speed_preds[i] * np.sin(h)
        v_n = ai_speed_preds[i] * np.cos(h)
        ekf.update_velocity(v_e, v_n, ai_speed_conf[i])
        
        # NHC
        if motion_states[i] == "normal":
            ekf.apply_nhc(h, 0.8)
            
        # GNSS Update
        if state == "GNSS_AVAILABLE":
            ekf.update_gnss(df_ins["gt_east_m"].iloc[i], df_ins["gt_north_m"].iloc[i], v_e, v_n)
            
        pos_e[i] = ekf.x[0]
        pos_n[i] = ekf.x[1]
        
    df["ekf_east_m"] = pos_e
    df["ekf_north_m"] = pos_n
    df["gnss_state"] = states
    
    # Map Matching
    mm = MapMatcher(pbf_path)
    
    # Evaluation
    err_2d = np.sqrt((df["ekf_east_m"] - df_ins["gt_east_m"])**2 + (df["ekf_north_m"] - df_ins["gt_north_m"])**2)
    final_err = err_2d.iloc[-1]
    dist = df_ins["cum_distance_m"].iloc[-1]
    drift = (final_err / dist) * 100.0 if dist > 0 else 0.0
    
    print("\\n==================================================")
    print("BENCHMARK RESULTS (Full System: INS + AI + EKF + NHC)")
    print("==================================================")
    print(f"Final Position Error: {final_err:.2f} m")
    print(f"Overall Drift: {drift:.2f} % (Target: < 10%)")
    print(f"Mean RMSE: {np.nanmean(err_2d):.2f} m")
    
    # Ablation summary
    print("\\nABLATION STUDY:")
    print("A. INS Only Drift: 870.62 % (From Phase 2 Baseline)")
    print(f"F. Full System Drift: {drift:.2f} %")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()
