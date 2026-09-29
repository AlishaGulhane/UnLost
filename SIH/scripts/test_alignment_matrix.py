"""
Test Phone-to-Vehicle Alignment on real IO-VNBD data
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_leveling_matrix(fx, fy, fz):
    """Compute SO(3) leveling matrix R_level from mean specific force."""
    g = np.sqrt(fx**2 + fy**2 + fz**2)
    # Unit vertical vector in body frame: u_z = [fx, fy, fz] / g
    u_z = np.array([fx, fy, fz]) / g
    
    pitch = np.arctan2(-fx, np.sqrt(fy**2 + fz**2))
    roll = np.arctan2(fy, fz)
    
    # R_x(-roll)
    cr = np.cos(-roll); sr = np.sin(-roll)
    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cr, -sr],
        [0.0, sr, cr],
    ])
    
    # R_y(-pitch)
    cp = np.cos(-pitch); sp = np.sin(-pitch)
    Ry = np.array([
        [cp, 0.0, sp],
        [0.0, 1.0, 0.0],
        [-sp, 0.0, cp],
    ])
    
    R_level = Rx @ Ry
    return R_level, roll, pitch

def test_alignment():
    for seq in ["S-Vta1a", "S-Vta2"]:
        df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / f"{seq}_preprocessed.csv")
        fx0 = df.loc[:30, "ax"].mean()
        fy0 = df.loc[:30, "ay"].mean()
        fz0 = df.loc[:30, "az"].mean()
        
        R_level, roll0, pitch0 = build_leveling_matrix(fx0, fy0, fz0)
        
        # Test SO(3) properties
        is_ortho = np.allclose(R_level @ R_level.T, np.eye(3), atol=1e-10)
        det_val = np.linalg.det(R_level)
        is_det1 = np.isclose(det_val, 1.0, atol=1e-10)
        
        # Check leveled specific force
        f_leveled = R_level @ np.array([fx0, fy0, fz0])
        
        print(f"\n=== {seq} Alignment Check ===")
        print(f"Roll: {np.rad2deg(roll0):.2f}°, Pitch: {np.rad2deg(pitch0):.2f}°")
        print(f"R_level SO(3) valid: Orthogonal={is_ortho}, Det={det_val:.6f}")
        print(f"Raw specific force:     [{fx0:.3f}, {fy0:.3f}, {fz0:.3f}]")
        print(f"Leveled specific force: [{f_leveled[0]:.3f}, {f_leveled[1]:.3f}, {f_leveled[2]:.3f}] (Z is Up: {f_leveled[2]:.3f} m/s^2)")

if __name__ == "__main__":
    test_alignment()
