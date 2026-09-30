
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

class MotionDetector:
    """Rules-based motion and vibration classification from raw/filtered IMU signals."""
    def __init__(self):
        self.stat_thresh = 0.5  # m/s^2 variance
        self.brake_thresh = -1.5 # m/s^2 forward acc
        self.turn_thresh = 0.3   # rad/s yaw rate
        self.pothole_thresh = 4.0 # m/s^2 vertical variance

    def detect_batch(self, acc_nav_batch, gyro_b_batch):
        """Batch detection for a sliding window."""
        states = []
        for i in range(len(acc_nav_batch)):
            acc = acc_nav_batch[i]
            gyro = gyro_b_batch[i]
            
            # Simple heuristic
            acc_forward = acc[1] # North/forward
            acc_up = acc[2]
            yaw_rate = gyro[2]
            
            if acc_forward < self.brake_thresh:
                states.append("braking")
            elif abs(yaw_rate) > self.turn_thresh:
                states.append("turning")
            elif abs(acc_up) > self.pothole_thresh:
                states.append("pothole")
            else:
                states.append("normal")
        return states


class SpeedEstimator:
    """AI Speed Estimation using IMU features."""
    def __init__(self, window_size=50):
        self.model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        self.scaler = StandardScaler()
        self.window_size = window_size
        self.is_trained = False

    def _extract_features(self, acc_seq, gyro_seq):
        n_samples = len(acc_seq)
        features = []
        # Moving window
        for i in range(n_samples - self.window_size + 1):
            w_acc = acc_seq[i:i+self.window_size]
            w_gyro = gyro_seq[i:i+self.window_size]
            
            f = np.concatenate([
                np.mean(w_acc, axis=0),
                np.std(w_acc, axis=0),
                np.max(w_acc, axis=0) - np.min(w_acc, axis=0),
                np.mean(w_gyro, axis=0),
                np.std(w_gyro, axis=0)
            ])
            features.append(f)
        return np.array(features)

    def train(self, acc_seq, gyro_seq, speed_seq):
        print("Extracting features for training...")
        X = self._extract_features(acc_seq, gyro_seq)
        y = speed_seq[self.window_size - 1:]
        
        # Valid speeds only (GNSS > 1 km/h moving or valid)
        mask = ~np.isnan(y)
        X = X[mask]
        y = y[mask]
        
        print(f"Training Random Forest on {len(X)} samples...")
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        print("Training complete.")
        
        # Score
        preds = self.model.predict(X_scaled)
        rmse = np.sqrt(np.mean((y - preds)**2))
        mae = np.mean(np.abs(y - preds))
        print(f"Train RMSE: {rmse:.2f} m/s, MAE: {mae:.2f} m/s")

    def predict_batch(self, acc_seq, gyro_seq):
        if not self.is_trained:
            raise ValueError("Model not trained.")
        X = self._extract_features(acc_seq, gyro_seq)
        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        
        # Confidence based on out-of-distribution (simple heuristic: distance to training mean)
        # For an edge-friendly approach, we just output a flat 0.8 confidence for now
        confidences = np.full(len(preds), 0.8)
        
        # Pad beginning
        pad_len = self.window_size - 1
        preds = np.concatenate([np.zeros(pad_len), preds])
        confidences = np.concatenate([np.zeros(pad_len), confidences])
        
        return preds, confidences
