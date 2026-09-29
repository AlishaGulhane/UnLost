# Phase 2 Technical Report: Classical Strapdown INS / Dead Reckoning Baseline

## 1. Executive Summary

This report establishes the **Phase 2: Pure Classical Strapdown Inertial Navigation System (INS) / Dead Reckoning Baseline** for the **Intelligent GNSS-Denied Vehicle Navigation Using AI-Enhanced Dead Reckoning (IDR-NAV)** project.

All experiments were executed on real ground-vehicle runs from the **IO-VNBD** benchmark dataset (`S-Vta1a` and `S-Vta2`). In accordance with strict evaluation rules:
- No artificial GNSS position corrections or resets were applied during propagation.
- No ground-truth velocity was fed into the INS.
- No future-sample leakage occurred.
- The pipeline represents a **pure, unassisted classical strapdown dead reckoning baseline**, demonstrating the real physical error growth and sensor drift characteristics of smartphone MEMS inertial sensors.

---

## 2. Independent Verification of Phase 1 Distance & Speed Metrics

Before interpreting inertial drift relative to travelled distance, an independent audit of the raw dataset CSVs and Phase 1 calculation logic was conducted to resolve the apparent inconsistency in `S-Vta1a` (42.79 min duration, reported 28.78 km/h peak speed, but 40.55 km cumulative distance).

### 2.1 Investigation Findings

1. **Speed Column Identification**:
   In the raw smartphone CSVs (`data/raw/S-Vta1a.csv` and `data/raw/S-Vta2.csv`), column index 3 is titled `' GPS SPEED (Kmh)'`.
2. **Speed Unit Misinterpretation in Raw Log**:
   Although the column header string states `(Kmh)`, the actual numeric values logged by AndroSensor from the Android Location API (`Location.getSpeed()`) are recorded in **meters per second (m/s)**.
   - For `S-Vta1a`: Raw column mean = $15.68$, max = $28.78$.
   - If interpreted as km/h: A vehicle travelling at max $28.78\text{ km/h}$ for $42.79\text{ min}$ could cover at most $20.52\text{ km}$.
   - If interpreted as m/s: Peak speed is $28.78\text{ m/s} = \mathbf{103.61\text{ km/h}}$ ($64.38\text{ mph}$), and mean speed is $15.68\text{ m/s} = \mathbf{56.46\text{ km/h}}$ ($35.08\text{ mph}$). This represents standard UK highway driving, exactly matching the experimental protocol described in the IO-VNBD publication.
3. **Cumulative Distance Calculation**:
   Cumulative distance was calculated by projecting WGS84 GNSS coordinates $(\text{lat}, \text{lon}, \text{alt})$ onto a Local East-North-Up (ENU) Cartesian tangent plane using WGS-84 ellipsoidal curvature radii and summing 2D Euclidean step displacements:
   $$\Delta d_k = \sqrt{(E_k - E_{k-1})^2 + (N_k - N_{k-1})^2}, \quad D_{\text{cum}} = \sum_{k=1}^N \Delta d_k$$
4. **Cross-Validation (Numerical Integration of Speed vs Coordinate Distance)**:
   - For `S-Vta1a`:
     - Cumulative ENU step distance: **40,546.34 m (40.55 km)**
     - Integral of raw speed as m/s ($\sum v \Delta t$): **40,270.50 m (40.27 km)**
     - Discrepancy between coordinate distance and speed integral: **0.68%**
   - For `S-Vta2`:
     - Cumulative ENU step distance: **11,074.78 m (11.07 km)**
     - Integral of raw speed as m/s ($\sum v \Delta t$): **11,002.18 m (11.00 km)**
     - Discrepancy between coordinate distance and speed integral: **0.65%**
5. **Phase 1 Pipeline Error**:
   In Phase 1, `loader.py` read the column value $28.78$, assumed it was km/h, and divided it by $3.6$ (`speed_mps = gps_speed_kmh / 3.6`), erroneously scaling down the velocity to $7.99\text{ m/s}$.

### 2.2 Metric Verification & Correction Summary

| Metric | Sequence `S-Vta1a` | Sequence `S-Vta2` | Verification & Correction Notes |
| :--- | :---: | :---: | :--- |
| **Duration** | 2,567.5 s (42.79 min) | 1,099.0 s (18.32 min) | Verified from monotonic hardware clock (`TIME SINCE START (ms)`) |
| **Original Phase 1 Peak Speed** | 28.78 km/h | 22.58 km/h | Erroneously reported by taking m/s value as km/h |
| **Corrected Verified Peak Speed** | **103.61 km/h (28.78 m/s)** | **81.29 km/h (22.58 m/s)** | Verified: raw CSV column is in m/s; multiplied by 3.6 |
| **Corrected Verified Mean Speed** | **56.46 km/h (15.68 m/s)** | **36.04 km/h (10.01 m/s)** | Consistent with highway driving and roundabouts |
| **Cumulative Trajectory Distance** | **40.55 km (40,546.3 m)** | **11.07 km (11,074.8 m)** | Independently verified from ENU displacements |
| **Net Start-to-End Displacement** | 25.36 km (25,355.6 m) | 6.51 km (6,506.4 m) | Verified Euclidean straight-line endpoint distance |
| **Speed Integral Consistency** | **99.32% Match** | **99.35% Match** | Coordinate path matches speed integral within < 0.7% |

With distance and velocity ground truth independently verified and validated, all subsequent INS drift metrics are evaluated against the true verified reference.

---

## 3. Architecture of the Implemented INS Module

The classical INS engine is implemented in `src/navigation/ins.py` with the following modular pipeline:

```text
Preprocessed IO-VNBD Smartphone Data (10 Hz)
                    ↓
        [Initial Attitude Alignment]
    (Roll0, Pitch0 from Gravity; Yaw0 from Azimuth)
                    ↓
          For Each Time Step dt:
  ┌──────────────────────────────────────────────────┐
  │ 1. Gyroscope Angular Rate (omega_b)              │
  │    → Delta Quaternion Update                     │
  │    → q_{k+1} = q_k ⊗ dq, Normalized ||q|| = 1    │
  │    → Euler Angles (Roll, Pitch, Yaw) Extraction   │
  │                                                  │
  │ 2. Direction Cosine Matrix R_b^n(q) Computation  │
  │                                                  │
  │ 3. Acceleration Transformation & Gravity:        │
  │    a^n = R_b^n * a_lin^b                         │
  │                                                  │
  │ 4. Numerical Integration (Trapezoidal Method):   │
  │    v_{k+1} = v_k + 0.5 * (a_k^n + a_{k+1}^n) * dt│
  │    p_{k+1} = p_k + 0.5 * (v_k + v_{k+1}) * dt    │
  └──────────────────────────────────────────────────┘
                    ↓
   Pure Classical Dead-Reckoned INS Trajectory
   (East, North, Up Position, Velocity, Attitude)
```

---

## 4. Mathematical Model

### 4.1 Coordinate Frames
- **Body Frame ($b$)**: Smartphone sensor frame (AndroSensor convention: $X$ lateral/longitudinal, $Y$ longitudinal/lateral, $Z$ out-of-screen normal).
- **Navigation Frame ($n$)**: Local East-North-Up (ENU) Cartesian tangent plane anchored at the sequence origin $(\text{lat}_0, \text{lon}_0, \text{alt}_0)$.
  - $X_n$: East ($+E$)
  - $Y_n$: North ($+N$)
  - $Z_n$: Up ($+U$)
  - Navigation gravity vector: $\mathbf{g}^n = [0, 0, -g]^T$, where $g = 9.80665\text{ m/s}^2$.

### 4.2 Initial Attitude Alignment
During initial near-stationary samples ($N = 30$, first 3 seconds), specific force measurements $\mathbf{f}^b = [f_x, f_y, f_z]^T$ measure the reaction to gravity:
$$\theta_0 = \arctan2(-f_x, \sqrt{f_y^2 + f_z^2}), \quad \phi_0 = \arctan2(f_y, f_z)$$
Initial yaw $\psi_0$ is initialized from the sensor azimuth $\alpha_0$ in Local ENU convention:
$$\psi_0 = \frac{\pi}{2} - \alpha_0$$
The initial attitude is converted to a normalized quaternion $\mathbf{q}_0 = [q_w, q_x, q_y, q_z]^T$.

### 4.3 Attitude Propagation
Given angular velocity from the 3-axis gyroscope $\boldsymbol{\omega}^b = [\omega_x, \omega_y, \omega_z]^T$ over timestep $\Delta t$:
$$\boldsymbol{\theta} = \boldsymbol{\omega}^b \Delta t, \quad \theta = \|\boldsymbol{\theta}\|$$
$$\Delta \mathbf{q} = \begin{bmatrix} \cos(\theta / 2) \\ \frac{\sin(\theta / 2)}{\theta} \boldsymbol{\theta} \end{bmatrix} \quad (\text{or } [1, \frac{1}{2}\boldsymbol{\theta}]^T \text{ for } \theta \to 0)$$
$$\mathbf{q}_{k+1} = \frac{\mathbf{q}_k \otimes \Delta \mathbf{q}}{\|\mathbf{q}_k \otimes \Delta \mathbf{q}\|}$$
Direction Cosine Matrix $\mathbf{R}_b^n(\mathbf{q})$ transforms vectors from body frame to navigation frame:
$$\mathbf{R}_b^n(\mathbf{q}) = \begin{bmatrix}
1 - 2(q_y^2 + q_z^2) & 2(q_x q_y - q_w q_z) & 2(q_x q_z + q_w q_y) \\
2(q_x q_y + q_w q_z) & 1 - 2(q_x^2 + q_z^2) & 2(q_y q_z - q_w q_x) \\
2(q_x q_z - q_w q_y) & 2(q_y q_z + q_w q_x) & 1 - 2(q_x^2 + q_y^2)
\end{bmatrix}$$

### 4.4 Acceleration Coordinate Transformation & Gravity Handling
$$\mathbf{a}_k^n = \mathbf{R}_b^n(\mathbf{q}_k) \mathbf{a}_{\text{lin}, k}^b$$
where $\mathbf{a}_{\text{lin}}^b = \mathbf{f}^b - \mathbf{g}_{\text{sensor}}^b$ is the dynamic linear acceleration in the smartphone frame.

### 4.5 Velocity and Position Integration
Using trapezoidal integration:
$$\mathbf{v}_{k+1} = \mathbf{v}_k + \frac{1}{2} (\mathbf{a}_k^n + \mathbf{a}_{k+1}^n) \Delta t_k$$
$$\mathbf{p}_{k+1} = \mathbf{p}_k + \frac{1}{2} (\mathbf{v}_k + \mathbf{v}_{k+1}) \Delta t_k$$

---

## 5. Experimental Setup

- **Benchmark Datasets**: `S-Vta1a` and `S-Vta2` (Real IO-VNBD smartphone sequences).
- **Sampling Frequency**: Nominal 10.0 Hz with actual measured sample periods $\Delta t_k \approx 0.100\text{ s}$ ($\sigma_{\Delta t} \approx 0.70\text{ ms}$).
- **Initial Conditions**: Position $\mathbf{p}_0 = [0, 0, 0]^T\text{ m}$, Velocity $\mathbf{v}_0 = [0, 0, 0]^T\text{ m/s}$.
- **Attitude Initialization**: Gravity-aligned roll/pitch, sensor azimuth aligned yaw.
- **Integration Scheme**: Classical 2nd-order Trapezoidal strapdown integration.
- **Aiding**: Strictly **NONE** (Pure classical dead reckoning).

---

## 6. Quantitative Experimental Results

The following table summarizes the measured performance metrics of the pure INS baseline evaluated against verified ground truth:

| Performance Metric | Sequence `S-Vta1a` | Sequence `S-Vta2` | Unit |
| :--- | :---: | :---: | :---: |
| **Duration** | 2,567.5 (42.79 min) | 1,099.0 (18.32 min) | seconds |
| **Logged Samples** | 25,676 | 10,991 | samples |
| **Verified Travelled Distance** | 40,546.34 (40.55 km) | 11,074.78 (11.07 km) | meters |
| **Final 2D Position Error** | **353,003.10 (353.00 km)** | **218,366.35 (218.37 km)** | meters |
| **Final 3D Position Error** | **399,763.81 (399.76 km)** | **377,278.87 (377.28 km)** | meters |
| **2D Position RMSE** | **171,169.10 (171.17 km)** | **109,424.08 (109.42 km)** | meters |
| **Mean 2D Position Error** | 125,185.12 (125.19 km) | 85,043.17 (85.04 km) | meters |
| **Maximum 2D Position Error** | 353,003.10 (353.00 km) | 218,366.35 (218.37 km) | meters |
| **Final Drift (% of Distance)** | **870.62%** | **1,971.75%** | % |
| **Mean Velocity Error** | 158.63 | 336.96 | m/s |
| **Maximum Velocity Error** | 359.58 | 461.98 | m/s |
| **Mean Heading Error** | 70.04 | 114.50 | degrees |

---

## 7. Numerical Sanity Verification

The INS outputs were verified against all required numerical integrity checks:
1. **NaN / Inf Checks**: 0 NaNs and 0 infinite values across all 33 output columns for both sequences.
2. **Timestamp Monotonicity**: Timestamps remain strictly monotonically increasing ($\Delta t > 0$).
3. **Array Dimension Consistency**: Exactly 25,676 output rows for `S-Vta1a` and 10,991 for `S-Vta2`.
4. **Origin Integrity**: Trajectories originate exactly at $(E_0, N_0, U_0) = (0.000, 0.000, 0.000)\text{ m}$.
5. **Quaternion Normalization**: Quaternion norm $\|\mathbf{q}\|$ maintained at $1.00000000$ (maximum deviation from unity $< 2.22 \times 10^{-16}$).
6. **Ground-Truth Causality**: Strict causality enforced; zero future-sample leakage, zero GNSS correction updates during state propagation.

---

## 8. Physical Interpretation of Pure INS Drift

The results demonstrate the classic, unavoidable divergence of unassisted strapdown inertial dead reckoning when executed with consumer-grade smartphone MEMS sensors:

1. **Double Integration of Acceleration Bias ($t^2$ error)**:
   A residual constant accelerometer bias $\mathbf{b}_a$ produces a position error growing quadratically:
   $$\Delta \mathbf{p}_{\text{bias}}(t) = \frac{1}{2} \mathbf{b}_a t^2$$
   Over $t = 2,567.5\text{ s}$ ($S-Vta1a$), a bias of only $0.05\text{ m/s}^2$ ($~5\text{ mg}$) generates an unassisted position error of $\approx 164\text{ km}$!
2. **Gyroscope Drift & Gravity Leakage ($t^3$ error)**:
   Any uncorrected gyroscope bias $\mathbf{b}_g$ leads to attitude tilt error $\delta \boldsymbol{\theta}(t) = \mathbf{b}_g t$. When the attitude tilts, the massive Earth gravity vector ($9.81\text{ m/s}^2$) leaks into the horizontal plane:
   $$\mathbf{a}_{\text{leakage}}^n \approx g \cdot \delta \boldsymbol{\theta}(t) = g \mathbf{b}_g t$$
   Integrating this false horizontal acceleration twice produces cubic position divergence:
   $$\Delta \mathbf{p}_{\text{gravity}}(t) = \frac{1}{6} g \mathbf{b}_g t^3$$
   Over 42.8 minutes, even a fraction of a milliradian per second of gyro drift projects kilometers of artificial velocity and hundreds of kilometers of horizontal error.
3. **Velocity Divergence**:
   Without Zero-Velocity Updates (ZUPT) or speed constraints, INS-estimated speed diverges monotonically to hundreds of meters per second ($359\text{ m/s}$ in `S-Vta1a`), far exceeding physical vehicle dynamics.
4. **Phone Mounting and Road Vibrations**:
   Engine vibration, tire-road interaction, and dashboard mount compliance induce high-frequency acceleration spikes that introduce rectification errors in uncalibrated strapdown integration.

---

## 9. Generated Artifacts and Visualizations

All generated outputs have been saved to the designated repository directories:

### Processed INS Trajectory Datasets
- `data/processed/S-Vta1a_ins.csv` (14.56 MB, 25,676 rows, 33 columns)
- `data/processed/S-Vta2_ins.csv` (6.23 MB, 10,991 rows, 33 columns)

### Diagnostic Visualizations (`outputs/phase2_plots/`)
1. **01_trajectory_comparison_S-Vta1a.png & S-Vta2.png**: Dual-panel ENU comparison showing the full unbounded INS drift and the ground-truth trajectory reference.
2. **02_position_error_vs_time_S-Vta1a.png & S-Vta2.png**: 2D and 3D position error growth curves over elapsed time.
3. **03_drift_vs_distance_S-Vta1a.png & S-Vta2.png**: Position drift and percentage error plotted against verified travelled distance.
4. **04_velocity_comparison_S-Vta1a.png & S-Vta2.png**: INS-estimated velocity components and speed divergence versus ground-truth speed.
5. **05_orientation_profiles_S-Vta1a.png & S-Vta2.png**: Roll, Pitch, and Yaw attitude propagation profiles over the full duration.

---

## 10. Baseline Limitations & Transition to Subsequent Phases

The Phase 2 baseline establishes quantitatively that **pure classical inertial dead reckoning without aiding cannot sustain vehicle navigation over multi-minute durations**. Specifically:
- Pure INS does not estimate or correct accelerometer or gyroscope biases online.
- Pure INS cannot bound gravity leakage caused by attitude drift.
- Pure INS lacks velocity observability during straight-line cruising and stops.
- Pure INS does not account for the misalignment between the smartphone sensor axes and the vehicle's longitudinal/lateral chassis axes.

These limitations define the exact technological roadmap for subsequent phases:
- **Phase 3 (Next)**: **Phone-to-Vehicle Alignment** to resolve dynamic mounting rotation matrices and decouple vehicle forward motion from phone orientation.
- **Phase 4**: **AI Speed Estimation & Motion Dynamics** to predict forward vehicle velocity directly from IMU spectrograms and vibrations.
- **Phase 5**: **Extended Kalman Filter (EKF) / Non-Holonomic Constraints (NHC)** to fuse AI speed, ZUPT, and kinematics, binding the $t^2$ and $t^3$ drift down to sub-percent operational levels.
