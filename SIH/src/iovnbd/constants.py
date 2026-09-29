"""
IO-VNBD Constants, Schemas, and Reference Frames
"""

from typing import Dict, List

# Earth & Geodetic Constants (WGS-84)
WGS84_A = 6378137.0          # Semi-major axis (meters)
WGS84_F = 1.0 / 298.257223563 # Flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F) # Semi-minor axis (meters)
WGS84_E_SQ = 2.0 * WGS84_F - WGS84_F ** 2 # Eccentricity squared
GRAVITY_STANDARD = 9.80665   # Standard gravity (m/s^2)

# Nominal Sampling Rates
NOMINAL_IMU_HZ = 10.0
NOMINAL_SAMPLE_PERIOD_S = 0.100

# Canonical Schema for IO-VNBD Smartphone Data (S-*.csv)
# 24 raw columns as recorded by the AndroSensor Android app
SMARTPHONE_RAW_COLUMNS: List[str] = [
    "GPS LATITUDE (degrees)",
    "GPS LONGITUDE (degrees)",
    "GPS ALTITUDE (m)",
    "GPS SPEED (Kmh)",
    "GPS ACCURACY (m)",
    "GPS ORIENTATION (°)",
    "GPS SATELLITES IN RANGE",
    "TIME SINCE START (ms)",
    "DATE (YYYY-MO-DD HH-MI-SS_SSS)",
    "ACCELEROMETER X (m/s²)",
    "ACCELEROMETER Y (m/s²)",
    "ACCELEROMETER Z (m/s²)",
    "GRAVITY X (m/s²)",
    "GRAVITY Y (m/s²)",
    "GRAVITY Z (m/s²)",
    "GYROSCOPE Yaw (rad/s)",
    "GYROSCOPE Pitch (rad/s)",
    "GYROSCOPE Roll (rad/s)",
    "MAGNETIC FIELD X (μT)",
    "MAGNETIC FIELD Y (μT)",
    "MAGNETIC FIELD Z (μT)",
    "ORIENTATION (Yaw) (°)",
    "ORIENTATION (Pitch) (°)",
    "ORIENTATION (Roll ) (°)",
]

# Standardized Internal Names for Smartphone Streams
CANONICAL_PHONE_FIELDS: Dict[str, str] = {
    "lat": "lat",
    "lon": "lon",
    "alt_m": "alt_m",
    "gps_speed_kmh": "gps_speed_kmh",
    "gps_accuracy_m": "gps_accuracy_m",
    "gps_bearing_deg": "gps_bearing_deg",
    "satellites": "satellites",
    "time_ms": "time_ms",
    "datetime_str": "datetime_str",
    "ax": "ax", # m/s^2
    "ay": "ay", # m/s^2
    "az": "az", # m/s^2
    "grav_x": "grav_x", # m/s^2
    "grav_y": "grav_y", # m/s^2
    "grav_z": "grav_z", # m/s^2
    "gyro_yaw": "gyro_yaw",   # rad/s (Z-axis in phone frame)
    "gyro_pitch": "gyro_pitch", # rad/s (X-axis in phone frame)
    "gyro_roll": "gyro_roll",   # rad/s (Y-axis in phone frame)
    "mag_x": "mag_x", # microTesla
    "mag_y": "mag_y", # microTesla
    "mag_z": "mag_z", # microTesla
    "phone_yaw_deg": "phone_yaw_deg",
    "phone_pitch_deg": "phone_pitch_deg",
    "phone_roll_deg": "phone_roll_deg",
}

# Canonical Schema for IO-VNBD Vehicle CAN ECU Data (V-*.csv)
VEHICLE_RAW_COLUMNS: List[str] = [
    "No of GPS Satellites Available",
    "Time Since Start of Day (seconds)",
    "Latitude (degrees)",
    "Longitude (degrees)",
    "Velocity (km/hr)",
    "Heading (degrees)",
    "Height (km)",
    "Vertical velocity (km/hr)",
    "Sample period (seconds)",
    "Steering Angle (degrees)",
    "Wheel Speed Front Left (rad/sec)",
    "Wheel Speed Front Right (rad/sec)",
    "Wheel Speed Rear Left (rad/sec)",
    "Wheel Speed Rear Right (rad/sec)",
    "Yaw Rate (deg/sec)",
    "Indicated Vehicle Speed (km/hr)",
    "Indicated Longitudinal Acceleration (g)",
    "Indicated Lateral Acceleration (g)",
    "Handbrake (0 or 1)",
    "Gear Requested (Number fof gear employed 1-5)",
    "Gear (Number fof gear employed 1-5)",
    "Engine Speed (rev/min)",
    "Coolant Temperature (degrees)",
    "Clutch Position (0 or 1)",
    "Brake Pressure (psi)",
    "Brake Position (0 or 1)",
    "Battery Voltage (volts)",
    "Air Temperature (degrees)",
    "Accelerator Pedal Position (%)",
]
