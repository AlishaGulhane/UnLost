"""
Phase 2 Visualization Module: Pure Classical INS Baseline vs Ground Truth
Generates publication-quality diagnostic plots for trajectory, error growth,
velocity divergence, and orientation profiles.
"""

from pathlib import Path
from typing import Optional, Tuple, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def set_plot_style():
    """Configure clean, modern aesthetics for all generated figures."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8


def plot_trajectory_comparison(
    df_ins: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot 2D Ground Truth vs Pure Classical INS trajectory in ENU coordinates.
    Includes dual views (full unbounded INS drift and ground-truth reference zoom).
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), dpi=150)

    gt_e_km = df_ins["gt_east_m"] / 1000.0
    gt_n_km = df_ins["gt_north_m"] / 1000.0
    ins_e_km = df_ins["ins_east_m"] / 1000.0
    ins_n_km = df_ins["ins_north_m"] / 1000.0

    # Panel 1: Full scale showing massive INS drift
    ax1.plot(gt_e_km, gt_n_km, color="#1f77b4", linewidth=2.5, label="Ground Truth (GNSS/VBOX)", zorder=3)
    ax1.plot(ins_e_km, ins_n_km, color="#d62728", linewidth=2.0, linestyle="--", label="Pure Classical INS Baseline", zorder=4)

    # Origin and endpoints
    ax1.scatter(gt_e_km.iloc[0], gt_n_km.iloc[0], color="#2ca02c", s=120, edgecolors="black", label="Origin (0,0)", zorder=5)
    ax1.scatter(gt_e_km.iloc[-1], gt_n_km.iloc[-1], color="#1f77b4", marker="X", s=120, edgecolors="black", label="GT End", zorder=5)
    ax1.scatter(ins_e_km.iloc[-1], ins_n_km.iloc[-1], color="#d62728", marker="X", s=120, edgecolors="black", label="INS End", zorder=5)

    final_err_km = df_ins["pos_error_2d_m"].iloc[-1] / 1000.0
    ax1.set_title(f"A. Pure INS vs Ground Truth (Full Scale)\nSequence: {sequence_name} | Final Drift: {final_err_km:.1f} km", fontsize=12, fontweight="bold")
    ax1.set_xlabel("East (km)", fontsize=11)
    ax1.set_ylabel("North (km)", fontsize=11)
    ax1.legend(loc="best", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Panel 2: Ground Truth reference focus
    ax2.plot(gt_e_km, gt_n_km, color="#1f77b4", linewidth=2.5, label="Ground Truth Trajectory")
    ax2.plot(ins_e_km, ins_n_km, color="#d62728", linewidth=1.5, linestyle="--", alpha=0.7, label="Pure INS (drifting)")
    ax2.scatter(gt_e_km.iloc[0], gt_n_km.iloc[0], color="#2ca02c", s=120, edgecolors="black", label="Origin (0,0)", zorder=5)
    ax2.scatter(gt_e_km.iloc[-1], gt_n_km.iloc[-1], color="#1f77b4", marker="X", s=120, edgecolors="black", label="GT End", zorder=5)

    pad_e = (gt_e_km.max() - gt_e_km.min()) * 0.2 + 1.0
    pad_n = (gt_n_km.max() - gt_n_km.min()) * 0.2 + 1.0
    ax2.set_xlim(gt_e_km.min() - pad_e, gt_e_km.max() + pad_e)
    ax2.set_ylim(gt_n_km.min() - pad_n, gt_n_km.max() + pad_n)
    ax2.set_title(f"B. Ground Truth Reference Scale (Zoomed)\nSequence: {sequence_name}", fontsize=12, fontweight="bold")
    ax2.set_xlabel("East (km)", fontsize=11)
    ax2.set_ylabel("North (km)", fontsize=11)
    ax2.legend(loc="best", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_position_error_vs_time(
    df_ins: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot 2D and 3D position error growth over elapsed time.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    t_min = df_ins["elapsed_s"] / 60.0
    err_2d_km = df_ins["pos_error_2d_m"] / 1000.0
    err_3d_km = df_ins["pos_error_3d_m"] / 1000.0

    ax.plot(t_min, err_2d_km, color="#d62728", linewidth=2.5, label="2D Horizontal Error (East-North)")
    ax.plot(t_min, err_3d_km, color="#9467bd", linewidth=2.0, linestyle=":", label="3D Position Error (East-North-Up)")

    final_2d = err_2d_km.iloc[-1]
    rmse_2d = np.sqrt(np.mean(df_ins["pos_error_2d_m"]**2)) / 1000.0

    ax.set_title(f"Pure INS Position Error vs Time — {sequence_name}\nFinal 2D Error: {final_2d:.2f} km | 2D RMSE: {rmse_2d:.2f} km", fontsize=12, fontweight="bold")
    ax.set_xlabel("Elapsed Time (minutes)", fontsize=11)
    ax.set_ylabel("Position Error (km)", fontsize=11)
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_position_error_vs_distance(
    df_ins: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot 2D position error vs travelled distance (using verified cumulative distance).
    """
    set_plot_style()
    fig, ax1 = plt.subplots(figsize=(10, 6), dpi=150)

    dist_km = df_ins["cum_distance_m"] / 1000.0
    err_2d_km = df_ins["pos_error_2d_m"] / 1000.0
    drift_pct = df_ins["drift_pct_distance"]

    ax1.plot(dist_km, err_2d_km, color="#d62728", linewidth=2.5, label="2D Position Drift (km)")
    ax1.set_xlabel("Travelled Distance (km) [Independently Verified]", fontsize=11)
    ax1.set_ylabel("Position Error (km)", color="#d62728", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#d62728")
    ax1.grid(True, linestyle="--", alpha=0.6)

    ax2 = ax1.twinx()
    ax2.plot(dist_km, drift_pct, color="#ff7f0e", linewidth=1.8, linestyle="--", label="Drift (% of Distance)")
    ax2.set_ylabel("Drift Error (% of Travelled Distance)", color="#ff7f0e", fontsize=11)
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    ax2.grid(False)

    final_pct = drift_pct.iloc[-1]
    ax1.set_title(f"Pure INS Drift vs Travelled Distance — {sequence_name}\nFinal Drift: {err_2d_km.iloc[-1]:.2f} km ({final_pct:.1f}% of {dist_km.iloc[-1]:.2f} km travelled)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


# Alias for convenience
plot_drift_vs_distance = plot_position_error_vs_distance


def plot_velocity_comparison(
    df_ins: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Compare INS-estimated velocity vs Ground Truth velocity over time.
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), dpi=150, sharex=True)

    t_min = df_ins["elapsed_s"] / 60.0

    # Panel 1: Speed comparison
    ax1.plot(t_min, df_ins["gt_speed_mps"], color="#1f77b4", linewidth=1.5, label="Ground Truth Speed (m/s)")
    ax1.plot(t_min, df_ins["ins_speed_mps"], color="#d62728", linewidth=2.0, linestyle="--", label="INS Estimated Speed (m/s)")
    ax1.set_ylabel("Speed (m/s)", fontsize=11)
    ax1.set_title(f"Velocity Profile & Divergence — {sequence_name}", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Panel 2: Velocity components
    ax2.plot(t_min, df_ins["ins_ve_mps"], color="#2ca02c", linewidth=1.5, label="INS East Velocity (v_E)")
    ax2.plot(t_min, df_ins["ins_vn_mps"], color="#1f77b4", linewidth=1.5, label="INS North Velocity (v_N)")
    ax2.plot(t_min, df_ins["ins_vu_mps"], color="#9467bd", linewidth=1.5, linestyle=":", label="INS Up Velocity (v_U)")
    ax2.set_xlabel("Elapsed Time (minutes)", fontsize=11)
    ax2.set_ylabel("Velocity Components (m/s)", fontsize=11)
    ax2.legend(loc="upper left", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_orientation_profiles(
    df_ins: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot Roll, Pitch, and Yaw profiles over time.
    """
    set_plot_style()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), dpi=150, sharex=True)

    t_min = df_ins["elapsed_s"] / 60.0

    # Roll
    ax1.plot(t_min, df_ins["ins_roll_deg"], color="#1f77b4", linewidth=1.5, label="INS Roll (°)")
    ax1.set_ylabel("Roll (°)", fontsize=11)
    ax1.set_title(f"Strapdown Gyroscope Orientation Propagation — {sequence_name}", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Pitch
    ax2.plot(t_min, df_ins["ins_pitch_deg"], color="#ff7f0e", linewidth=1.5, label="INS Pitch (°)")
    ax2.set_ylabel("Pitch (°)", fontsize=11)
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    # Yaw
    ax3.plot(t_min, df_ins["ins_yaw_deg"], color="#2ca02c", linewidth=1.5, label="INS Yaw (° [math 0=East, 90=North])")
    if "gt_heading_deg" in df_ins and "ins_bearing_deg" in df_ins:
        ax3.plot(t_min, df_ins["ins_bearing_deg"], color="#d62728", linewidth=1.5, linestyle="--", label="INS Bearing (° from North)")
        ax3.plot(t_min, df_ins["gt_heading_deg"], color="#7f7f7f", linewidth=1.0, alpha=0.7, label="GT Course Heading (°)")
    ax3.set_xlabel("Elapsed Time (minutes)", fontsize=11)
    ax3.set_ylabel("Yaw / Heading (°)", fontsize=11)
    ax3.legend(loc="upper right", frameon=True)
    ax3.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_alignment_signals(
    df_aligned: pd.DataFrame,
    sequence_name: str,
    time_window_s: Tuple[float, float] = (100.0, 220.0),
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Compare raw smartphone body-frame IMU vs aligned vehicle-frame IMU signals over a sample window.
    """
    set_plot_style()
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), dpi=150)

    # Window slice
    t0, t1 = time_window_s
    t = df_aligned["elapsed_s"]
    mask = (t >= t0) & (t <= t1)
    df_w = df_aligned[mask]
    tw = df_w["elapsed_s"]

    # Panel 1: Raw Phone Accelerometer
    ax = axes[0, 0]
    ax.plot(tw, df_w["ax"], label="ax (Phone Width)", color="#1f77b4", alpha=0.8)
    ax.plot(tw, df_w["ay"], label="ay (Phone Length)", color="#2ca02c", alpha=0.8)
    ax.plot(tw, df_w["az"], label="az (Phone Normal)", color="#d62728", alpha=0.8)
    ax.set_ylabel("Specific Force (m/s²)", fontsize=10)
    ax.set_title("1. Raw Smartphone Accelerometer (Body Frame)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    # Panel 2: Aligned Vehicle Accelerometer
    ax = axes[0, 1]
    ax.plot(tw, df_w["veh_ax"], label="veh_ax (Forward longitudinal)", color="#ff7f0e", linewidth=1.5)
    ax.plot(tw, df_w["veh_ay"], label="veh_ay (Lateral)", color="#9467bd", alpha=0.8)
    ax.plot(tw, df_w["veh_az"], label="veh_az (Vertical Up)", color="#8c564b", alpha=0.8)
    ax.set_ylabel("Specific Force (m/s²)", fontsize=10)
    ax.set_title("2. Aligned Vehicle Accelerometer (Vehicle Frame R_b^v)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    # Panel 3: Raw Phone Gyroscope
    ax = axes[1, 0]
    ax.plot(tw, df_w["gyro_pitch"], label="gyro_pitch (X-rate)", color="#1f77b4", alpha=0.8)
    ax.plot(tw, df_w["gyro_roll"], label="gyro_roll (Y-rate)", color="#2ca02c", alpha=0.8)
    ax.plot(tw, df_w["gyro_yaw"], label="gyro_yaw (Z-rate)", color="#d62728", alpha=0.8)
    ax.set_xlabel("Elapsed Time (s)", fontsize=10)
    ax.set_ylabel("Angular Rate (rad/s)", fontsize=10)
    ax.set_title("3. Raw Smartphone Gyroscope (Body Frame)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    # Panel 4: Aligned Vehicle Gyroscope
    ax = axes[1, 1]
    ax.plot(tw, df_w["veh_gyro_x"], label="veh_gyro_x (Roll rate)", color="#ff7f0e", alpha=0.8)
    ax.plot(tw, df_w["veh_gyro_y"], label="veh_gyro_y (Pitch rate)", color="#9467bd", alpha=0.8)
    ax.plot(tw, df_w["veh_gyro_z"], label="veh_gyro_z (Yaw turn rate)", color="#d62728", linewidth=1.5)
    ax.set_xlabel("Elapsed Time (s)", fontsize=10)
    ax.set_ylabel("Angular Rate (rad/s)", fontsize=10)
    ax.set_title("4. Aligned Vehicle Gyroscope (Vehicle Frame R_b^v)", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    fig.suptitle(f"Phone-to-Vehicle Sensor Alignment (R_b^v) Signal Verification — {sequence_name}", fontsize=13, fontweight="bold", y=0.99)
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_phase2_vs_phase3_trajectory(
    df_p2: pd.DataFrame,
    df_p3: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Compare Ground Truth vs Phase 2 (Phone-frame INS) vs Phase 3 (Aligned Vehicle-frame INS).
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), dpi=150)

    gt_e_km = df_p2["gt_east_m"] / 1000.0
    gt_n_km = df_p2["gt_north_m"] / 1000.0
    p2_e_km = df_p2["ins_east_m"] / 1000.0
    p2_n_km = df_p2["ins_north_m"] / 1000.0
    p3_e_km = df_p3["ins_east_m"] / 1000.0
    p3_n_km = df_p3["ins_north_m"] / 1000.0

    # Panel 1: Full Scale Comparison
    ax1.plot(gt_e_km, gt_n_km, color="#1f77b4", linewidth=2.5, label="Ground Truth", zorder=3)
    ax1.plot(p2_e_km, p2_n_km, color="#7f7f7f", linewidth=1.5, linestyle=":", label="Phase 2 (Phone-frame INS)", zorder=4)
    ax1.plot(p3_e_km, p3_n_km, color="#d62728", linewidth=2.0, linestyle="--", label="Phase 3 (Aligned Vehicle INS)", zorder=5)

    ax1.scatter(gt_e_km.iloc[0], gt_n_km.iloc[0], color="#2ca02c", s=120, edgecolors="black", label="Origin (0,0)", zorder=6)
    ax1.scatter(gt_e_km.iloc[-1], gt_n_km.iloc[-1], color="#1f77b4", marker="X", s=120, edgecolors="black", label="GT End", zorder=6)
    ax1.scatter(p2_e_km.iloc[-1], p2_n_km.iloc[-1], color="#7f7f7f", marker="X", s=120, edgecolors="black", label="P2 End", zorder=6)
    ax1.scatter(p3_e_km.iloc[-1], p3_n_km.iloc[-1], color="#d62728", marker="X", s=120, edgecolors="black", label="P3 End", zorder=6)

    ax1.set_title(f"A. Full Trajectory Comparison (Global Drift Scale)\n{sequence_name}", fontsize=12, fontweight="bold")
    ax1.set_xlabel("East (km)", fontsize=11)
    ax1.set_ylabel("North (km)", fontsize=11)
    ax1.legend(loc="best", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Panel 2: Ground Truth reference focus
    ax2.plot(gt_e_km, gt_n_km, color="#1f77b4", linewidth=2.5, label="Ground Truth Trajectory")
    ax2.plot(p2_e_km, p2_n_km, color="#7f7f7f", linewidth=1.2, linestyle=":", alpha=0.7, label="Phase 2 INS")
    ax2.plot(p3_e_km, p3_n_km, color="#d62728", linewidth=1.5, linestyle="--", alpha=0.8, label="Phase 3 Aligned INS")
    ax2.scatter(gt_e_km.iloc[0], gt_n_km.iloc[0], color="#2ca02c", s=120, edgecolors="black", label="Origin (0,0)", zorder=6)
    ax2.scatter(gt_e_km.iloc[-1], gt_n_km.iloc[-1], color="#1f77b4", marker="X", s=120, edgecolors="black", label="GT End", zorder=6)

    pad_e = (gt_e_km.max() - gt_e_km.min()) * 0.2 + 1.0
    pad_n = (gt_n_km.max() - gt_n_km.min()) * 0.2 + 1.0
    ax2.set_xlim(gt_e_km.min() - pad_e, gt_e_km.max() + pad_e)
    ax2.set_ylim(gt_n_km.min() - pad_n, gt_n_km.max() + pad_n)
    ax2.set_title(f"B. Ground Truth Reference Scale (Zoomed)\n{sequence_name}", fontsize=12, fontweight="bold")
    ax2.set_xlabel("East (km)", fontsize=11)
    ax2.set_ylabel("North (km)", fontsize=11)
    ax2.legend(loc="best", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig


def plot_phase2_vs_phase3_error(
    df_p2: pd.DataFrame,
    df_p3: pd.DataFrame,
    sequence_name: str,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Compare position error development over time for Phase 2 vs Phase 3.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    t_min = df_p2["elapsed_s"] / 60.0
    err_p2_km = df_p2["pos_error_2d_m"] / 1000.0
    err_p3_km = df_p3["pos_error_2d_m"] / 1000.0

    ax.plot(t_min, err_p2_km, color="#7f7f7f", linewidth=2.0, linestyle=":", label=f"Phase 2 (Phone Frame) — Final: {err_p2_km.iloc[-1]:.1f} km")
    ax.plot(t_min, err_p3_km, color="#d62728", linewidth=2.5, label=f"Phase 3 (Aligned Vehicle Frame) — Final: {err_p3_km.iloc[-1]:.1f} km")

    ax.set_title(f"Position Error vs Time: Phase 2 vs Phase 3 — {sequence_name}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Elapsed Time (minutes)", fontsize=11)
    ax.set_ylabel("2D Position Error (km)", fontsize=11)
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
    if show_plot:
        plt.show()
    return fig
