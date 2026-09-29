# IDR-NAV — Intelligent Dead-Reckoning Navigation

> **Smartphone-based vehicle localization for GNSS-denied environments.**  
> Combining IMU sensing, classical strapdown inertial navigation, phone-to-vehicle attitude leveling, AI-assisted speed estimation, multi-sensor fusion (EKF/UKF), and offline map-matching.

---

## 📌 Project Overview & Current Status

The IDR-NAV backend is currently frozen following the rigorous implementation and validation of **Phases 1 through 3** against real-world automotive sequences from the **IO-VNBD** (Input-Output Vehicle Navigation Benchmark Dataset, Coventry University):

- ✅ **Phase 1 — IO-VNBD Data Ingestion & Preprocessing Pipeline**
  - Robust sensor stream ingestion, timestamp validation, monotonic sorting, and duplicate pruning.
  - WGS84 Geodetic $\to$ local Cartesian East-North-Up (ENU) coordinate conversion with vehicle-origin anchoring.
  - Dynamic local gravity estimation and compensation.
  - Full automated validation: 5/5 unit tests passed.

- ✅ **Phase 2 — Classical Strapdown INS Baseline**
  - Quaternion-based angular rate integration for 3D body attitude propagation.
  - Global frame acceleration transformation ($\mathbf{a}^n = \mathbf{q} \otimes \mathbf{a}^b \otimes \mathbf{q}^* - \mathbf{g}^n$).
  - Trapezoidal integration for velocity and 3D position state propagation.
  - Quantified raw MEMS drift rate without external aiding: 12/12 unit tests passed.

- ✅ **Phase 3 — Phone-to-Vehicle Roll/Pitch Alignment**
  - Smartphone-to-vehicle coordinate frame leveling using static/low-acceleration gravity vector estimation.
  - Rodrigues minimal-rotation formulation yielding rotation matrix $\mathbf{R}_{p2v}$ with numerical orthogonality error $\approx 10^{-16}$ and $\det(\mathbf{R}) = 1.000000$.
  - Transformed acceleration and angular velocity into vehicle Forward-Lateral-Up (FLU) frame.
  - Full automated validation: 21/21 unit tests passed.
  - *Limitation*: Roll and pitch leveling achieved; full yaw observability is not claimed without vehicle dynamics / AI heading aiding.

- 🔵 **Phases 4–14 — Planned Architecture**
  - Phase 4: AI Speed Estimation (Spectrogram CNN/LSTM forward speed prediction directly from smartphone vibrations)
  - Phase 5: Motion State & Vibration Classification
  - Phase 6: Deep Inertial Odometry & Learned IMU Bias Correction
  - Phase 7: Error-State Extended Kalman Filter (ES-EKF) / UKF Fusion
  - Phase 8: Non-Holonomic Constraints (NHC: $v_y^v \approx 0, v_z^v \approx 0$) & Zero Velocity Updates (ZUPT)
  - Phase 9: GNSS Outage Seamless Handoff & In-Tunnel Navigation
  - Phase 10: OpenStreetMap (OSM) Offline Network Map-Matching
  - Phase 11: Real-time C++ Edge Engine & Android SDK

---

## 📊 Benchmark Findings (Real IO-VNBD Data)

Evaluated across two real automotive runs representing distinct driving behaviors:
1. **`S-Vta1a`** (Driver E / Aggressive, 42.79 min, 40.55 km, 25,676 samples @ 10 Hz)
2. **`S-Vta2`** (Independent Validation / Suburban-Urban, 18.32 min, 11.07 km, 10,991 samples @ 10 Hz)

| Metric | `S-Vta1a` (Ground Truth) | `S-Vta1a` (Phase 2 INS) | `S-Vta1a` (Phase 3 Aligned) | `S-Vta2` (Ground Truth) | `S-Vta2` (Phase 2 INS) | `S-Vta2` (Phase 3 Aligned) |
|---|---|---|---|---|---|---|
| **Duration** | 42.79 min | 42.79 min | 42.79 min | 18.32 min | 18.32 min | 18.32 min |
| **Distance** | 40.55 km | — | — | 11.07 km | — | — |
| **Peak Speed** | 103.61 km/h | — | — | 81.29 km/h | — | — |
| **Mean Speed** | 56.46 km/h | — | — | 36.04 km/h | — | — |
| **Final 2D Position Error** | — | **353.00 km** | **352.36 km** | — | **218.37 km** | **247.37 km** |
| **Horizontal RMSE** | — | **171.17 km** | **170.91 km** | — | **109.41 km** | **122.84 km** |
| **Drift Ratio (% of Distance)** | — | **870.6 %** | **869.0 %** | — | **1971.8 %** | **2233.6 %** |
| **Leveling Angles** | — | — | Roll: -0.05°, Pitch: +0.25° | — | — | Roll: -12.67°, Pitch: +6.86° |

### Key Scientific Insight
> **Coordinate leveling alone does not prevent inertial divergence.**  
> While Phase 3 accurately levels the gravity vector to machine precision ($\det \mathbf{R} = 1.000000$), uncompensated MEMS accelerometer bias ($\sim 0.05\text{ m/s}^2$) becomes redistributed into the horizontal plane. Without a velocity aiding source (AI Speed or Non-Holonomic Constraints), double-integration yields classic $t^2$ quadratic error growth. This quantitatively validates why AI speed estimation and multi-sensor fusion (Phases 4–8) are necessary.

---

## 🖥️ Interactive Engineering Dashboard

A presentation-ready, zero-build-step engineering dashboard is provided in `/dashboard`:
- **Overview & Hero Section**: Dynamic scalar metrics ribbon binding real values for both sequences.
- **Trajectory Visualizer**: High-DPI canvas overlaying Ground Truth, Phase 2, and Phase 3 ENU tracks with dual scaling modes (`Full Divergence` vs `Zoom to Ground Truth`).
- **Drift Analysis**: Quantitative error-growth curves and side-by-side performance breakdown.
- **GNSS Outage Simulation**: Visual demonstration of seamless GNSS loss and recovery handoff to dead reckoning.
- **Dataset Switcher**: Instantly switch between `S-Vta1a` and `S-Vta2`.

### Running the Dashboard Locally

```bash
# Option 1: Serve locally via Python
python -m http.server 8080 --directory dashboard
# Open in browser: http://localhost:8080

# Option 2: Open directly (zero build required, fully offline)
# Double-click dashboard/index.html
```

---

## 🛠️ Repository Structure

```text
├── dashboard/                     # Presentation-ready engineering dashboard
│   ├── index.html                 # Single scrolling page markup
│   ├── styles.css                 # Automotive / editorial styling system
│   ├── app.js                     # High-DPI canvas renderers & reactive data binding
│   └── data/                      # Pre-generated benchmark data (dashboard_data.js / .json)
├── data/
│   ├── raw/                       # Raw IO-VNBD dataset CSV files (S-Vta1a, S-Vta2)
│   └── processed/                 # Preprocessed, INS propagated, and Aligned CSVs
├── outputs/
│   ├── phase1_plots/              # Preprocessing & ground truth diagnostic plots
│   ├── phase2_plots/              # Classical INS trajectory & drift diagnostic plots
│   └── phase3_plots/              # Phone-to-vehicle alignment & comparative plots
├── scripts/
│   ├── export_dashboard_data.py   # Downsamples & extracts real metrics for dashboard
│   ├── run_phase1_pipeline.py     # Pipeline execution script
│   ├── run_phase2_ins.py          # Classical INS execution script
│   └── run_phase3_alignment.py    # Leveling & alignment execution script
├── src/
│   ├── pipeline/                  # Phase 1: Ingestion, ENU, filtering
│   ├── dead_reckoning/            # Phase 2: Quaternion attitude & INS propagation
│   └── alignment/                 # Phase 3: Gravity estimation & Rodrigues leveling
├── tests/                         # Automated pytest validation suite (Phase 1, 2, 3)
├── phase2_ins_report.md           # Detailed Phase 2 engineering & evaluation report
└── phase3_alignment_report.md     # Detailed Phase 3 engineering & evaluation report
```

---

## 🧪 Running Automated Tests

```bash
# Run the complete test suite across Phases 1–3
pytest -v
```
*(All 38 automated test cases pass with 100% green coverage).*
