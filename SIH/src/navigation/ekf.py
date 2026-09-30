
import numpy as np

class GNSSStateMachine:
    def __init__(self):
        self.state = "GNSS_AVAILABLE"
        self.outage_duration = 0.0

    def update(self, has_gnss, dt):
        if has_gnss:
            if self.state in ["GNSS_LOST", "DEAD_RECKONING", "GNSS_DEGRADED"]:
                self.state = "GNSS_REACQUIRED"
            else:
                self.state = "GNSS_AVAILABLE"
            self.outage_duration = 0.0
        else:
            self.outage_duration += dt
            if self.outage_duration < 3.0:
                self.state = "GNSS_DEGRADED"
            elif self.outage_duration < 10.0:
                self.state = "GNSS_LOST"
            else:
                self.state = "DEAD_RECKONING"
        return self.state


class EKF:
    """Loosely coupled EKF for Dead Reckoning (Pos, Vel)."""
    def __init__(self, dt):
        self.dt = dt
        # State: [Pos_E, Pos_N, Vel_E, Vel_N]
        self.x = np.zeros(4)
        self.P = np.eye(4) * 10.0
        
        self.F = np.eye(4)
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        
        self.Q = np.eye(4) * 0.1
        self.Q[2, 2] = 0.5
        self.Q[3, 3] = 0.5
        
        # GNSS measurement
        self.H_gnss = np.eye(4)
        self.R_gnss = np.eye(4) * 5.0
        
        # Velocity measurement (AI Speed)
        self.H_vel = np.zeros((2, 4))
        self.H_vel[0, 2] = 1.0
        self.H_vel[1, 3] = 1.0
        self.R_vel = np.eye(2) * 2.0

    def predict(self, acc_e, acc_n):
        # We can incorporate INS acceleration as control input
        u = np.array([0.5 * acc_e * self.dt**2, 0.5 * acc_n * self.dt**2, acc_e * self.dt, acc_n * self.dt])
        self.x = self.F @ self.x + u
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update_gnss(self, pos_e, pos_n, vel_e, vel_n):
        z = np.array([pos_e, pos_n, vel_e, vel_n])
        y = z - self.H_gnss @ self.x
        S = self.H_gnss @ self.P @ self.H_gnss.T + self.R_gnss
        K = self.P @ self.H_gnss.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        # Joseph form
        I_KH = np.eye(4) - K @ self.H_gnss
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R_gnss @ K.T

    def update_velocity(self, vel_e, vel_n, confidence):
        z = np.array([vel_e, vel_n])
        y = z - self.H_vel @ self.x
        
        R = self.R_vel / max(0.1, confidence)
        S = self.H_vel @ self.P @ self.H_vel.T + R
        K = self.P @ self.H_vel.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        I_KH = np.eye(4) - K @ self.H_vel
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T
        
    def apply_nhc(self, heading, confidence):
        """Non-holonomic constraint: lateral velocity = 0"""
        # Direction of lateral velocity: [-sin(heading), cos(heading)]
        # We want [-sin(h), cos(h)] dot [v_e, v_n] = 0
        H_nhc = np.array([[-np.sin(heading), np.cos(heading), 0, 0]]) # Wait, state is P_E, P_N, V_E, V_N
        H_nhc = np.array([[0, 0, -np.sin(heading), np.cos(heading)]])
        
        z = np.array([0.0])
        y = z - H_nhc @ self.x
        R_nhc = np.array([[1.0]]) / max(0.1, confidence)
        
        S = H_nhc @ self.P @ H_nhc.T + R_nhc
        K = self.P @ H_nhc.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        I_KH = np.eye(4) - K @ H_nhc
        self.P = I_KH @ self.P @ I_KH.T + K @ R_nhc @ K.T
