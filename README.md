# Rogue Star Solar System Orbit Perturbation Simulation

This repository contains a high-performance Newtonian N-body simulation model analyzing the gravitational impact of a rogue star flying past the solar system. 

It integrates the trajectories of the Sun, the 8 major planets, and the passing rogue star (optionally carrying its own planets) using a symplectic Velocity Verlet solver compiled in C.

## 🌟 Interactive Orbit Visualizers
You can view the interactive, animated 2D orbit visualizers directly in your browser:

* **[3 AU Flyby (Catastrophic Ejection)](https://tboats.github.io/rogue-star-simulation/data/interactive_orbits_3au.html)**
  * *Rogue star passes between Mars and Jupiter. Jupiter, Saturn, Uranus, and Neptune are completely ejected into interstellar space! Earth remains bound to the Sun, but its orbit is warped into a highly eccentric ellipse ($e \approx 0.36$), swinging from Venus's region to Mars's region.*
* **[10 AU Flyby (Saturn Ejection)](https://tboats.github.io/rogue-star-simulation/data/interactive_orbits_10au.html)**
  * *Rogue star passes at Saturn's distance. Saturn is dynamically ejected on a hyperbolic escape path. Uranus and Neptune collapse into highly elongated elliptical orbits.*
* **[50 AU Flyby (Severe Outer System Compression)](https://tboats.github.io/rogue-star-simulation/data/interactive_orbits_50au.html)**
  * *Rogue star passes beyond Neptune. Neptune's semi-major axis shrinks by 0.87 AU, and its eccentricity increases 5-fold ($e \to 0.05$).*
* **[100 AU Flyby (Deep Space Pass)](https://tboats.github.io/rogue-star-simulation/data/interactive_orbits_100au.html)**
  * *A stable flyby in deep space. The solar system remains structurally intact with only small orbital precessions.*

*(Note: [interactive_orbits.html](https://tboats.github.io/rogue-star-simulation/data/interactive_orbits.html) is currently configured with the **3 AU** scenario.)*

---

## 📐 How the Physics Works

### 1. Hyperbolic Trajectory Setup
To simulate a realistic unbound stellar flyby, the rogue star's initial position and velocity relative to the Sun are calculated using Kepler's hyperbolic equations:
$$e \sinh F - F = n (t - t_{\text{mid}})$$
This ensures the rogue star reaches its closest approach distance $d_{\text{min}}$ exactly at the midpoint ($t_{\text{mid}} = T/2$) of the simulation timeline.

### 2. Barycentric center-of-mass Correction
To prevent the entire solar system from accelerating and drifting off-screen due to the rogue star's massive gravitational pull, all body positions and velocities are shifted to the system's center-of-mass barycentric frame at $t=0$:
$$\mathbf{R}_{CM} = \frac{\sum m_i \mathbf{r}_i}{\sum m_i}, \quad \mathbf{V}_{CM} = \frac{\sum m_i \mathbf{v}_i}{\sum m_i}$$

---

## 🛠️ Running Locally

### Prerequisites
Make sure you have `numpy`, `pandas`, `plotly`, and `scipy` installed:
```bash
pip install numpy pandas plotly scipy
```

### Steps
1. **Fetch Initial Conditions** (pulls J2000 vectors from NASA Horizons):
   ```bash
   python3 src/fetch_data.py
   ```
2. **Run Simulator**:
   ```bash
   python3 src/simulator.py --closest_approach 3.0 --years 1000.0 --mass 1.0 --rogue_planets
   ```
3. **Generate Dashboard**:
   ```bash
   python3 src/create_interactive_dashboard.py
   ```
4. **Generate Analysis Notebook**:
   ```bash
   python3 src/generate_notebook.py
   ```
