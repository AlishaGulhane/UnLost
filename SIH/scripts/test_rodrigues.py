import numpy as np

def align_vectors_rodrigues(v_from, v_to):
    """Compute SO(3) rotation matrix R such that R @ v_from = v_to with zero parasitic yaw."""
    a = v_from / np.linalg.norm(v_from)
    b = v_to / np.linalg.norm(v_to)
    
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    
    if s < 1e-12:
        # Collinear vectors
        if c > 0:
            return np.eye(3)
        else:
            # 180 degree rotation around any orthogonal axis
            ortho = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            axis = np.cross(a, ortho)
            axis = axis / np.linalg.norm(axis)
            return -np.eye(3) + 2.0 * np.outer(axis, axis)
            
    # Skew symmetric matrix of v
    vx = np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0]
    ])
    
    R = np.eye(3) + vx + (vx @ vx) * (1.0 / (1.0 + c))
    return R

# Test on arbitrary vectors
test_vectors = [
    np.array([-0.045, -0.004, 9.831]),
    np.array([-1.109, -2.083, 9.405]),
    np.array([1.5, -3.2, 8.9]),
    np.array([0.0, 0.0, 9.81]),
]

target = np.array([0.0, 0.0, 1.0])

for f in test_vectors:
    R = align_vectors_rodrigues(f, target)
    f_rot = R @ f
    # Check SO(3)
    assert np.allclose(R @ R.T, np.eye(3)), "Not orthogonal"
    assert np.isclose(np.linalg.det(R), 1.0), "Det != 1"
    # Check alignment
    expected_z = np.linalg.norm(f)
    assert np.allclose(f_rot, [0.0, 0.0, expected_z], atol=1e-10), f"Failed alignment: {f_rot} vs [0, 0, {expected_z}]"
    print(f"Input: {f} -> Leveled: {f_rot} | Det={np.linalg.det(R):.6f} [PASSED]")
