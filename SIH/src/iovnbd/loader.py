"""
IO-VNBD Dataset Loader & Parser
Supports raw smartphone and vehicle sensor CSVs from the official benchmark.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .constants import (
    CANONICAL_PHONE_FIELDS,
    NOMINAL_IMU_HZ,
    SMARTPHONE_RAW_COLUMNS,
    VEHICLE_RAW_COLUMNS,
)


@dataclass
class DatasetMetadata:
    sequence_name: str
    file_path: Path
    total_samples: int
    duration_s: float
    effective_hz: float
    num_missing_gps: int
    gps_lat_range: Tuple[float, float]
    gps_lon_range: Tuple[float, float]
    speed_kmh_max: float
    has_vehicle_ecu: bool


class IOVNBDLoader:
    """
    Robust loader for IO-VNBD dataset files.
    """

    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/raw")

    @staticmethod
    def _normalize_header(col_name: str) -> str:
        """Strip non-ascii symbols, whitespace, and brackets for robust matching."""
        s = col_name.strip()
        # Remove non-ascii
        ascii_clean = s.encode("ascii", "ignore").decode("ascii").strip()
        return ascii_clean.lower()

    def load_smartphone_sequence(
        self,
        file_path_or_name: Union[str, Path],
        clean_dropouts: bool = True,
        remove_duplicate_timestamps: bool = True,
    ) -> Tuple[pd.DataFrame, DatasetMetadata]:
        """
        Load and parse a smartphone sequence CSV (e.g. S-Vta1a.csv, S-S1.csv).
        """
        path = Path(file_path_or_name)
        if not path.is_file():
            # Try finding in data_dir
            candidate = self.data_dir / path.name
            if candidate.is_file():
                path = candidate
            else:
                raise FileNotFoundError(f"IO-VNBD file not found: {file_path_or_name}")

        df = pd.read_csv(path, encoding_errors="replace", low_memory=False)
        if df.shape[1] < 20:
            raise ValueError(
                f"File {path.name} has only {df.shape[1]} columns; expected at least 24 for IO-VNBD smartphone data."
            )

        # Standard canonical column mapping
        col_names = list(CANONICAL_PHONE_FIELDS.keys())
        if df.shape[1] == len(col_names):
            df.columns = col_names
        elif df.shape[1] >= len(col_names):
            df = df.iloc[:, : len(col_names)]
            df.columns = col_names
        else:
            raise ValueError(
                f"Unexpected column count {df.shape[1]} in {path.name}. Required {len(col_names)}."
            )

        # Convert numeric columns
        numeric_cols = [c for c in col_names if c not in ("datetime_str", "satellites")]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Parse timestamps
        if remove_duplicate_timestamps:
            df = df.drop_duplicates(subset=["time_ms"]).sort_values("time_ms")

        # Basic validity filter: time_ms must be valid and non-negative
        df = df[df["time_ms"].notna() & (df["time_ms"] >= 0)].copy()

        # Compute elapsed time in seconds
        t0_ms = df["time_ms"].iloc[0]
        df["elapsed_s"] = (df["time_ms"] - t0_ms) / 1000.0
        df["dt_s"] = df["elapsed_s"].diff().fillna(1.0 / NOMINAL_IMU_HZ)

        # Convert speed to m/s
        df["speed_mps"] = df["gps_speed_kmh"] / 3.6

        # Convert gyro from rad/s or check magnitude
        # Phone gyros in IO-VNBD are in rad/s: gyro_yaw, gyro_pitch, gyro_roll

        # Handling dropouts / interpolation if requested
        num_missing_gps = df["lat"].isna().sum()
        if clean_dropouts:
            # Interpolate brief IMU missing values
            imu_cols = ["ax", "ay", "az", "grav_x", "grav_y", "grav_z", "gyro_yaw", "gyro_pitch", "gyro_roll"]
            df[imu_cols] = df[imu_cols].interpolate(method="linear", limit=5).bfill().ffill()

        df = df.reset_index(drop=True)

        duration_s = float(df["elapsed_s"].iloc[-1]) if len(df) > 0 else 0.0
        effective_hz = float(len(df) / duration_s) if duration_s > 0 else NOMINAL_IMU_HZ
        valid_gps = df[df["lat"].notna() & df["lon"].notna()]
        lat_range = (float(valid_gps["lat"].min()), float(valid_gps["lat"].max())) if len(valid_gps) > 0 else (0.0, 0.0)
        lon_range = (float(valid_gps["lon"].min()), float(valid_gps["lon"].max())) if len(valid_gps) > 0 else (0.0, 0.0)
        max_speed = float(df["gps_speed_kmh"].max()) if len(df) > 0 else 0.0

        metadata = DatasetMetadata(
            sequence_name=path.stem,
            file_path=path,
            total_samples=len(df),
            duration_s=duration_s,
            effective_hz=effective_hz,
            num_missing_gps=int(num_missing_gps),
            gps_lat_range=lat_range,
            gps_lon_range=lon_range,
            speed_kmh_max=max_speed,
            has_vehicle_ecu=False,
        )

        return df, metadata

    def split_sequence(
        self,
        df: pd.DataFrame,
        train_fraction: float = 0.70,
        val_fraction: float = 0.15,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split a continuous driving sequence into sequential train/val/test splits.
        Preserves temporal continuity.
        """
        n = len(df)
        train_end = int(n * train_fraction)
        val_end = int(n * (train_fraction + val_fraction))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        return train_df, val_df, test_df
