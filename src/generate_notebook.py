import json
import os

def create_notebook():
    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.9.4"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    def add_markdown(source):
        notebook["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": source if isinstance(source, list) else [source]
        })

    def add_code(source):
        notebook["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source if isinstance(source, list) else [source]
        })

    # Cell 1: Title
    add_markdown([
        "# Rogue Star Flyby: Solar System Perturbation Analysis\n",
        "\n",
        "This notebook analyzes the physical impact of a rogue star flying past the solar system. It uses Newtonian N-body simulation results to study orbital stability and long-term deviations.\n",
        "\n",
        "## Analysis Outline\n",
        "1. **Heliocentric Distance Timeline**: Plotting the orbits of the planets and the trajectory of the rogue star relative to the Sun.\n",
        "2. **Orbital Element Shifts ($a(t)$ and $e(t)$)**: Calculating and plotting osculating Keplerian orbital parameters (semi-major axis $a$ and eccentricity $e$) of the planets over the simulation timeline to quantify permanent structural changes.\n",
        "3. **Gravitational Perturbation Ratio**: Computing the ratio of the rogue star's gravitational force vs the Sun's force on each planet.\n",
        "4. **Orbit Change Summary**: Generating a statistical table of pre- vs. post-flyby orbital characteristics."
    ])

    # Cell 2: Imports
    add_code([
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import plotly.graph_objects as go\n",
        "from plotly.subplots import make_subplots\n",
        "import os\n",
        "\n",
        "# Set styling for clean plots\n",
        "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n",
        "plt.rcParams['figure.figsize'] = (12, 6)\n",
        "plt.rcParams['font.size'] = 11"
    ])

    # Cell 3: Load Data
    add_code([
        "# Load simulation results\n",
        "data_path = os.path.join('data', 'simulation_results.npz')\n",
        "if not os.path.exists(data_path):\n",
        "    data_path = os.path.join('Projects', 'rogue-star-simulation', 'repo', 'data', 'simulation_results.npz') # fallback if run from workspace root\n",
        "\n",
        "data = np.load(data_path)\n",
        "t = data['t']          # Time in days\n",
        "r = data['r']          # Positions (steps, bodies, 3) in AU\n",
        "v = data['v']          # Velocities (steps, bodies, 3) in AU/day\n",
        "names = list(data['names'])\n",
        "gms = data['gms']      # GM values in AU^3/day^2\n",
        "years = t / 365.25\n",
        "\n",
        "# Extract rogue star metadata\n",
        "rogue_mass = float(data['rogue_mass']) if 'rogue_mass' in data else 1.0\n",
        "closest_approach = float(data['closest_approach']) if 'closest_approach' in data else 1000.0\n",
        "rogue_speed = float(data['rogue_speed']) if 'rogue_speed' in data else 30.0\n",
        "\n",
        "# Convert positions to Heliocentric (relative to the Sun)\n",
        "sun_idx = names.index('Sun')\n",
        "r_helio = r.copy()\n",
        "v_helio = v.copy()\n",
        "for i in range(len(names)):\n",
        "    r_helio[:, i, :] -= r[:, sun_idx, :]\n",
        "    v_helio[:, i, :] -= v[:, sun_idx, :]\n",
        "\n",
        "print(f\"Loaded {len(t):,} steps for {len(names)} bodies over {years[-1]:.1f} years.\")\n",
        "print(f\"Rogue Star Parameters: Mass = {rogue_mass:.1f} M☉, Closest Approach = {closest_approach:.1f} AU, Speed = {rogue_speed:.1f} km/s\")"
    ])

    # Cell 4: Heliocentric Distance Analysis Markdown
    add_markdown([
        "## 1. Heliocentric Distance Analysis\n",
        "\n",
        "We calculate the heliocentric distance $d_i(t) = \\|\\mathbf{r}_i(t) - \\mathbf{r}_{\\text{sun}}(t)\\|$ for each planet and the rogue star to view their trajectory and closest approach timeline."
    ])

    # Cell 5: Plot Heliocentric Distances
    add_code([
        "distances = {}\n",
        "for i, name in enumerate(names):\n",
        "    if name == 'Sun':\n",
        "        continue\n",
        "    distances[name] = np.linalg.norm(r_helio[:, i, :], axis=1)\n",
        "\n",
        "# Plot planets and rogue star\n",
        "fig = go.Figure()\n",
        "\n",
        "for name in distances:\n",
        "    # Using secondary axis or logarithmic scale might be useful, but let's show them on standard layout first\n",
        "    fig.add_trace(\n",
        "        go.Scatter(\n",
        "            x=years,\n",
        "            y=distances[name],\n",
        "            mode='lines',\n",
        "            name='Rogue Star' if name == 'RogueStar' else name,\n",
        "            hovertemplate=\"Time: %{{x:.1f}} yrs<br>Dist: %{{y:.2f}} AU<extra></extra>\"\n",
        "        )\n",
        "    )\n",
        "\n",
        "fig.update_layout(\n",
        "    title=\"Heliocentric Distances over Time\",\n",
        "    xaxis_title=\"Time (Earth Years)\",\n",
        "    yaxis_title=\"Distance from Sun (AU)\",\n",
        "    yaxis_type=\"log\", # Log scale useful because Rogue Star is at ~10,000 AU and planets are at 0.4-30 AU\n",
        "    template=\"plotly_dark\",\n",
        "    hovermode=\"x unified\"\n",
        ")\n",
        "fig.show()"
    ])

    # Cell 6: Orbital Elements Markdown
    add_markdown([
        "## 2. Dynamic Orbital Element Shifts ($a(t)$ and $e(t)$)\n",
        "\n",
        "Using specific energy $\\epsilon$ and angular momentum $\\mathbf{h}$ in the two-body approximation, we compute the osculating orbital elements (semi-major axis $a$ and eccentricity $e$) for each planet dynamically at every simulation step:\n",
        "\n",
        "$$\\epsilon = \\frac{1}{2} v^2 - \\frac{G(M_{\\text{sun}} + m)}{r} \\approx \\frac{1}{2} v_{\\text{helio}}^2 - \\frac{G M_{\\text{sun}}}{r_{\\text{helio}}}$$\n",
        "$$a = -\\frac{G M_{\\text{sun}}}{2 \\epsilon}$$\n",
        "$$\\mathbf{h} = \\mathbf{r}_{\\text{helio}} \\times \\mathbf{v}_{\\text{helio}}$$\n",
        "$$e = \\sqrt{1 + \\frac{2 \\epsilon h^2}{G^2 M_{\\text{sun}}^2}}$$\n",
        "\n",
        "These elements change due to gravitational perturbations. A permanent shift after the flyby represents orbital reshaping."
    ])

    # Cell 7: Compute and Plot Orbital Elements
    add_code([
        "gm_sun = gms[names.index('Sun')]\n",
        "orbital_elements = {}\n",
        "\n",
        "for i, name in enumerate(names):\n",
        "    if name in ['Sun', 'RogueStar', 'RogueJupiter', 'RogueSaturn']:\n",
        "        continue\n",
        "        \n",
        "    pos_p = r_helio[:, i, :]\n",
        "    vel_p = v_helio[:, i, :]\n",
        "    \n",
        "    # Heliocentric distance and speed squared\n",
        "    r_mag = np.linalg.norm(pos_p, axis=1)\n",
        "    v2 = np.sum(vel_p ** 2, axis=1)\n",
        "    \n",
        "    # Specific energy\n",
        "    energy = 0.5 * v2 - (gm_sun / r_mag)\n",
        "    \n",
        "    # Semi-major axis\n",
        "    a = -gm_sun / (2.0 * energy)\n",
        "    \n",
        "    # Angular momentum vector\n",
        "    h_vec = np.cross(pos_p, vel_p)\n",
        "    h2 = np.sum(h_vec ** 2, axis=1)\n",
        "    \n",
        "    # Eccentricity\n",
        "    e = np.sqrt(np.clip(1.0 + (2.0 * energy * h2) / (gm_sun ** 2), 0.0, None))\n",
        "    \n",
        "    orbital_elements[name] = {\n",
        "        'a': a,\n",
        "        'e': e\n",
        "    }\n",
        "\n",
        "# Plot a(t) and e(t) for Outer Planets (most perturbed)\n",
        "outer_planets = ['Jupiter', 'Saturn', 'Uranus', 'Neptune']\n",
        "fig = make_subplots(rows=2, cols=1, subplot_titles=(\"Semi-major Axis (a) vs Time\", \"Eccentricity (e) vs Time\"))\n",
        "\n",
        "colors_p = {'Jupiter': '#d7ccc8', 'Saturn': '#fff59d', 'Uranus': '#80deea', 'Neptune': '#9fa8da'}\n",
        "\n",
        "for name in outer_planets:\n",
        "    if name not in orbital_elements:\n",
        "        continue\n",
        "    fig.add_trace(\n",
        "        go.Scatter(\n",
        "            x=years,\n",
        "            y=orbital_elements[name]['a'],\n",
        "            mode='lines',\n",
        "            name=f\"{name} a\",\n",
        "            line=dict(color=colors_p.get(name)),\n",
        "            hovertemplate=\"%{{x:.1f}} yrs: a = %{{y:.4f}} AU<extra></extra>\"\n",
        "        ),\n",
        "        row=1, col=1\n",
        "    )\n",
        "    fig.add_trace(\n",
        "        go.Scatter(\n",
        "            x=years,\n",
        "            y=orbital_elements[name]['e'],\n",
        "            mode='lines',\n",
        "            name=f\"{name} e\",\n",
        "            line=dict(color=colors_p.get(name), dash='dash'),\n",
        "            hovertemplate=\"%{{x:.1f}} yrs: e = %{{y:.5f}}<extra></extra>\"\n",
        "        ),\n",
        "        row=2, col=1\n",
        "    )\n",
        "\n",
        "fig.update_layout(\n",
        "    height=700,\n",
        "    title=\"Outer Planet Orbital Parameters over the Flyby Timeline\",\n",
        "    template=\"plotly_dark\",\n",
        "    showlegend=True\n",
        ")\n",
        "fig.update_xaxes(title_text=\"Time (Earth Years)\", row=2, col=1)\n",
        "fig.update_yaxes(title_text=\"Semi-major Axis (AU)\", row=1, col=1)\n",
        "fig.update_yaxes(title_text=\"Eccentricity\", row=2, col=1)\n",
        "fig.show()"
    ])

    # Cell 8: Perturbation Ratio Markdown
    add_markdown([
        "## 3. Gravitational Perturbation Ratio\n",
        "\n",
        "We quantify the instant pull of the rogue star relative to the Sun on each planet:\n",
        "\n",
        "$$\\text{Perturbation Ratio}(t) = \\frac{a_{\\text{rogue}}}{a_{\\text{sun}}} = \\frac{M_{\\text{rogue}}}{M_{\\text{sun}}} \\cdot \\frac{d_{\\text{planet-sun}}^2}{d_{\\text{planet-rogue}}^2}$$\n",
        "\n",
        "Plotting this ratio over time demonstrates when the rogue star's gravitational force peaks for each planet."
    ])

    # Cell 9: Compute and Plot Perturbation Ratio
    add_code([
        "rogue_idx = names.index('RogueStar')\n",
        "gm_rogue = gms[rogue_idx]\n",
        "r_rogue = r_helio[:, rogue_idx, :]\n",
        "\n",
        "fig = go.Figure()\n",
        "\n",
        "for i, name in enumerate(names):\n",
        "    if name in ['Sun', 'RogueStar', 'RogueJupiter', 'RogueSaturn']:\n",
        "        continue\n",
        "    # Distance to Sun\n",
        "    d_sun = distances[name]\n",
        "    # Distance to Rogue Star\n",
        "    pos_p = r_helio[:, i, :]\n",
        "    d_rog = np.linalg.norm(pos_p - r_rogue, axis=1)\n",
        "    \n",
        "    # Perturbation ratio\n",
        "    ratio = (gm_rogue * (d_sun ** 2)) / (gm_sun * (d_rog ** 2))\n",
        "    \n",
        "    fig.add_trace(\n",
        "        go.Scatter(\n",
        "            x=years,\n",
        "            y=ratio,\n",
        "            mode='lines',\n",
        "            name=name,\n",
        "            hovertemplate=\"Time: %{{x:.1f}} yrs<br>Ratio: %{{y:.4e}}<extra></extra>\"\n",
        "        )\n",
        "    )\n",
        "\n",
        "fig.update_layout(\n",
        "    title=\"Rogue Star Gravitational Perturbation Ratio on Planets\",\n",
        "    xaxis_title=\"Time (Earth Years)\",\n",
        "    yaxis_title=\"Force Ratio (Rogue Star / Sun)\",\n",
        "    yaxis_type=\"log\",\n",
        "    template=\"plotly_dark\"\n",
        ")\n",
        "fig.show()"
    ])

    # Cell 10: Statistical Table
    add_code([
        "# Orbit Change Summary statistics (comparing first 10% vs last 10% of simulation)\n",
        "slice_len = int(0.1 * len(years))\n",
        "stats = []\n",
        "\n",
        "for name in orbital_elements:\n",
        "    a_arr = orbital_elements[name]['a']\n",
        "    e_arr = orbital_elements[name]['e']\n",
        "    \n",
        "    a_init = np.mean(a_arr[:slice_len])\n",
        "    a_final = np.mean(a_arr[-slice_len:])\n",
        "    delta_a = a_final - a_init\n",
        "    pct_a = (delta_a / a_init) * 100.0\n",
        "    \n",
        "    e_init = np.mean(e_arr[:slice_len])\n",
        "    e_final = np.mean(e_arr[-slice_len:])\n",
        "    delta_e = e_final - e_init\n",
        "    \n",
        "    stats.append({\n",
        "        'Planet': name,\n",
        "        'a_initial (AU)': a_init,\n",
        "        'a_final (AU)': a_final,\n",
        "        'Δa (AU)': delta_a,\n",
        "        'Δa (%)': pct_a,\n",
        "        'e_initial': e_init,\n",
        "        'e_final': e_final,\n",
        "        'Δe': delta_e\n",
        "    })\n",
        "\n",
        "df_stats = pd.DataFrame(stats)\n",
        "print(\"📊 Orbit Perturbation Summary Table (Pre- vs. Post-Flyby)\")\n",
        "display(df_stats.round(6))"
    ])

    # Save to notebook file
    src_dir = os.path.dirname(__file__)
    notebook_path = os.path.join(src_dir, "..", "analysis.ipynb")
    
    with open(notebook_path, "w") as f:
        json.dump(notebook, f, indent=2)
        
    print(f"🎉 Successfully created analysis notebook at {notebook_path}!")

if __name__ == "__main__":
    create_notebook()
