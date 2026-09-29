"""
Navigation Module for IDR-NAV
Contains Classical Strapdown Inertial Navigation System (INS),
Phone-to-Vehicle Alignment (R_b^v), and diagnostic visualization tools.
"""

from .alignment import (
    AlignmentConfig,
    PhoneToVehicleAlignment,
    align_vectors_rodrigues,
    validate_rotation_matrix,
)
from .ins import (
    INSConfig,
    INSState,
    InitialAttitudeAlignment,
    InertialDeadReckoning,
    compute_ins_metrics,
    euler_to_quaternion,
    quaternion_multiply,
    quaternion_to_euler,
    quaternion_to_rotation_matrix,
)
from .visualization import (
    plot_alignment_signals,
    plot_drift_vs_distance,
    plot_orientation_profiles,
    plot_phase2_vs_phase3_error,
    plot_phase2_vs_phase3_trajectory,
    plot_position_error_vs_distance,
    plot_position_error_vs_time,
    plot_trajectory_comparison,
    plot_velocity_comparison,
)

__all__ = [
    "AlignmentConfig",
    "PhoneToVehicleAlignment",
    "align_vectors_rodrigues",
    "validate_rotation_matrix",
    "INSConfig",
    "INSState",
    "InitialAttitudeAlignment",
    "InertialDeadReckoning",
    "compute_ins_metrics",
    "quaternion_multiply",
    "quaternion_to_rotation_matrix",
    "euler_to_quaternion",
    "quaternion_to_euler",
    "plot_trajectory_comparison",
    "plot_position_error_vs_time",
    "plot_position_error_vs_distance",
    "plot_velocity_comparison",
    "plot_orientation_profiles",
    "plot_drift_vs_distance",
    "plot_alignment_signals",
    "plot_phase2_vs_phase3_trajectory",
    "plot_phase2_vs_phase3_error",
]
