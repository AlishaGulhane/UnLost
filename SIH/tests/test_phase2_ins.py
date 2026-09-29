"""
Unit and Integration Tests for Phase 2: Classical Strapdown INS Dead Reckoning
Validates attitude updates, numerical integration, stationary behavior,
output schema, and execution against real IO-VNBD data.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.navigation import (
    INSConfig,
    InertialDeadReckoning,
    compute_ins_metrics,
    euler_to_quaternion,
    quaternion_multiply,
    quaternion_to_euler,
    quaternion_to_rotation_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA_FILE = PROJECT_ROOT / "data" / "processed" / "S-Vta1a_preprocessed.csv"


def test_quaternion_and_euler_consistency():
    """Verify quaternion multiplication, rotation matrix, and Euler conversions."""
    # Identity
    q_id = np.array([1.0, 0.0, 0.0, 0.0])
    R_id = quaternion_to_rotation_matrix(q_id)
    assert np.allclose(R_id, np.eye(3), atol=1e-9)

    # 90 degree yaw rotation (pi/2 around Z-axis)
    yaw_90 = np.pi / 2.0
    q_yaw = euler_to_quaternion(0.0, 0.0, yaw_90)
    assert np.isclose(np.linalg.norm(q_yaw), 1.0, atol=1e-7)

    R_yaw = quaternion_to_rotation_matrix(q_yaw)
    v_body = np.array([1.0, 0.0, 0.0]) # Body +X
    v_nav = R_yaw @ v_body              # In ENU: +X (East) rotated by +90 deg -> +Y (North)
    assert np.allclose(v_nav, [0.0, 1.0, 0.0], atol=1e-7)

    # Euler roundtrip test
    angles = [(0.1, -0.2, 0.5), (0.0, 0.0, 0.0), (-0.3, 0.1, 2.8)]
    for r, p, y in angles:
        q = euler_to_quaternion(r, p, y)
        r_rec, p_rec, y_rec = quaternion_to_euler(q)
        assert np.isclose(r, r_rec, atol=1e-6)
        assert np.isclose(p, p_rec, atol=1e-6)
        assert np.isclose(y, y_rec, atol=1e-6)


def test_timestamp_and_dt_handling():
    """Verify handling of irregular timesteps and dt bounding."""
    ins = InertialDeadReckoning()
    p0 = np.zeros(3)
    v0 = np.zeros(3)
    q0 = np.array([1.0, 0.0, 0.0, 0.0])
    ins.initialize(p0, v0, q0)

    acc = np.array([1.0, 0.0, 0.0])
    gyro = np.zeros(3)

    # Step with normal dt = 0.1 s
    p1, v1, _, _, _ = ins.propagate_step(0.1, acc, gyro)
    assert np.isclose(v1[0], 0.05, atol=1e-5) # Trapezoidal: 0.5 * (0 + 1) * 0.1 = 0.05

    # Step with zero or negative dt should default safely without crashing or NaN
    p2, v2, _, _, _ = ins.propagate_step(0.0, acc, gyro)
    assert np.all(np.isfinite(p2))
    assert np.all(np.isfinite(v2))


def test_orientation_propagation():
    """Verify gyroscope integration correctly tracks attitude rotation."""
    config = INSConfig(use_android_linear_acc=True)
    ins = InertialDeadReckoning(config=config)
    ins.initialize(np.zeros(3), np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0]))

    # Pure constant yaw rate: 90 deg/s (pi/2 rad/s) for 1 second (10 steps of 0.1s)
    yaw_rate = np.pi / 2.0
    gyro_input = np.array([0.0, 0.0, yaw_rate]) # [wx, wy, wz]
    acc_input = np.zeros(3)

    for _ in range(10):
        _, _, q, rpy, _ = ins.propagate_step(0.1, acc_input, gyro_input)
        assert np.isclose(np.linalg.norm(q), 1.0, atol=1e-6)

    # After 1 second at pi/2 rad/s, total yaw should be approx pi/2 rad (90 deg)
    assert np.isclose(rpy[2], np.pi / 2.0, atol=1e-2)
    assert np.isclose(rpy[0], 0.0, atol=1e-4) # Roll unchanged
    assert np.isclose(rpy[1], 0.0, atol=1e-4) # Pitch unchanged


def test_stationary_behavior():
    """Verify that ideal stationary inputs produce zero velocity and position drift."""
    config = INSConfig(use_android_linear_acc=True)
    ins = InertialDeadReckoning(config=config)
    ins.initialize(np.zeros(3), np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0]))

    # Stationary: zero linear acceleration and zero angular rate
    acc_stationary = np.zeros(3)
    gyro_stationary = np.zeros(3)

    for _ in range(100): # 10 seconds of simulated stationary data
        p, v, q, _, _ = ins.propagate_step(0.1, acc_stationary, gyro_stationary)

    assert np.allclose(p, np.zeros(3), atol=1e-9)
    assert np.allclose(v, np.zeros(3), atol=1e-9)
    assert np.allclose(q, [1.0, 0.0, 0.0, 0.0], atol=1e-9)


def test_acceleration_and_velocity_integration():
    """Verify constant acceleration integration matches analytic kinematics: v = a*t, p = 0.5*a*t^2."""
    config = INSConfig(use_android_linear_acc=True, integration_method="trapezoidal")
    ins = InertialDeadReckoning(config=config)
    ins.initialize(np.zeros(3), np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0]))

    acc_const = np.array([2.0, 0.0, 0.0]) # 2 m/s^2 along East
    gyro_zero = np.zeros(3)

    dt = 0.05
    total_steps = 100 # 5.0 seconds
    for _ in range(total_steps):
        p, v, _, _, _ = ins.propagate_step(dt, acc_const, gyro_zero)

    expected_v = 2.0 * 5.0 # 10.0 m/s
    expected_p = 0.5 * 2.0 * (5.0**2) # 25.0 m

    assert np.isclose(v[0], expected_v, atol=1e-1)
    assert np.isclose(p[0], expected_p, atol=0.5)


def test_output_schema_and_finite_values():
    """Verify that propagate_sequence outputs the canonical schema with all expected columns."""
    # Synthetic DataFrame with 50 samples
    n = 50
    t_ms = np.arange(n) * 100
    df_synth = pd.DataFrame({
        "time_ms": t_ms,
        "elapsed_s": t_ms / 1000.0,
        "dt_s": np.full(n, 0.1),
        "ax": np.zeros(n),
        "ay": np.zeros(n),
        "az": np.full(n, 9.80665),
        "lin_ax": np.zeros(n),
        "lin_ay": np.zeros(n),
        "lin_az": np.zeros(n),
        "gyro_yaw": np.zeros(n),
        "gyro_pitch": np.zeros(n),
        "gyro_roll": np.zeros(n),
        "east_m": np.zeros(n),
        "north_m": np.zeros(n),
        "up_m": np.zeros(n),
        "cum_distance_m": np.zeros(n),
        "phone_yaw_deg": np.zeros(n),
    })

    ins = InertialDeadReckoning()
    df_out = ins.propagate_sequence(df_synth)

    required_cols = [
        "time_ms", "elapsed_s", "dt_s",
        "ins_east_m", "ins_north_m", "ins_up_m",
        "ins_ve_mps", "ins_vn_mps", "ins_vu_mps", "ins_speed_mps",
        "ins_roll_deg", "ins_pitch_deg", "ins_yaw_deg",
        "ins_qw", "ins_qx", "ins_qy", "ins_qz",
        "ins_acc_east", "ins_acc_north", "ins_acc_up",
        "pos_error_2d_m", "pos_error_3d_m",
    ]
    for col in required_cols:
        assert col in df_out.columns, f"Missing required output column: {col}"

    # Check finite values
    assert not df_out[required_cols].isna().any().any()
    assert np.all(np.isfinite(df_out[required_cols].to_numpy()))


def test_short_real_data_ins_execution():
    """Verify INS execution on real IO-VNBD data slice."""
    assert REAL_DATA_FILE.is_file(), f"Real preprocessed file {REAL_DATA_FILE} not found!"
    df_real = pd.read_csv(REAL_DATA_FILE)

    # Slice first 200 samples (20 seconds)
    df_slice = df_real.iloc[:200].copy()

    ins = InertialDeadReckoning(INSConfig(use_android_linear_acc=True))
    df_ins = ins.propagate_sequence(df_slice)

    assert len(df_ins) == 200
    assert np.isclose(df_ins["ins_east_m"].iloc[0], 0.0, atol=1e-3)
    assert np.isclose(df_ins["ins_north_m"].iloc[0], 0.0, atol=1e-3)
    assert np.all(np.isfinite(df_ins["ins_speed_mps"]))

    metrics = compute_ins_metrics(df_ins)
    assert "pos_rmse_2d_m" in metrics
    assert "final_pos_error_2d_m" in metrics
    assert metrics["final_pos_error_2d_m"] >= 0.0
