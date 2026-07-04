import numpy as np
import json
import os
import argparse
import math
import subprocess

def solve_hyperbolic_kepler(e, M):
    """
    Solves Kepler's equation for hyperbolic orbits:
    e * sinh(F) - F = M
    using the Newton-Raphson method.
    """
    # Initial guess: arcsinh(M / e) is a good approximation
    F = math.asinh(M / e)
    for _ in range(100):
        f_val = e * math.sinh(F) - F - M
        df_val = e * math.cosh(F) - 1.0
        dF = f_val / df_val
        F -= dF
        if abs(dF) < 1e-12:
            break
    return F

def run_simulation(years=5000.0, dt=0.5, rogue_mass=1.0, closest_approach=1000.0, rogue_speed=30.0, rogue_planets=False):
    """
    Runs the n-body solar system + rogue star simulation.
    
    Parameters:
    - years: float, duration of the simulation in Earth years.
    - dt: float, time step size in days.
    - rogue_mass: float, mass of the rogue star in Solar Masses.
    - closest_approach: float, closest approach distance in AU.
    - rogue_speed: float, speed at infinity in km/s.
    - rogue_planets: bool, whether the rogue star carries its own planets.
    """
    src_dir = os.path.dirname(__file__)
    init_path = os.path.join(src_dir, "..", "data", "initial_conditions.json")
    
    if not os.path.exists(init_path):
        raise FileNotFoundError(f"❌ Initial conditions file not found at {init_path}. Please run fetch_data.py first.")
        
    with open(init_path, "r") as f:
        init_data = json.load(f)
        
    bodies = init_data["bodies"]
    names = [b["name"] for b in bodies]
    gms = [b["gm_au3_day2"] for b in bodies]
    pos = [b["position"] for b in bodies]
    vel = [b["velocity"] for b in bodies]
    
    gm_sun = gms[names.index("Sun")]
    
    # ----------------------------------------------------
    # Initialize the Rogue Star Trajectory
    # ----------------------------------------------------
    # Conversion constant: 1 km/s in AU/day
    KM_S_TO_AU_DAY = 86400.0 / 149597870.7
    v_inf = rogue_speed * KM_S_TO_AU_DAY
    
    # Mass conversion (Sun GM is 1.0 Solar Mass)
    gm_rogue = rogue_mass * gm_sun
    
    # Total mass of the Sun + Rogue Star (neglect planets for relative trajectory setup)
    gm_total = gm_sun + gm_rogue
    
    # Semi-major axis for hyperbolic orbit: a = GM / v_inf^2
    a_semi = gm_total / (v_inf ** 2)
    
    # Eccentricity: e = 1 + d_min / a
    e_ecc = 1.0 + (closest_approach / a_semi)
    
    # Mean motion: n = sqrt(GM / a^3)
    n_motion = math.sqrt(gm_total / (a_semi ** 3))
    
    # Midpoint of the simulation (closest approach time in days)
    total_days = years * 365.25
    t_mid = total_days / 2.0
    
    # Time diff relative to periapsis at t=0
    t_diff = -t_mid
    
    # Solve Kepler's equation for hyperbolic anomaly F at t=0
    M_hyp = n_motion * t_diff
    F_anomaly = solve_hyperbolic_kepler(e_ecc, M_hyp)
    
    # Relative coordinates relative to Sun (focus of hyperbola)
    # At periapsis (F=0), y_rel = closest_approach, x_rel = 0.
    # Motion is from negative x to positive x.
    coshF = math.cosh(F_anomaly)
    sinhF = math.sinh(F_anomaly)
    sq_e2_minus_1 = math.sqrt(e_ecc ** 2 - 1.0)
    
    pos_rel = np.array([
        a_semi * sq_e2_minus_1 * sinhF,
        a_semi * (e_ecc - coshF),
        0.0
    ])
    
    denom = e_ecc * coshF - 1.0
    vel_rel = np.array([
        a_semi * sq_e2_minus_1 * n_motion * coshF / denom,
        -a_semi * n_motion * sinhF / denom,
        0.0
    ])
    
    # Place rogue star relative to Sun
    sun_idx = names.index("Sun")
    pos_rogue = np.array(pos[sun_idx]) + pos_rel
    vel_rogue = np.array(vel[sun_idx]) + vel_rel
    
    # Append Rogue Star to N-body system
    names.append("RogueStar")
    gms.append(gm_rogue)
    pos.append(pos_rogue.tolist())
    vel.append(vel_rogue.tolist())
    
    # Optionally append Rogue Planets orbiting the Rogue Star
    if rogue_planets:
        # Match masses from Jupiter and Saturn in initial_conditions
        gm_jup = [b["gm_au3_day2"] for b in bodies if b["name"] == "Jupiter"][0]
        gm_sat = [b["gm_au3_day2"] for b in bodies if b["name"] == "Saturn"][0]
        
        # Rogue Jupiter: r = 5.204 AU (Jupiter's mean distance), circular velocity
        r_rj = 5.204
        v_rj = math.sqrt(gm_rogue / r_rj)
        pos_rj = np.array([r_rj, 0.0, 0.0])
        vel_rj = np.array([0.0, v_rj, 0.0])
        
        # Rogue Saturn: r = 9.582 AU (Saturn's mean distance), circular velocity (inclined/orthogonal offset)
        r_rs = 9.582
        v_rs = math.sqrt(gm_rogue / r_rs)
        pos_rs = np.array([0.0, r_rs, 0.0])
        vel_rs = np.array([-v_rs, 0.0, 0.0])
        
        # Add to system
        names.append("RogueJupiter")
        gms.append(gm_jup)
        pos.append((pos_rogue + pos_rj).tolist())
        vel.append((vel_rogue + vel_rj).tolist())
        
        names.append("RogueSaturn")
        gms.append(gm_sat)
        pos.append((pos_rogue + pos_rs).tolist())
        vel.append((vel_rogue + vel_rs).tolist())
    
    num_bodies = len(names)
    gms_arr = np.array(gms)
    pos_arr = np.array(pos)
    vel_arr = np.array(vel)
    
    # ----------------------------------------------------
    # Barycentric (Center of Mass) Correction
    # ----------------------------------------------------
    pos_cm = np.sum(gms_arr[:, np.newaxis] * pos_arr, axis=0) / np.sum(gms_arr)
    vel_cm = np.sum(gms_arr[:, np.newaxis] * vel_arr, axis=0) / np.sum(gms_arr)
    
    pos_arr -= pos_cm
    vel_arr -= vel_cm
    
    # Simulation settings
    num_steps = int(np.ceil(total_days / dt))
    
    # Adaptive downsampling to keep dataset sizes constant (~365,000 saved states max)
    max_saved_states = 365250
    save_every = max(1, int(num_steps / max_saved_states))
    num_saved_steps = int(np.ceil(num_steps / save_every)) + 1
    
    print(f"🌍 Starting N-body Gravitational Orbit Simulation (with Rogue Star)")
    print(f"  Rogue Star Mass:   {rogue_mass:.2f} M_sun (GM: {gm_rogue:.4e} AU^3/day^2)")
    print(f"  Closest Approach:  {closest_approach:.2f} AU")
    print(f"  Speed at Infinity: {rogue_speed:.2f} km/s (v_inf: {v_inf:.4e} AU/day)")
    print(f"  Simulation Range:  {years:.2f} Earth years ({total_days:.2f} days)")
    print(f"  Step Size (dt):    {dt:.4f} days")
    print(f"  Total Steps:       {num_steps:,}")
    print(f"  Save Every:        {save_every} step(s)")
    print(f"  Saved States:      {num_saved_steps:,}")
    print(f"  Bodies Simulating: {', '.join(names)}")
    print(f"  Frame:             Mutual Barycenter (Inertial)")
    
    # Compile C integrator for maximum speed
    c_integrator_src = os.path.join(src_dir, "integrator.c")
    c_integrator_bin = os.path.join(src_dir, "integrator")
    compiled = False
    
    if os.path.exists(c_integrator_src):
        if not os.path.exists(c_integrator_bin) or os.path.getmtime(c_integrator_src) > os.path.getmtime(c_integrator_bin):
            print("🛠️ Compiling high-performance C integrator...")
            try:
                subprocess.run(["clang", "-O3", c_integrator_src, "-o", c_integrator_bin], check=True)
                compiled = True
            except Exception as e:
                print(f"⚠️ Compilation failed: {e}. Falling back to Python solver.")
        else:
            compiled = True
            
    data_dir = os.path.join(src_dir, "..", "data")
    use_c = False
    crossings_idx = np.array([], dtype=np.int32)
    crossings_t = np.array([], dtype=np.float64)
    
    if compiled and os.path.exists(c_integrator_bin):
        try:
            print("🚀 Executing high-performance C integrator...")
            input_bin = os.path.join(data_dir, "temp_input.bin")
            output_bin = os.path.join(data_dir, "temp_output.bin")
            periods_bin = os.path.join(data_dir, "temp_periods.bin")
            
            # Write input binary
            with open(input_bin, "wb") as f:
                f.write(gms_arr.tobytes())
                f.write(pos_arr.tobytes())
                f.write(vel_arr.tobytes())
                
            # Run C program
            cmd = [
                c_integrator_bin,
                str(num_bodies),
                str(years),
                str(dt),
                str(save_every),
                input_bin,
                output_bin,
                periods_bin
            ]
            subprocess.run(cmd, check=True)
            
            # Read output binary
            step_size_doubles = 1 + num_bodies * 3 + num_bodies * 3
            data = np.fromfile(output_bin, dtype=np.float64)
            data = data.reshape(-1, step_size_doubles)
            
            saved_t = data[:, 0]
            saved_r = data[:, 1 : 1 + num_bodies * 3].reshape(-1, num_bodies, 3)
            saved_v = data[:, 1 + num_bodies * 3 :].reshape(-1, num_bodies, 3)
            
            # Read crossings data
            if os.path.exists(periods_bin):
                crossings_data = np.fromfile(periods_bin, dtype=[('idx', 'i4'), ('t', 'f8')])
                crossings_idx = crossings_data['idx']
                crossings_t = crossings_data['t']
                
            # Clean up temp files
            if os.path.exists(input_bin): os.remove(input_bin)
            if os.path.exists(output_bin): os.remove(output_bin)
            if os.path.exists(periods_bin): os.remove(periods_bin)
            use_c = True
        except Exception as e:
            print(f"⚠️ C integration failed: {e}. Falling back to Python solver.")
            
    if not use_c:
        # Fallback Python N-body loop
        print("🚀 Executing Python integrator (slower)...")
        # Define compute_accelerations locally for speed
        def compute_acc(positions, gm_values):
            n = positions.shape[0]
            accelerations = np.zeros_like(positions)
            for i in range(n):
                diffs = positions - positions[i]
                dists = np.linalg.norm(diffs, axis=1)
                dists[i] = 1.0
                inv_dists3 = 1.0 / (dists ** 3)
                inv_dists3[i] = 0.0
                accelerations[i] = np.sum(diffs * (gm_values[:, np.newaxis] * inv_dists3[:, np.newaxis]), axis=0)
            return accelerations

        # Pre-allocate output arrays
        saved_t = np.zeros(num_saved_steps)
        saved_r = np.zeros((num_saved_steps, num_bodies, 3))
        saved_v = np.zeros((num_saved_steps, num_bodies, 3))
        
        # Save initial state
        saved_t[0] = 0.0
        saved_r[0] = pos_arr
        saved_v[0] = vel_arr
        
        # Track crossings in Python
        crossings_list = []
        prev_y = pos_arr[:, 1] - pos_arr[0, 1]
        
        acc = compute_acc(pos_arr, gms_arr)
        
        save_idx = 1
        for step in range(1, num_steps + 1):
            vel_half = vel_arr + 0.5 * acc * dt
            pos_arr = pos_arr + vel_half * dt
            acc = compute_acc(pos_arr, gms_arr)
            vel_arr = vel_half + 0.5 * acc * dt
            
            # Check crossings relative to Sun
            for i in range(1, num_bodies):
                curr_y = pos_arr[i, 1] - pos_arr[0, 1]
                if prev_y[i] < 0.0 and curr_y >= 0.0:
                    frac = -prev_y[i] / (curr_y - prev_y[i])
                    t_cross = (step - 1) * dt + frac * dt
                    crossings_list.append((i, t_cross))
                prev_y[i] = curr_y
                
            if step % save_every == 0 or step == num_steps:
                current_time = step * dt
                if save_idx < num_saved_steps:
                    saved_t[save_idx] = current_time
                    saved_r[save_idx] = pos_arr.copy()
                    saved_v[save_idx] = vel_arr.copy()
                    save_idx += 1
                    
                if step % (num_steps // 10 or 1) == 0 or step == num_steps:
                    pct = (step / num_steps) * 100
                    print(f"  Progress: {pct:.1f}% ({step:,} / {num_steps:,} steps)...")
                    
        saved_t = saved_t[:save_idx]
        saved_r = saved_r[:save_idx]
        saved_v = saved_v[:save_idx]
        
        if len(crossings_list) > 0:
            crossings_idx = np.array([c[0] for c in crossings_list], dtype=np.int32)
            crossings_t = np.array([c[1] for c in crossings_list], dtype=np.float64)
            
    # Save results to compressed numpy file
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, "simulation_results.npz")
    
    np.savez_compressed(
        output_path,
        t=saved_t,
        r=saved_r,
        v=saved_v,
        names=names,
        gms=gms_arr,
        years=years,
        crossings_idx=crossings_idx,
        crossings_t=crossings_t,
        rogue_mass=rogue_mass,
        closest_approach=closest_approach,
        rogue_speed=rogue_speed,
        rogue_planets=1 if rogue_planets else 0
    )
    
    print(f"🎉 Simulation completed successfully!")
    print(f"💾 Results saved to: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperbolic Rogue Star solar system perturber N-body simulator")
    parser.add_argument("--years", type=float, default=5000.0, help="Simulation duration in Earth years (default: 5000)")
    parser.add_argument("--dt", type=float, default=0.5, help="Time step in days (default: 0.5)")
    parser.add_argument("--mass", type=float, default=1.0, help="Rogue star mass in solar masses (default: 1.0)")
    parser.add_argument("--closest_approach", type=float, default=1000.0, help="Closest approach distance in AU (default: 1000.0)")
    parser.add_argument("--speed", type=float, default=30.0, help="Rogue star velocity at infinity in km/s (default: 30.0)")
    parser.add_argument("--rogue_planets", action="store_true", help="Give the rogue star two planets (default: False)")
    args = parser.parse_args()
    
    run_simulation(
        years=args.years,
        dt=args.dt,
        rogue_mass=args.mass,
        closest_approach=args.closest_approach,
        rogue_speed=args.speed,
        rogue_planets=args.rogue_planets
    )
