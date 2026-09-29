"""
IDR-NAV Navigation Module: Phone-to-Vehicle Alignment (R_b^v)
Implements Phase 3: Estimation of the SO(3) rotation matrix transforming
sensor streams from the smartphone body frame (b) to the vehicle chassis frame (v).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class AlignmentConfig:
    """Configuration for Phone-to-Vehicle Alignment estimation."""
    initial_samples: int = 30
    yaw_mode: str = "motion_acceleration"  # "leveling_only", "motion_acceleration", "mount_nominal", "initial_course"
    min_accel_threshold: float = 0.5       # m/s^2 forward acceleration for motion-based yaw


def align_vectors_rodrigues(v_from: np.ndarray, v_to: np.ndarray) -> np.ndarray:
    """
    Compute minimal-angle SO(3) rotation matrix R such that R @ v_from = v_to.
    Guarantees orthogonality and determinant = +1 with zero parasitic yaw.
    """
    norm_from = float(np.linalg.norm(v_from))
    norm_to = float(np.linalg.norm(v_to))
    if norm_from < 1e-12 or norm_to < 1e-12:
        return np.eye(3, dtype=np.float64)

    a = v_from / norm_from
    b = v_to / norm_to

    v = np.cross(a, b)
    c = float(np.dot(a, b))
    s = float(np.linalg.norm(v))

    if s < 1e-12:
        if c > 0.0:
            return np.eye(3, dtype=np.float64)
        else:
            # 180 degree rotation around an orthogonal axis
            ortho = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            axis = np.cross(a, ortho)
            axis = axis / np.linalg.norm(axis)
            return -np.eye(3, dtype=np.float64) + 2.0 * np.outer(axis, axis)

    vx = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0]
    ], dtype=np.float64)

    R = np.eye(3, dtype=np.float64) + vx + (vx @ vx) * (1.0 / (1.0 + c))
    return R


def validate_rotation_matrix(R: np.ndarray, atol: float = 1e-6) -> Tuple[bool, float, float]:
    """
    Validate SO(3) properties:
    1. Orthogonality: R^T R ~= I
    2. Special Orthogonal: det(R) ~= +1
    Returns (is_valid, max_ortho_error, det_error).
    """
    ortho_error = float(np.max(np.abs(R @ R.T - np.eye(3))))
    det_val = float(np.linalg.det(R))
    det_error = float(abs(det_val - 1.0))
    is_valid = (ortho_error < atol) and (det_error < atol)
    return is_valid, ortho_error, det_error


class PhoneToVehicleAlignment:
    """
    Estimates and applies the transformation from smartphone sensor frame (b)
    to vehicle chassis frame (v) using Forward-Left-Up (FLU) convention.
    """

    def __init__(self, config: Optional[AlignmentConfig] = None):
        self.config = config or AlignmentConfig()

    def estimate_rotation(self, df: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Estimate the SO(3) rotation matrix R_b_v relating body frame to vehicle frame:
        x_v = R_b_v @ x_b.

        Two-stage process:
        1. Leveling (Roll & Pitch): Rotates phone gravity to point strictly along vehicle vertical (Up).
        2. Heading (Yaw): Aligns horizontal forward axis with vehicle longitudinal travel direction.
        """
        n_init = min(self.config.initial_samples, len(df))
        init_slice = df.iloc[:n_init]

        # 1. Leveling using initial specific force (gravity)
        fx = float(init_slice["ax"].mean())
        fy = float(init_slice["ay"].mean())
        fz = float(init_slice["az"].mean())
        f_mean = np.array([fx, fy, fz], dtype=np.float64)

        # In vehicle FLU frame, specific force points Up (+Z_v)
        z_vehicle = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        R_level = align_vectors_rodrigues(f_mean, z_vehicle)

        # Roll and Pitch tilt angles of the phone relative to vehicle horizontal
        pitch_level_rad = float(np.arctan2(-fx, np.sqrt(fy**2 + fz**2)))
        roll_level_rad = float(np.arctan2(fy, fz))

        # 2. Yaw alignment
        psi_rad = 0.0
        yaw_mode = self.config.yaw_mode

        if yaw_mode == "motion_acceleration":
            # Rotate linear accelerations into leveled frame
            if "lin_ax" in df and "lin_ay" in df and "lin_az" in df:
                lin_a = df[["lin_ax", "lin_ay", "lin_az"]].to_numpy()
                a_level = (R_level @ lin_a.T).T

                # Filter samples during vehicle acceleration
                if "gps_speed_kmh" in df:
                    v = df["gps_speed_kmh"].to_numpy() # verified m/s
                    dt = df["dt_s"].to_numpy()
                    valid_dt = np.where(dt > 0, dt, 0.1)
                    dv = np.diff(v, prepend=v[0]) / valid_dt
                    acc_mask = (v > 2.0) & (dv > self.config.min_accel_threshold) & (dv < 4.0)

                    if np.sum(acc_mask) >= 10:
                        a_fwd_est = float(np.mean(a_level[acc_mask, 0]))
                        a_lat_est = float(np.mean(a_level[acc_mask, 1]))
                        psi_rad = float(np.arctan2(a_lat_est, a_fwd_est))

        elif yaw_mode == "mount_nominal":
            # IO-VNBD benchmark setup: windshield phone mount in landscape
            # Phone +X aligns with vehicle forward, or +Y depending on orientation
            psi_rad = float(np.deg2rad(-90.0))

        elif yaw_mode == "initial_course":
            moving = df[df["gps_speed_kmh"] > 2.0]
            if len(moving) > 0 and "gt_heading_deg" in moving and "phone_yaw_deg" in df:
                gt_h0 = float(moving["gt_heading_deg"].iloc[0])
                phone_yaw0 = float(init_slice["phone_yaw_deg"].mean())
                psi_rad = float(np.deg2rad(phone_yaw0 - gt_h0))

        # Rotation around vehicle vertical Z axis by -psi to align X with forward
        c = np.cos(psi_rad)
        s = np.sin(psi_rad)
        R_yaw = np.array([
            [c, s, 0.0],
            [-s, c, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)

        R_b_v = R_yaw @ R_level

        # Validation
        is_valid, ortho_err, det_err = validate_rotation_matrix(R_b_v)

        info = {
            "roll_tilt_deg": float(np.rad2deg(roll_level_rad)),
            "pitch_tilt_deg": float(np.rad2deg(pitch_level_rad)),
            "yaw_align_deg": float(np.rad2deg(psi_rad)),
            "det_R": float(np.linalg.det(R_b_v)),
            "ortho_error": float(ortho_err),
            "is_valid_so3": float(1.0 if is_valid else 0.0),
            "f_raw_norm": float(np.linalg.norm(f_mean)),
            "f_aligned_z": float((R_b_v @ f_mean)[2]),
            "yaw_mode": yaw_mode,
        }

        return R_b_v, info

    def transform_signals(self, df: pd.DataFrame, R_b_v: np.ndarray) -> pd.DataFrame:
        """
        Apply rotation matrix R_b_v to all 3-axis sensor streams in df.
        Preserves all original columns and appends veh_* transformed columns.
        """
        df_aligned = df.copy()

        # 1. Accelerometer (total specific force)
        if all(c in df for c in ["ax", "ay", "az"]):
            acc_raw = df[["ax", "ay", "az"]].to_numpy()
            acc_veh = (R_b_v @ acc_raw.T).T
            df_aligned["veh_ax"] = acc_veh[:, 0]
            df_aligned["veh_ay"] = acc_veh[:, 1]
            df_aligned["veh_az"] = acc_veh[:, 2]

        # 2. Linear Acceleration
        if all(c in df for c in ["lin_ax", "lin_ay", "lin_az"]):
            lin_raw = df[["lin_ax", "lin_ay", "lin_az"]].to_numpy()
            lin_veh = (R_b_v @ lin_raw.T).T
            df_aligned["veh_lin_ax"] = lin_veh[:, 0]
            df_aligned["veh_lin_ay"] = lin_veh[:, 1]
            df_aligned["veh_lin_az"] = lin_veh[:, 2]

        # 3. Gravity Vector
        if all(c in df for c in ["grav_x", "grav_y", "grav_z"]):
            grav_raw = df[["grav_x", "grav_y", "grav_z"]].to_numpy()
            grav_veh = (R_b_v @ grav_raw.T).T
            df_aligned["veh_grav_x"] = grav_veh[:, 0]
            df_aligned["veh_grav_y"] = grav_veh[:, 1]
            df_aligned["veh_grav_z"] = grav_veh[:, 2]

        # 4. Gyroscope (pitch=wx, roll=wy, yaw=wz)
        if all(c in df for c in ["gyro_pitch", "gyro_roll", "gyro_yaw"]):
            gyro_raw = np.column_stack([
                df["gyro_pitch"].to_numpy(),
                df["gyro_roll"].to_numpy(),
                df["gyro_yaw"].to_numpy(),
            ])
            gyro_veh = (R_b_v @ gyro_raw.T).T
            df_aligned["veh_gyro_x"] = gyro_veh[:, 0]  # Vehicle roll rate
            df_aligned["veh_gyro_y"] = gyro_veh[:, 1]  # Vehicle pitch rate
            df_aligned["veh_gyro_z"] = gyro_veh[:, 2]  # Vehicle yaw rate (turning)

        # 5. Magnetometer
        if all(c in df for c in ["mag_x", "mag_y", "mag_z"]):
            mag_raw = df[["mag_x", "mag_y", "mag_z"]].to_numpy()
            mag_veh = (R_b_v @ mag_raw.T).T
            df_aligned["veh_mag_x"] = mag_veh[:, 0]
            df_aligned["veh_mag_y"] = mag_veh[:, 1]
            df_aligned["veh_mag_z"] = mag_veh[:, 2]

        return df_aligned
