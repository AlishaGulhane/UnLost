import numpy as np

def quat_mult(p, q):
    pw, px, py, pz = p
    qw, qx, qy, qz = q
    return np.array([
        pw*qw - px*qx - py*qy - pz*qz,
        pw*qx + px*qw + py*qz - pz*qy,
        pw*qy - px*qz + py*qw + pz*qx,
        pw*qz + px*qy - py*qx + pz*qw,
    ])

def quat_to_rot(q):
    qw, qx, qy, qz = q
    return np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)],
    ])

def euler_to_quat(roll, pitch, yaw):
    cr = np.cos(roll / 2.0)
    sr = np.sin(roll / 2.0)
    cp = np.cos(pitch / 2.0)
    sp = np.sin(pitch / 2.0)
    cy = np.cos(yaw / 2.0)
    sy = np.sin(yaw / 2.0)
    
    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy
    return np.array([qw, qx, qy, qz])

def quat_to_euler(q):
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

    return roll, pitch, yaw

# Test roundtrip
test_angles = [
    (0.0, 0.0, 0.0),
    (0.1, -0.2, 0.5),
    (np.deg2rad(15), np.deg2rad(-30), np.deg2rad(45)),
    (np.deg2rad(-5), np.deg2rad(10), np.deg2rad(170)),
]

for r, p, y in test_angles:
    q = euler_to_quat(r, p, y)
    r2, p2, y2 = quat_to_euler(q)
    assert np.allclose([r, p, y], [r2, p2, y2]), f"Failed for {r},{p},{y} vs {r2},{p2},{y2}"
print("Quaternion <-> Euler roundtrip tests PASSED!")
