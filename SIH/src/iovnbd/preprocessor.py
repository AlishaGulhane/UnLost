"""
IO-VNBD Preprocessor & Geodetic Coordinate Conversion
Converts raw sensor streams into calibrated, localized East-North-Up navigation data.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
from scipy import signal

from .constants import GRAVITY_STANDARD, NOMINAL_IMU_HZ, WGS84_A, WGS84_E_SQ


def geodetic_to_enu(
    lat: np.ndarray,
    lon: np.ndarray,
    alt: np.ndarray,
    lat0: float,
    lon0: float,
    alt0: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert WGS84 Geodetic coordinates (lat, lon, alt) to Local East-North-Up (ENU) coordinates (meters).
    Origin is (lat0, lon0, alt0).
    """
    phi0 = np.deg2rad(lat0)
    phi = np.deg2rad(lat)
    dphi = phi - phi0
    dlam = np.deg2rad(lon - lon0)

    # Radii of curvature for WGS-84
    sin_phi0 = np.sin(phi0)
    r_n = WGS84_A / np.sqrt(1.0 - WGS84_E_SQ * (sin_phi0 ** 2)) # Prime vertical radius
    r_m = WGS84_A * (1.0 - WGS84_E_SQ) / ((1.0 - WGS84_E_SQ * (sin_phi0 ** 2)) ** 1.5) # Meridian radius

    # Local ENU projection
    east = dlam * r_n * np.cos(phi0)
    north = dphi * r_m
    up = alt - alt0

    return east, north, up


def enu_to_geodetic(
    east: np.ndarray,
    north: np.ndarray,
    up: np.ndarray,
    lat0: float,
    lon0: float,
    alt0: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert Local ENU coordinates (meters) back to WGS84 (lat, lon, alt).
    """
    phi0 = np.deg2rad(lat0)
    sin_phi0 = np.sin(phi0)
    r_n = WGS84_A / np.sqrt(1.0 - WGS84_E_SQ * (sin_phi0 ** 2))
    r_m = WGS84_A * (1.0 - WGS84_E_SQ) / ((1.0 - WGS84_E_SQ * (sin_phi0 ** 2)) ** 1.5)

    dphi = north / r_m
    dlam = east / (r_n * np.cos(phi0))

    lat = np.rad2deg(phi0 + dphi)
    lon = np.rad2deg(np.deg2rad(lon0) + dlam)
    alt = alt0 + up

    return lat, lon, alt


class NavigationPreprocessor:
    """
    Preprocesses raw IO-VNBD smartphone data for navigation and dead reckoning.
    """

    def __init__(self, target_hz: float = NOMINAL_IMU_HZ):
        self.target_hz = target_hz
        self.dt = 1.0 / target_hz

    def preprocess_sequence(
        self,
        df: pd.DataFrame,
        reference_origin: Optional[Tuple[float, float, float]] = None,
        apply_lowpass: bool = False,
        cutoff_hz: float = 3.0,
    ) -> pd.DataFrame:
        """
        Preprocess the sequence:
        1. Establish ENU coordinate frame with ground truth trajectory.
        2. Compute linear acceleration (removing gravity).
        3. Compute ground-truth heading, velocity, and distance increments.
        4. Optionally apply Butterworth low-pass filter to IMU signals.
        """
        processed = df.copy()

        # 1. Determine origin
        valid_gps = processed[processed["lat"].notna() & processed["lon"].notna()]
        if len(valid_gps) == 0:
            raise ValueError("No valid GPS fixes in sequence to establish origin.")

        if reference_origin is None:
            lat0 = float(valid_gps["lat"].iloc[0])
            lon0 = float(valid_gps["lon"].iloc[0])
            alt0 = float(valid_gps["alt_m"].iloc[0]) if "alt_m" in valid_gps else 0.0
        else:
            lat0, lon0, alt0 = reference_origin

        processed["origin_lat"] = lat0
        processed["origin_lon"] = lon0
        processed["origin_alt"] = alt0

        # 2. Local ENU coordinates
        east, north, up = geodetic_to_enu(
            processed["lat"].to_numpy(),
            processed["lon"].to_numpy(),
            processed["alt_m"].fillna(alt0).to_numpy(),
            lat0,
            lon0,
            alt0,
        )
        processed["east_m"] = east
        processed["north_m"] = north
        processed["up_m"] = up

        # 3. Ground truth cumulative distance and step vectors
        d_east = np.diff(east, prepend=east[0])
        d_north = np.diff(north, prepend=north[0])
        step_dist = np.sqrt(d_east ** 2 + d_north ** 2)
        processed["step_distance_m"] = step_dist
        processed["cum_distance_m"] = np.cumsum(np.nan_to_num(step_dist))

        # Ground truth heading from trajectory displacement
        # 0 = North (+Y), pi/2 = East (+X)
        gt_heading = np.arctan2(d_east, d_north)
        processed["gt_heading_rad"] = gt_heading
        processed["gt_heading_deg"] = np.rad2deg(gt_heading) % 360.0

        # 4. Linear Acceleration (remove static gravity vector provided by Android SensorManager)
        processed["lin_ax"] = processed["ax"] - processed["grav_x"]
        processed["lin_ay"] = processed["ay"] - processed["grav_y"]
        processed["lin_az"] = processed["az"] - processed["grav_z"]

        # Accelerometer total magnitude
        processed["acc_norm"] = np.sqrt(
            processed["ax"] ** 2 + processed["ay"] ** 2 + processed["az"] ** 2
        )
        processed["lin_acc_norm"] = np.sqrt(
            processed["lin_ax"] ** 2 + processed["lin_ay"] ** 2 + processed["lin_az"] ** 2
        )

        # 5. Optional low-pass filtering on IMU signals
        if apply_lowpass and cutoff_hz < (self.target_hz / 2.0):
            nyquist = 0.5 * self.target_hz
            norm_cutoff = cutoff_hz / nyquist
            b, a = signal.butter(4, norm_cutoff, btype="low", analog=False)

            for col in ["ax", "ay", "az", "lin_ax", "lin_ay", "lin_az", "gyro_yaw", "gyro_pitch", "gyro_roll"]:
                vals = processed[col].to_numpy()
                if np.all(np.isfinite(vals)):
                    processed[f"{col}_filt"] = signal.filtfilt(b, a, vals)
                else:
                    processed[f"{col}_filt"] = vals

        return processed
