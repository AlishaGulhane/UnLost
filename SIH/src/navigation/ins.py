"""
IDR-NAV Navigation Module: Classical Strapdown Inertial Navigation System (INS)
Implements Phase 2: Pure Classical Inertial Dead Reckoning baseline without GNSS aiding.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class INSConfig:
    """Configuration parameters for Pure Classical Strapdown INS Dead Reckoning."""
    use_android_linear_acc: bool = True
    gravity_magnitude: float = 9.80665
    integration_method: str = "trapezoidal"  # "trapezoidal" or "euler"
    initial_alignment_samples: int = 30
    yaw_initialization_mode: str = "sensor_yaw"  # "sensor_yaw", "mag_heading", "gt_heading", "zero"


@dataclass
class INSState:
    """State vector of the Inertial Navigation System at a given time step."""
    timestamp_ms: float
    elapsed_s: float
    position_enu: np.ndarray    # [East, North, Up] in meters
    velocity_enu: np.ndarray    # [v_East, v_North, v_Up] in m/s
    quaternion: np.ndarray      # [qw, qx, qy, qz] unit quaternion (body -> navigation)
    euler_rpy_deg: np.ndarray   # [roll, pitch, yaw] in degrees
    acc_nav: np.ndarray         # [a_East, a_North, a_Up] in m/s^2


def quaternion_multiply(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Compute quaternion product p (x) q with convention [qw, qx, qy, qz]."""
    pw, px, py, pz = p
    qw, qx, qy, qz = q
    return np.array([
        pw * qw - px * qx - py * qy - pz * qz,
        pw * qx + px * qw + py * qz - pz * qy,
        pw * qy - px * qz + py * qw + pz * qx,
        pw * qz + px * qy - py * qx + pz * qw,
    ], dtype=np.float64)


def quaternion_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Convert unit quaternion [qw, qx, qy, qz] to 3x3 Direction Cosine Matrix R_b_n."""
    qw, qx, qy, qz = q
    return np.array([
        [1.0 - 2.0 * (qy**2 + qz**2), 2.0 * (qx * qy - qw * qz), 2.0 * (qx * qz + qw * qy)],
        [2.0 * (qx * qy + qw * qz), 1.0 - 2.0 * (qx**2 + qz**2), 2.0 * (qy * qz - qw * qx)],
        [2.0 * (qx * qz - qw * qy), 2.0 * (qy * qz + qw * qx), 1.0 - 2.0 * (qx**2 + qy**2)],
    ], dtype=np.float64)


def euler_to_quaternion(roll_rad: float, pitch_rad: float, yaw_rad: float) -> np.ndarray:
    """Convert Euler angles (roll, pitch, yaw) in radians to unit quaternion [qw, qx, qy, qz]."""
    cr = np.cos(roll_rad / 2.0)
    sr = np.sin(roll_rad / 2.0)
    cp = np.cos(pitch_rad / 2.0)
    sp = np.sin(pitch_rad / 2.0)
    cy = np.cos(yaw_rad / 2.0)
    sy = np.sin(yaw_rad / 2.0)

    q = np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ], dtype=np.float64)
    norm = np.linalg.norm(q)
    return q / norm if norm > 1e-12 else np.array([1.0, 0.0, 0.0, 0.0])


def quaternion_to_euler(q: np.ndarray) -> Tuple[float, float, float]:
    """
    Convert unit quaternion [qw, qx, qy, qz] to Euler angles (roll, pitch, yaw) in radians.
    Convention: Tait-Bryan Z-Y-X (yaw, pitch, roll).
    """
    qw, qx, qy, qz = q
    # roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))

    # yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return float(roll), float(pitch), float(yaw)


class InitialAttitudeAlignment:
    """
    Initial attitude alignment for strapdown INS.
    Estimates initial roll and pitch from accelerometer gravity vector during initial samples,
    and initializes yaw using available magnetometer/fused phone orientation or reference heading.
    """

    @staticmethod
    def align(
        df: pd.DataFrame,
        num_samples: int = 30,
        mode: str = "sensor_yaw",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute initial quaternion q0 and Euler angles (roll0, pitch0, yaw0) in radians.
        """
        n = min(num_samples, len(df))
        init_slice = df.iloc[:n]

        fx = float(init_slice["ax"].mean())
        fy = float(init_slice["ay"].mean())
        fz = float(init_slice["az"].mean())

        # Roll and Pitch from specific force (gravity vector in body frame)
        # f^b = [fx, fy, fz]^T. Since f^b ~= -g^b = [0, 0, g]^T when horizontal:
        pitch0 = np.arctan2(-fx, np.sqrt(fy**2 + fz**2))
        roll0 = np.arctan2(fy, fz)

        # Yaw initialization
        if mode == "sensor_yaw" and "phone_yaw_deg" in df:
            # Android sensor orientation yaw: azimuth degrees clockwise from magnetic North.
            # In Local ENU Cartesian coordinates: 0 rad is East (+X), pi/2 rad is North (+Y).
            # Math yaw = deg2rad(90 - azimuth)
            azimuth_deg = float(init_slice["phone_yaw_deg"].mean())
            yaw0 = np.deg2rad(90.0 - azimuth_deg)
        elif mode == "mag_heading" and "mag_x" in df and "mag_y" in df:
            # Tilt-compensated magnetic heading
            mx = float(init_slice["mag_x"].mean())
            my = float(init_slice["mag_y"].mean())
            mz = float(init_slice["mag_z"].mean())
            # Project magnetometer onto horizontal plane using roll0, pitch0
            # m_h_x = mx * cos(theta) + my * sin(phi)*sin(theta) + mz * cos(phi)*sin(theta)
            # m_h_y = my * cos(phi) - mz * sin(phi)
            m_hx = mx * np.cos(pitch0) + my * np.sin(roll0) * np.sin(pitch0) + mz * np.cos(roll0) * np.sin(pitch0)
            m_hy = my * np.cos(roll0) - mz * np.sin(roll0)
            mag_azimuth = np.arctan2(-m_hy, m_hx)  # Angle from magnetic North
            yaw0 = (np.pi / 2.0) - mag_azimuth
        elif mode == "gt_heading" and "gt_heading_deg" in df:
            moving = df[df["gps_speed_kmh"] > 1.0]
            if len(moving) > 0:
                gt_h0 = float(moving["gt_heading_deg"].iloc[0])
            else:
                gt_h0 = 0.0
            yaw0 = np.deg2rad(90.0 - gt_h0)
        else:
            yaw0 = 0.0

        q0 = euler_to_quaternion(roll0, pitch0, yaw0)
        rpy0 = np.array([roll0, pitch0, yaw0], dtype=np.float64)
        return q0, rpy0


class InertialDeadReckoning:
    """
    Pure Classical Strapdown Inertial Navigation System (INS).
    Integrates 3-axis accelerometer and 3-axis gyroscope data forward in time
    to maintain position, velocity, and orientation estimates in the Local ENU frame.
    Strictly causal with no future samples, no GNSS resets, and no ground-truth leakage.
    """

    def __init__(self, config: Optional[INSConfig] = None):
        self.config = config or INSConfig()
        self.g_nav = np.array([0.0, 0.0, -self.config.gravity_magnitude], dtype=np.float64)
        self.reset()

    def reset(self):
        """Reset INS internal states to zero."""
        self.p = np.zeros(3, dtype=np.float64)
        self.v = np.zeros(3, dtype=np.float64)
        self.q = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        self.rpy = np.zeros(3, dtype=np.float64)
        self.acc_nav_prev = np.zeros(3, dtype=np.float64)
        self.initialized = False

    def initialize(
        self,
        p0: np.ndarray,
        v0: np.ndarray,
        q0: np.ndarray,
    ):
        """Set initial conditions for position, velocity, and attitude."""
        self.p = np.array(p0, dtype=np.float64).copy()
        self.v = np.array(v0, dtype=np.float64).copy()
        norm_q = np.linalg.norm(q0)
        self.q = (np.array(q0, dtype=np.float64) / norm_q).copy()
        r, p, y = quaternion_to_euler(self.q)
        self.rpy = np.array([r, p, y], dtype=np.float64)
        self.acc_nav_prev = np.zeros(3, dtype=np.float64)
        self.initialized = True

    def propagate_step(
        self,
        dt: float,
        acc_b: np.ndarray,
        gyro_b: np.ndarray,
        grav_b: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Propagate INS state forward by time step dt:
        1. Gyroscope integration -> attitude update (quaternion & Euler).
        2. Acceleration coordinate transformation (body -> ENU) & gravity handling.
        3. Velocity integration (navigation frame).
        4. Position integration (navigation frame).

        Returns:
            (p, v, q, rpy, acc_nav)
        """
        if not self.initialized:
            raise RuntimeError("INS must be initialized before propagation.")

        # Guard against zero or negative dt
        dt_eff = float(dt) if dt > 1e-5 else 0.100

        # 1. Orientation propagation using gyroscope angular rates
        # gyro_b = [omega_x, omega_y, omega_z]^T (rad/s)
        theta_vec = gyro_b * dt_eff
        theta = float(np.linalg.norm(theta_vec))

        if theta > 1e-12:
            half_theta = theta / 2.0
            sin_scale = np.sin(half_theta) / theta
            dq = np.array([
                np.cos(half_theta),
                sin_scale * theta_vec[0],
                sin_scale * theta_vec[1],
                sin_scale * theta_vec[2],
            ], dtype=np.float64)
        else:
            dq = np.array([1.0, 0.5 * theta_vec[0], 0.5 * theta_vec[1], 0.5 * theta_vec[2]], dtype=np.float64)

        # Quaternion update: q_k+1 = q_k (x) dq
        q_next = quaternion_multiply(self.q, dq)
        norm_q = float(np.linalg.norm(q_next))
        self.q = q_next / norm_q if norm_q > 1e-12 else np.array([1.0, 0.0, 0.0, 0.0])

        # Euler angles from updated quaternion
        roll, pitch, yaw = quaternion_to_euler(self.q)
        self.rpy = np.array([roll, pitch, yaw], dtype=np.float64)

        # 2. Direction Cosine Matrix from body to navigation frame
        R_b_n = quaternion_to_rotation_matrix(self.q)

        # 3. Transform acceleration to navigation frame and compensate gravity
        if self.config.use_android_linear_acc:
            # If linear acceleration is provided (already gravity compensated in body frame)
            acc_nav = R_b_n @ acc_b
        else:
            # Classical strapdown: rotate specific force and subtract navigation gravity
            # a^n = R_b_n * f^b + g^n, where g^n = [0, 0, -g]
            acc_nav = R_b_n @ acc_b + self.g_nav

        # 4. Numerical integration for velocity and position
        if self.config.integration_method == "trapezoidal":
            # Trapezoidal integration
            v_next = self.v + 0.5 * (self.acc_nav_prev + acc_nav) * dt_eff
            p_next = self.p + 0.5 * (self.v + v_next) * dt_eff
        else:
            # Standard Euler integration
            v_next = self.v + acc_nav * dt_eff
            p_next = self.p + self.v * dt_eff + 0.5 * acc_nav * (dt_eff**2)

        self.acc_nav_prev = acc_nav.copy()
        self.v = v_next
        self.p = p_next

        return self.p.copy(), self.v.copy(), self.q.copy(), self.rpy.copy(), acc_nav.copy()

    def propagate_sequence(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute pure INS dead reckoning over an entire preprocessed dataset sequence.
        Produces complete output DataFrame containing:
        - Timestamps
        - INS East, North, Up position and velocity
        - INS Roll, Pitch, Yaw and Quaternion
        - Preserved Ground Truth references
        - Quantitative error metrics for each timestamp
        """
        n_samples = len(df)
        if n_samples == 0:
            raise ValueError("Input DataFrame is empty.")

        # 1. Initial Alignment
        q0, rpy0 = InitialAttitudeAlignment.align(
            df,
            num_samples=self.config.initial_alignment_samples,
            mode=self.config.yaw_initialization_mode,
        )

        p0 = np.array([
            float(df["east_m"].iloc[0]),
            float(df["north_m"].iloc[0]),
            float(df["up_m"].iloc[0]),
        ], dtype=np.float64)
        v0 = np.zeros(3, dtype=np.float64)

        self.initialize(p0, v0, q0)

        # 2. Extract sensor arrays
        dt_arr = df["dt_s"].to_numpy()
        time_ms_arr = df["time_ms"].to_numpy()
        elapsed_s_arr = df["elapsed_s"].to_numpy()

        if self.config.use_android_linear_acc:
            acc_b_arr = df[["lin_ax", "lin_ay", "lin_az"]].to_numpy()
        else:
            acc_b_arr = df[["ax", "ay", "az"]].to_numpy()

        # Phone gyro: pitch=omega_x, roll=omega_y, yaw=omega_z
        gyro_b_arr = np.column_stack([
            df["gyro_pitch"].to_numpy(),
            df["gyro_roll"].to_numpy(),
            df["gyro_yaw"].to_numpy(),
        ])

        # Preallocate output buffers
        pos_out = np.zeros((n_samples, 3), dtype=np.float64)
        vel_out = np.zeros((n_samples, 3), dtype=np.float64)
        quat_out = np.zeros((n_samples, 4), dtype=np.float64)
        rpy_out = np.zeros((n_samples, 3), dtype=np.float64)
        acc_nav_out = np.zeros((n_samples, 3), dtype=np.float64)

        # Initial state at k = 0
        pos_out[0] = self.p
        vel_out[0] = self.v
        quat_out[0] = self.q
        rpy_out[0] = self.rpy

        # Initial acceleration transformation
        R0 = quaternion_to_rotation_matrix(self.q)
        if self.config.use_android_linear_acc:
            a0_nav = R0 @ acc_b_arr[0]
        else:
            a0_nav = R0 @ acc_b_arr[0] + self.g_nav
        acc_nav_out[0] = a0_nav
        self.acc_nav_prev = a0_nav.copy()

        # 3. Propagate row by row
        for k in range(n_samples - 1):
            dt_k = dt_arr[k + 1]
            p_k, v_k, q_k, rpy_k, a_k = self.propagate_step(
                dt=dt_k,
                acc_b=acc_b_arr[k + 1],
                gyro_b=gyro_b_arr[k + 1],
            )
            pos_out[k + 1] = p_k
            vel_out[k + 1] = v_k
            quat_out[k + 1] = q_k
            rpy_out[k + 1] = rpy_k
            acc_nav_out[k + 1] = a_k

        # 4. Construct output DataFrame
        out_df = pd.DataFrame({
            "time_ms": time_ms_arr,
            "elapsed_s": elapsed_s_arr,
            "dt_s": dt_arr,
            # Position (ENU, meters)
            "ins_east_m": pos_out[:, 0],
            "ins_north_m": pos_out[:, 1],
            "ins_up_m": pos_out[:, 2],
            # Velocity (ENU, m/s)
            "ins_ve_mps": vel_out[:, 0],
            "ins_vn_mps": vel_out[:, 1],
            "ins_vu_mps": vel_out[:, 2],
            "ins_speed_mps": np.sqrt(vel_out[:, 0]**2 + vel_out[:, 1]**2 + vel_out[:, 2]**2),
            # Orientation (Euler degrees & Quaternions)
            "ins_roll_deg": np.rad2deg(rpy_out[:, 0]),
            "ins_pitch_deg": np.rad2deg(rpy_out[:, 1]),
            "ins_yaw_deg": np.rad2deg(rpy_out[:, 2]),
            "ins_qw": quat_out[:, 0],
            "ins_qx": quat_out[:, 1],
            "ins_qy": quat_out[:, 2],
            "ins_qz": quat_out[:, 3],
            # Navigation frame acceleration
            "ins_acc_east": acc_nav_out[:, 0],
            "ins_acc_north": acc_nav_out[:, 1],
            "ins_acc_up": acc_nav_out[:, 2],
        })

        # Preserve ground truth fields where available
        if "east_m" in df and "north_m" in df:
            out_df["gt_east_m"] = df["east_m"].to_numpy()
            out_df["gt_north_m"] = df["north_m"].to_numpy()
            out_df["gt_up_m"] = df["up_m"].to_numpy() if "up_m" in df else 0.0

            # Compute error metrics
            err_east = out_df["ins_east_m"] - out_df["gt_east_m"]
            err_north = out_df["ins_north_m"] - out_df["gt_north_m"]
            err_up = out_df["ins_up_m"] - out_df["gt_up_m"]

            out_df["pos_error_2d_m"] = np.sqrt(err_east**2 + err_north**2)
            out_df["pos_error_3d_m"] = np.sqrt(err_east**2 + err_north**2 + err_up**2)

        if "cum_distance_m" in df:
            out_df["cum_distance_m"] = df["cum_distance_m"].to_numpy()
            cum_dist = df["cum_distance_m"].to_numpy()
            out_df["drift_pct_distance"] = np.where(
                cum_dist > 10.0,
                (out_df["pos_error_2d_m"] / cum_dist) * 100.0,
                0.0,
            )

        if "gps_speed_kmh" in df:
            # Verified: raw gps_speed_kmh column stores m/s!
            out_df["gt_speed_mps"] = df["gps_speed_kmh"].to_numpy()
            out_df["gt_speed_kmh"] = out_df["gt_speed_mps"] * 3.6
            out_df["vel_error_mps"] = np.abs(out_df["ins_speed_mps"] - out_df["gt_speed_mps"])

        if "gt_heading_deg" in df:
            out_df["gt_heading_deg"] = df["gt_heading_deg"].to_numpy()
            # Convert math yaw to bearing (0=North, 90=East): bearing = (90 - yaw) % 360
            ins_bearing = (90.0 - out_df["ins_yaw_deg"]) % 360.0
            out_df["ins_bearing_deg"] = ins_bearing
            diff_bearing = np.abs(ins_bearing - out_df["gt_heading_deg"])
            out_df["heading_error_deg"] = np.minimum(diff_bearing, 360.0 - diff_bearing)

        return out_df


def compute_ins_metrics(df_ins: pd.DataFrame, total_distance_m: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate quantitative INS dead reckoning performance metrics from output DataFrame.
    """
    if "pos_error_2d_m" not in df_ins.columns:
        raise ValueError("DataFrame does not contain pos_error_2d_m column.")

    err_2d = df_ins["pos_error_2d_m"].to_numpy()
    err_3d = df_ins["pos_error_3d_m"].to_numpy() if "pos_error_3d_m" in df_ins else err_2d

    final_dist = total_distance_m if total_distance_m is not None else float(df_ins["cum_distance_m"].iloc[-1])

    metrics = {
        "final_pos_error_2d_m": float(err_2d[-1]),
        "final_pos_error_3d_m": float(err_3d[-1]),
        "pos_rmse_2d_m": float(np.sqrt(np.mean(err_2d**2))),
        "pos_rmse_3d_m": float(np.sqrt(np.mean(err_3d**2))),
        "mean_pos_error_2d_m": float(np.mean(err_2d)),
        "max_pos_error_2d_m": float(np.max(err_2d)),
        "drift_pct_of_distance": float((err_2d[-1] / final_dist) * 100.0) if final_dist > 0 else 0.0,
        "final_ins_east_m": float(df_ins["ins_east_m"].iloc[-1]),
        "final_ins_north_m": float(df_ins["ins_north_m"].iloc[-1]),
        "final_ins_up_m": float(df_ins["ins_up_m"].iloc[-1]),
        "final_gt_east_m": float(df_ins["gt_east_m"].iloc[-1]) if "gt_east_m" in df_ins else 0.0,
        "final_gt_north_m": float(df_ins["gt_north_m"].iloc[-1]) if "gt_north_m" in df_ins else 0.0,
        "final_ins_speed_mps": float(df_ins["ins_speed_mps"].iloc[-1]),
    }

    if "vel_error_mps" in df_ins.columns:
        metrics["mean_vel_error_mps"] = float(df_ins["vel_error_mps"].mean())
        metrics["max_vel_error_mps"] = float(df_ins["vel_error_mps"].max())

    if "heading_error_deg" in df_ins.columns:
        valid_h = df_ins["heading_error_deg"].dropna()
        metrics["mean_heading_error_deg"] = float(valid_h.mean())
        metrics["final_heading_error_deg"] = float(valid_h.iloc[-1])

    return metrics
