import requests
import json
import re
import os

def fetch_initial_conditions():
    print("🚀 Fetching J2000 initial conditions from NASA JPL Horizons...")
    url = "https://ssd.jpl.nasa.gov/api/horizons.api"

    # Define the bodies with their system GMs in km^3/s^2 (JPL DE440 constants)
    bodies_meta = [
        {"name": "Sun", "id": "10", "gm_km3_s2": 1.32712440041279419e11},
        {"name": "Mercury", "id": "1", "gm_km3_s2": 22031.868551},
        {"name": "Venus", "id": "2", "gm_km3_s2": 324858.592000},
        {"name": "Earth", "id": "3", "gm_km3_s2": 403503.235625},  # Earth + Moon barycenter GM
        {"name": "Mars", "id": "4", "gm_km3_s2": 42828.375816},
        {"name": "Jupiter", "id": "5", "gm_km3_s2": 126712764.100000},
        {"name": "Saturn", "id": "6", "gm_km3_s2": 37940584.841800},
        {"name": "Uranus", "id": "7", "gm_km3_s2": 5794556.400000},
        {"name": "Neptune", "id": "8", "gm_km3_s2": 6836527.100580}
    ]

    # Constants for units conversion
    AU_IN_KM = 149597870.7
    DAY_IN_S = 86400.0
    GM_CONVERSION = (DAY_IN_S ** 2) / (AU_IN_KM ** 3)

    results = {
        "epoch": "2000-01-01T12:00:00 TDB (J2000.0)",
        "bodies": []
    }

    for b in bodies_meta:
        print(f"  Fetching vector for {b['name']} (ID: {b['id']})...")
        params = {
            "format": "json",
            "COMMAND": b["id"],
            "OBJ_DATA": "NO",
            "MAKE_EPHEM": "YES",
            "EPHEM_TYPE": "VECTORS",
            "CENTER": "500@0", # Solar System Barycenter (inertial reference frame)
            "START_TIME": "2000-01-01T12:00:00",
            "STOP_TIME": "2000-01-01T12:01:00",
            "STEP_SIZE": "1d",
            "OUT_UNITS": "AU-D",
            "VEC_TABLE": "2"
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                print(f"❌ Error fetching {b['name']}: HTTP {response.status_code}")
                continue
            
            data = response.json()
            if "result" not in data:
                print(f"❌ Error fetching {b['name']}: No result in API response")
                continue
            
            result_text = data["result"]
            soe_part = result_text.split("$$SOE")[1].split("$$EOE")[0]
            
            # Extract coordinates using regular expressions
            x_match = re.search(r"X\s*=\s*([eE\d\+\-\.]+)\s*Y\s*=\s*([eE\d\+\-\.]+)\s*Z\s*=\s*([eE\d\+\-\.]+)", soe_part)
            v_match = re.search(r"VX\s*=\s*([eE\d\+\-\.]+)\s*VY\s*=\s*([eE\d\+\-\.]+)\s*VZ\s*=\s*([eE\d\+\-\.]+)", soe_part)
            
            if x_match and v_match:
                pos = [float(x_match.group(i)) for i in range(1, 4)]
                vel = [float(v_match.group(i)) for i in range(1, 4)]
                
                gm_au3_day2 = b["gm_km3_s2"] * GM_CONVERSION
                
                results["bodies"].append({
                    "name": b["name"],
                    "id": int(b["id"]),
                    "gm_km3_s2": b["gm_km3_s2"],
                    "gm_au3_day2": gm_au3_day2,
                    "position": pos,
                    "velocity": vel
                })
                print(f"    ✓ Pos: {pos}")
                print(f"    ✓ Vel: {vel}")
            else:
                print(f"❌ Failed to parse coordinates for {b['name']}")
                
        except Exception as e:
            print(f"❌ Exception occurred for {b['name']}: {e}")

    # Write out output file
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "initial_conditions.json")
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"🎉 Successfully saved initial conditions to {output_path}!")

if __name__ == "__main__":
    fetch_initial_conditions()
