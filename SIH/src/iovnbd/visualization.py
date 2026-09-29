"""
IO-VNBD Plotting and Signal Visualization Module
Generates publication-quality plots of trajectories, IMU raw/linear signals, and sensor diagnostics.
"""

from pathlib import Path
from typing import Optional, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def set_plot_style():
    """Configure clean, modern aesthetics for all generated figures."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8


def plot_ground_truth_trajectory(
    df: pd.DataFrame,
    title: str = "IO-VNBD Ground Truth Trajectory (Real Data)",
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot 2D ground truth trajectory in Local East-North-Up frame with velocity gradient.
    """
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

    east = df["east_m"].to_numpy()
    north = df["north_m"].to_numpy()
    speed = df["gps_speed_kmh"].to_numpy()

    # Scatter with speed colormap
    scatter = ax.scatter(
        east,
        north,
        c=speed,
        cmap="plasma",
        s=4,
        alpha=0.8,
        label="Vehicle GNSS Fixes",
    )
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Speed (km/h)", fontsize=11, fontweight="bold")

    # Start and End markers
    ax.scatter(
        east[0], north[0],
        c="#00cc44", edgecolors="black", s=120, zorder=5, label="Start (0, 0)"
    )
    ax.scatter(
        east[-1], north[-1],
        c="#ff2200", edgecolors="black", s=120, marker="X", zorder=5, label="End Point"
    )

    total_dist_km = df["cum_distance_m"].iloc[-1] / 1000.0
    duration_min = df["elapsed_s"].iloc[-1] / 60.0

    ax.set_title(
        f"{title}\nTotal Distance: {total_dist_km:.2f} km | Duration: {duration_min:.1f} mins | Samples: {len(df):,}",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Local East (meters)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Local North (meters)", fontsize=11, fontweight="bold")
    ax.axis("equal")
    ax.legend(loc="best", frameon=True, facecolor="white", framealpha=0.9)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"[Plot Saved] Trajectory plot saved to: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return fig


def plot_imu_signals(
    df: pd.DataFrame,
    title: str = "IO-VNBD Smartphone IMU Signals (Real Data)",
    time_window_s: Optional[tuple[float, float]] = None,
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot 3-axis Accelerometer (Total & Linear) and 3-axis Gyroscope signals vs time.
    """
    set_plot_style()
    plot_df = df.copy()
    if time_window_s is not None:
        t_min, t_max = time_window_s
        plot_df = plot_df[(plot_df["elapsed_s"] >= t_min) & (plot_df["elapsed_s"] <= t_max)]

    t = plot_df["elapsed_s"].to_numpy()

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True, dpi=150)

    # 1. Raw Accelerometer
    ax1 = axes[0]
    ax1.plot(t, plot_df["ax"], label="Acc X", color="#d62728", lw=0.9, alpha=0.85)
    ax1.plot(t, plot_df["ay"], label="Acc Y", color="#2ca02c", lw=0.9, alpha=0.85)
    ax1.plot(t, plot_df["az"], label="Acc Z (gravity axis)", color="#1f77b4", lw=0.9, alpha=0.85)
    ax1.set_ylabel("Total Acc (m/s²)", fontsize=11, fontweight="bold")
    ax1.set_title(f"{title} - Accelerometer & Gyroscope", fontsize=13, fontweight="bold", pad=10)
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. Linear Acceleration (Gravity Removed)
    ax2 = axes[1]
    ax2.plot(t, plot_df["lin_ax"], label="Linear Acc X", color="#d62728", lw=0.9, alpha=0.85)
    ax2.plot(t, plot_df["lin_ay"], label="Linear Acc Y", color="#2ca02c", lw=0.9, alpha=0.85)
    ax2.plot(t, plot_df["lin_az"], label="Linear Acc Z", color="#1f77b4", lw=0.9, alpha=0.85)
    ax2.axhline(0, color="black", linestyle=":", lw=0.8)
    ax2.set_ylabel("Linear Acc (m/s²)\n(Gravity Removed)", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.5)

    # 3. Gyroscope (Angular Velocities)
    ax3 = axes[2]
    ax3.plot(t, plot_df["gyro_yaw"], label="Gyro Yaw (Z)", color="#9467bd", lw=0.9, alpha=0.85)
    ax3.plot(t, plot_df["gyro_pitch"], label="Gyro Pitch (X)", color="#ff7f0e", lw=0.9, alpha=0.85)
    ax3.plot(t, plot_df["gyro_roll"], label="Gyro Roll (Y)", color="#8c564b", lw=0.9, alpha=0.85)
    ax3.set_ylabel("Angular Velocity (rad/s)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Elapsed Time (seconds)", fontsize=11, fontweight="bold")
    ax3.legend(loc="upper right", frameon=True)
    ax3.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"[Plot Saved] IMU signals plot saved to: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return fig


def plot_sensor_diagnostics(
    df: pd.DataFrame,
    title: str = "IO-VNBD Sensor Timing & Dynamic Statistics",
    save_path: Optional[Union[str, Path]] = None,
    show_plot: bool = False,
) -> plt.Figure:
    """
    Plot sampling interval distribution, speed profile, and acceleration histograms.
    """
    set_plot_style()
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), dpi=150)

    # (a) Sampling Interval dt (ms)
    ax_dt = axes[0, 0]
    dt_ms = df["dt_s"] * 1000.0
    ax_dt.hist(dt_ms.clip(80, 120), bins=40, color="#1f77b4", edgecolor="black", alpha=0.8)
    ax_dt.axvline(100.0, color="red", linestyle="--", lw=1.5, label="Nominal 100 ms (10 Hz)")
    ax_dt.set_title(f"Sampling Interval (dt) Distribution\nMean: {dt_ms.mean():.2f} ms | Std: {dt_ms.std():.2f} ms", fontweight="bold")
    ax_dt.set_xlabel("dt (milliseconds)", fontweight="bold")
    ax_dt.set_ylabel("Sample Count", fontweight="bold")
    ax_dt.legend(loc="upper right")

    # (b) Vehicle Speed Profile
    ax_spd = axes[0, 1]
    t_min = df["elapsed_s"] / 60.0
    ax_spd.plot(t_min, df["gps_speed_kmh"], color="#ff7f0e", lw=1.0)
    ax_spd.set_title(f"Ground Truth Vehicle Speed\nMax: {df['gps_speed_kmh'].max():.1f} km/h | Mean: {df['gps_speed_kmh'].mean():.1f} km/h", fontweight="bold")
    ax_spd.set_xlabel("Elapsed Time (minutes)", fontweight="bold")
    ax_spd.set_ylabel("Speed (km/h)", fontweight="bold")

    # (c) Accelerometer Magnitude Distribution
    ax_acc = axes[1, 0]
    ax_acc.hist(df["acc_norm"], bins=50, color="#2ca02c", edgecolor="black", alpha=0.8, label="|a| Total")
    ax_acc.hist(df["lin_acc_norm"], bins=50, color="#d62728", edgecolor="black", alpha=0.6, label="|a_lin| (No Gravity)")
    ax_acc.axvline(9.81, color="black", linestyle="--", lw=1.2, label="1g (9.81 m/s²)")
    ax_acc.set_title("Specific Force Magnitude Distribution", fontweight="bold")
    ax_acc.set_xlabel("Acceleration Magnitude (m/s²)", fontweight="bold")
    ax_acc.set_ylabel("Sample Count", fontweight="bold")
    ax_acc.legend(loc="upper right")

    # (d) Gyroscope Yaw Rate vs Ground Truth Turning
    ax_turn = axes[1, 1]
    ax_turn.hist(df["gyro_yaw"], bins=60, color="#9467bd", edgecolor="black", alpha=0.8)
    ax_turn.set_title(f"Yaw Angular Velocity (rad/s)\nRange: [{df['gyro_yaw'].min():.3f}, {df['gyro_yaw'].max():.3f}]", fontweight="bold")
    ax_turn.set_xlabel("Yaw Rate (rad/s)", fontweight="bold")
    ax_turn.set_ylabel("Sample Count", fontweight="bold")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"[Plot Saved] Sensor diagnostics plot saved to: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return fig
