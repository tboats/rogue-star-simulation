import numpy as np
import json
import os

def generate_dashboard():
    src_dir = os.path.dirname(__file__)
    data_dir = os.path.join(src_dir, "..", "data")
    npz_path = os.path.join(data_dir, "simulation_results.npz")
    
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"❌ Simulation results file not found at {npz_path}. Please run simulator.py first.")
        
    print("🌐 Loading simulation results for interactive dashboard...")
    data = np.load(npz_path)
    t = data["t"]
    r = data["r"]  # shape (steps, bodies, 3)
    names = list(data["names"])
    
    # Extract metadata if available
    rogue_mass = float(data["rogue_mass"]) if "rogue_mass" in data else 1.0
    closest_approach = float(data["closest_approach"]) if "closest_approach" in data else 1000.0
    rogue_speed = float(data["rogue_speed"]) if "rogue_speed" in data else 30.0
    
    # Downsample points for fluid browser performance and fast load times
    # Target around 50,000 steps
    target_steps = 50000
    downsample_factor = max(1, len(t) // target_steps)
    
    ds_indices = list(range(0, len(t), downsample_factor))
    if ds_indices[-1] != len(t) - 1:
        ds_indices.append(len(t) - 1)
        
    t_ds = t[ds_indices]
    r_ds = r[ds_indices]
    
    # Heliocentric conversion: subtract Sun position
    sun_idx = names.index("Sun")
    r_helio = r_ds.copy()
    for i in range(len(names)):
        r_helio[:, i, :] -= r_ds[:, sun_idx, :]
        
    # We round to 4 decimal places to compress the JSON file size significantly
    orbit_data = {}
    for i, name in enumerate(names):
        orbit_data[name] = {
            "x": np.round(r_helio[:, i, 0], 4).tolist(),
            "y": np.round(r_helio[:, i, 1], 4).tolist()
        }
        
    time_years = np.round(t_ds / 365.25, 2).tolist()
    
    # Precompute rogue star distance from the Sun over time
    rogue_idx = names.index("RogueStar")
    r_rogue_helio = r_helio[:, rogue_idx, :]
    d_rogue = np.round(np.linalg.norm(r_rogue_helio, axis=1), 2).tolist()
    
    periods = {
        "Sun": 1.0, "Mercury": 88.0, "Venus": 224.7, "Earth": 365.25, "Mars": 687.0,
        "Jupiter": 4332.6, "Saturn": 10759.2, "Uranus": 30688.5, "Neptune": 60182.0,
        "RogueStar": 999999.0, # Very long trail for the flyby star
        "RogueJupiter": 4332.6,
        "RogueSaturn": 10759.2
    }
    
    dt_ds = t_ds[1] - t_ds[0]
    trail_lengths = {}
    for name in names:
        period = periods.get(name, 365.25)
        if name == "RogueStar":
            trail_lengths[name] = len(t_ds) # Draw full path of the flyby star
        else:
            # Show 1.5 orbits for planets to ensure trails last past one full cycle
            trail_lengths[name] = int(np.ceil((period * 1.5) / dt_ds))

    # Payload to embed in HTML
    payload = {
        "names": names,
        "time_years": time_years,
        "orbit_data": orbit_data,
        "trail_lengths": trail_lengths,
        "d_rogue": d_rogue,
        "metadata": {
            "rogue_mass": rogue_mass,
            "closest_approach": closest_approach,
            "rogue_speed": rogue_speed
        }
    }
    
    payload_json = json.dumps(payload)
    
    # HTML and CSS and JS template for premium Notion-dark styled dashboard
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rogue Star Flyby - Interactive Solar System Orbit Visualizer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #030712;
            --panel-bg: rgba(9, 13, 22, 0.85);
            --border-color: rgba(48, 54, 61, 0.4);
            --text-color: #c9d1d9;
            --accent-color: #ff1744;
            --accent-glow: rgba(255, 23, 68, 0.4);
            --blue-accent: #58a6ff;
            --btn-hover: #1f6feb;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            overflow: hidden;
            display: flex;
            height: 100vh;
        }}
        
        #sidebar {{
            width: 340px;
            background-color: var(--panel-bg);
            border-right: 1px solid var(--border-color);
            padding: 24px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 20px;
            z-index: 10;
            overflow-y: auto;
            backdrop-filter: blur(8px);
        }}
        
        #canvas-container {{
            flex-grow: 1;
            position: relative;
            background-color: #010409;
            cursor: grab;
        }}
        
        #canvas-container:active {{
            cursor: grabbing;
        }}
        
        canvas#orbitCanvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
        
        h1 {{
            font-size: 22px;
            margin: 0;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ff8a00, #e52d27);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            font-size: 12px;
            color: #8b949e;
            margin-top: -12px;
            margin-bottom: 5px;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        h2 {{
            font-size: 13px;
            margin: 0;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }}
        
        .btn-row {{
            display: flex;
            gap: 8px;
        }}
        
        button {{
            flex-grow: 1;
            background-color: #161b22;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 10px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            outline: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}
        
        button:hover {{
            background-color: #21262d;
            border-color: #8b949e;
            transform: translateY(-1px);
        }}
        
        button.active {{
            background-color: var(--blue-accent);
            color: white;
            border-color: var(--blue-accent);
            box-shadow: 0 0 12px rgba(88, 166, 255, 0.3);
        }}
        
        .slider-row {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .slider-label {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #c9d1d9;
        }}
        
        .slider-label span:last-child {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--blue-accent);
        }}
        
        input[type="range"] {{
            width: 100%;
            accent-color: var(--blue-accent);
            height: 6px;
            border-radius: 3px;
            background: #21262d;
            outline: none;
            -webkit-appearance: none;
        }}
        
        input[type="range"]::-webkit-slider-runnable-track {{
            height: 6px;
        }}
        
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #58a6ff;
            cursor: pointer;
            margin-top: -4px;
            box-shadow: 0 0 6px rgba(88, 166, 255, 0.5);
        }}
        
        .checkbox-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 180px;
            overflow-y: auto;
            padding-right: 4px;
        }}
        
        .checkbox-row {{
            display: flex;
            align-items: center;
            font-size: 14px;
        }}
        
        .checkbox-row label {{
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
        }}
        
        .color-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px currentColor;
        }}
        
        #hud {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(9, 13, 22, 0.85);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px 20px;
            pointer-events: none;
            backdrop-filter: blur(8px);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .hud-value {{
            font-size: 24px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            background: linear-gradient(135deg, #58a6ff, #1f6feb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .hud-label {{
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        #instructions {{
            margin-top: auto;
            font-size: 12px;
            color: #8b949e;
            line-height: 1.5;
            border-top: 1px solid var(--border-color);
            padding-top: 12px;
        }}
        
        /* Distance chart styles */
        #distance-container {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .dist-value-row {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }}
        
        .dist-num {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            color: var(--accent-color);
        }}
        
        canvas#distanceCanvas {{
            border-radius: 8px;
            background-color: #020617;
            border: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <h1>Rogue Star Flyby</h1>
        <div class="subtitle" id="configSub">Flyby Scenario</div>
        
        <div class="control-group">
            <h2>Controls</h2>
            <div class="btn-row">
                <button id="playBtn" class="active">Pause</button>
                <button id="resetBtn">Reset</button>
            </div>
            <div class="btn-row">
                <button id="zoomInBtn">Zoom In</button>
                <button id="zoomOutBtn">Zoom Out</button>
            </div>
        </div>
        
        <div class="control-group" id="distance-container">
            <h2>Rogue Star Distance</h2>
            <div class="dist-value-row">
                <span>Distance from Sun:</span>
                <span class="dist-num"><span id="rogueDistVal">---</span> AU</span>
            </div>
            <canvas id="distanceCanvas" width="290" height="130"></canvas>
        </div>
        
        <div class="control-group">
            <div class="slider-row">
                <div class="slider-label">
                    <span>Speed</span>
                    <span id="speedVal">60.0x</span>
                </div>
                <input type="range" id="speedSlider" min="1" max="100" value="80">
            </div>
            
            <div class="slider-row">
                <div class="slider-label">
                    <span>Trail Glow</span>
                    <span id="trailAlphaVal">0.30</span>
                </div>
                <input type="range" id="trailAlphaSlider" min="0" max="1" step="0.05" value="0.30">
            </div>
        </div>
        
        <div class="control-group">
            <h2>System Bodies</h2>
            <div class="checkbox-list" id="bodiesList"></div>
        </div>
        
        <div id="instructions">
            💡 <strong>Controls Guide:</strong><br>
            • Drag canvas to pan viewport<br>
            • Scroll wheel to zoom in/out<br>
            • Click distance chart to scrub timeline
        </div>
    </div>
    
    <div id="canvas-container">
        <canvas id="orbitCanvas"></canvas>
        <div id="hud">
            <div class="hud-label">SIMULATION TIME</div>
            <div class="hud-value" id="hudTime">0.00 yrs</div>
        </div>
    </div>

    <script>
        // Embed the parsed simulation data directly
        const simData = {payload_json};
        
        const names = simData.names;
        const timeYears = simData.time_years;
        const orbitData = simData.orbit_data;
        const trailLengths = simData.trail_lengths;
        const d_rogue = simData.d_rogue;
        const meta = simData.metadata;
        
        // Display setup metadata
        document.getElementById("configSub").innerText = `M: ${{meta.rogue_mass.toFixed(1)}} M☉ | D_min: ${{meta.closest_approach.toFixed(0)}} AU | v: ${{meta.rogue_speed.toFixed(0)}} km/s`;
        
        const colors = {{
            "Sun": "#FFD700",
            "Mercury": "#a5d6a7",
            "Venus": "#ffe082",
            "Earth": "#64b5f6",
            "Mars": "#ff8a65",
            "Jupiter": "#d7ccc8",
            "Saturn": "#fff59d",
            "Uranus": "#80deea",
            "Neptune": "#9fa8da",
            "RogueStar": "#ff1744",
            "RogueJupiter": "#ff9100",
            "RogueSaturn": "#b388ff"
        }};
        
        const radii = {{
            "Sun": 10,
            "Mercury": 3.0,
            "Venus": 4.5,
            "Earth": 5.0,
            "Mars": 4.0,
            "Jupiter": 8.0,
            "Saturn": 7.0,
            "Uranus": 6.0,
            "Neptune": 6.0,
            "RogueStar": 9.0,
            "RogueJupiter": 7.0,
            "RogueSaturn": 6.0
        }};
        
        // App State
        let frame = 0;
        let frameFloat = 0.0;
        let isPlaying = true;
        let speed = 60.0; // frames per draw call (slider value 80)
        let trailAlpha = 0.3;
        
        // Dynamic zoom default: Fit planets nicely (radius ~35 AU)
        // If closest approach is smaller, zoom can adjust.
        let zoom = 14; // pixels per AU
        let panX = 0;
        let panY = 0;
        let dragStart = {{ x: 0, y: 0 }};
        let isDragging = false;
        const visibleBodies = {{}};
        
        names.forEach(name => {{
            visibleBodies[name] = true;
        }});
        
        // DOM Elements
        const canvas = document.getElementById("orbitCanvas");
        const ctx = canvas.getContext("2d");
        const distCanvas = document.getElementById("distanceCanvas");
        const distCtx = distCanvas.getContext("2d");
        const container = document.getElementById("canvas-container");
        const hudTime = document.getElementById("hudTime");
        const rogueDistVal = document.getElementById("rogueDistVal");
        
        const playBtn = document.getElementById("playBtn");
        const resetBtn = document.getElementById("resetBtn");
        const zoomInBtn = document.getElementById("zoomInBtn");
        const zoomOutBtn = document.getElementById("zoomOutBtn");
        const speedSlider = document.getElementById("speedSlider");
        const speedVal = document.getElementById("speedVal");
        const trailAlphaSlider = document.getElementById("trailAlphaSlider");
        const trailAlphaVal = document.getElementById("trailAlphaVal");
        const bodiesList = document.getElementById("bodiesList");
        
        // Initialize Sidebar Checkboxes
        names.forEach(name => {{
            const row = document.createElement("div");
            row.className = "checkbox-row";
            row.innerHTML = `
                <label>
                    <input type="checkbox" id="check-${{name}}" checked>
                    <span class="color-dot" style="color: ${{colors[name]}}; background-color: ${{colors[name]}}"></span>
                    ${{name === "RogueStar" ? "Rogue Star" : name}}
                </label>
            `;
            bodiesList.appendChild(row);
            
            document.getElementById(`check-${{name}}`).addEventListener("change", (e) => {{
                visibleBodies[name] = e.target.checked;
            }});
        }});
        
        // Canvas Resize
        function resizeCanvas() {{
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
        }}
        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();
        
        // Center pan initially
        panX = canvas.width / 2;
        panY = canvas.height / 2;
        
        // Zoom and Pan Mouse Handlers
        container.addEventListener("mousedown", (e) => {{
            isDragging = true;
            dragStart.x = e.clientX - panX;
            dragStart.y = e.clientY - panY;
        }});
        
        window.addEventListener("mouseup", () => {{
            isDragging = false;
        }});
        
        container.addEventListener("mousemove", (e) => {{
            if (isDragging) {{
                panX = e.clientX - dragStart.x;
                panY = e.clientY - dragStart.y;
            }}
        }});
        
        container.addEventListener("wheel", (e) => {{
            e.preventDefault();
            const zoomFactor = 1.1;
            const mouseX = e.clientX - container.getBoundingClientRect().left;
            const mouseY = e.clientY - container.getBoundingClientRect().top;
            
            const dx = mouseX - panX;
            const dy = mouseY - panY;
            
            if (e.deltaY < 0) {{
                zoom *= zoomFactor;
                panX = mouseX - dx * zoomFactor;
                panY = mouseY - dy * zoomFactor;
            }} else {{
                zoom /= zoomFactor;
                panX = mouseX - dx / zoomFactor;
                panY = mouseY - dy / zoomFactor;
            }}
        }});
        
        // Timeline Scrubbing on the Distance Canvas
        distCanvas.addEventListener("mousedown", scrubTimeline);
        distCanvas.addEventListener("mousemove", (e) => {{
            if (e.buttons === 1) scrubTimeline(e);
        }});
        
        function scrubTimeline(e) {{
            const rect = distCanvas.getBoundingClientRect();
            const padding = 20;
            const chartWidth = distCanvas.width - 2 * padding;
            const x = Math.max(0, Math.min(e.clientX - rect.left - padding, chartWidth));
            const pct = x / chartWidth;
            frame = Math.floor(pct * (timeYears.length - 1));
            frameFloat = frame;
        }}
        
        // Button Handlers
        playBtn.addEventListener("click", () => {{
            isPlaying = !isPlaying;
            playBtn.innerText = isPlaying ? "Pause" : "Play";
            playBtn.classList.toggle("active", isPlaying);
        }});
        
        resetBtn.addEventListener("click", () => {{
            frame = 0;
            frameFloat = 0.0;
            panX = canvas.width / 2;
            panY = canvas.height / 2;
            zoom = 14;
            hudTime.innerText = "0.00 yrs";
        }});
        
        zoomInBtn.addEventListener("click", () => {{
            zoom *= 1.3;
        }});
        
        zoomOutBtn.addEventListener("click", () => {{
            zoom /= 1.3;
        }});
        
        speedSlider.addEventListener("input", (e) => {{
            const val = parseInt(e.target.value);
            // Logarithmic mapping: 0.1x to 400x
            speed = 0.1 * Math.pow(4000, (val - 1) / 99);
            speedVal.innerText = `${{speed.toFixed(1)}}x`;
        }});
        
        trailAlphaSlider.addEventListener("input", (e) => {{
            trailAlpha = parseFloat(e.target.value);
            trailAlphaVal.innerText = trailAlpha.toFixed(2);
        }});
        
        // Distance Canvas Draw
        function drawDistanceChart() {{
            const w = distCanvas.width;
            const h = distCanvas.height;
            const padding = 20;
            const cw = w - 2 * padding;
            const ch = h - 2 * padding;
            
            distCtx.clearRect(0, 0, w, h);
            
            // Find min/max values
            let maxD = Math.max(...d_rogue);
            let minD = Math.min(...d_rogue);
            
            // Draw grid lines
            distCtx.strokeStyle = "rgba(48, 54, 61, 0.3)";
            distCtx.lineWidth = 1;
            
            // Horizontal lines
            for (let i = 0; i <= 3; i++) {{
                const y = padding + (ch / 3) * i;
                distCtx.beginPath();
                distCtx.moveTo(padding, y);
                distCtx.lineTo(w - padding, y);
                distCtx.stroke();
                
                // Labels
                const val = maxD - ((maxD - minD) / 3) * i;
                distCtx.fillStyle = "#8b949e";
                distCtx.font = "8px 'JetBrains Mono', monospace";
                distCtx.fillText(Math.round(val).toLocaleString() + " AU", padding + 5, y - 3);
            }}
            
            // Plot distance line
            distCtx.beginPath();
            distCtx.strokeStyle = "#58a6ff";
            distCtx.lineWidth = 1.5;
            
            for (let f = 0; f < d_rogue.length; f++) {{
                const x = padding + (f / (d_rogue.length - 1)) * cw;
                const y = padding + ch - ((d_rogue[f] - minD) / (maxD - minD)) * ch;
                
                if (f === 0) distCtx.moveTo(x, y);
                else distCtx.lineTo(x, y);
            }}
            distCtx.stroke();
            
            // Draw current time vertical cursor
            const cursorX = padding + (frame / (d_rogue.length - 1)) * cw;
            distCtx.beginPath();
            distCtx.strokeStyle = "#ff1744";
            distCtx.lineWidth = 1;
            distCtx.setLineDash([3, 3]);
            distCtx.moveTo(cursorX, padding);
            distCtx.lineTo(cursorX, h - padding);
            distCtx.stroke();
            distCtx.setLineDash([]); // Reset
            
            // Draw indicator dot on the curve
            const cursorY = padding + ch - ((d_rogue[frame] - minD) / (maxD - minD)) * ch;
            distCtx.beginPath();
            distCtx.arc(cursorX, cursorY, 4, 0, 2 * Math.PI);
            distCtx.fillStyle = "#ff1744";
            distCtx.shadowColor = "#ff1744";
            distCtx.shadowBlur = 6;
            distCtx.fill();
            distCtx.shadowBlur = 0; // reset
        }}
        
        // Main Canvas Orbit Loop
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw coordinate grid lines (every 20 AU)
            ctx.strokeStyle = "rgba(48, 54, 61, 0.15)";
            ctx.lineWidth = 1;
            const stepGrid = 20 * zoom;
            
            const startX = panX % stepGrid;
            for (let x = startX; x < canvas.width; x += stepGrid) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            
            const startY = panY % stepGrid;
            for (let y = startY; y < canvas.height; y += stepGrid) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
            
            const numFrames = timeYears.length;
            
            // Draw Trails
            names.forEach(name => {{
                if (!visibleBodies[name] || name === "Sun") return;
                
                const trailLen = trailLengths[name];
                const startFrame = Math.max(0, frame - trailLen);
                
                ctx.beginPath();
                ctx.strokeStyle = colors[name];
                ctx.globalAlpha = name === "RogueStar" ? trailAlpha * 1.5 : trailAlpha;
                ctx.lineWidth = name === "RogueStar" ? 1.8 : 1.2;
                
                for (let f = startFrame; f <= frame; f++) {{
                    const x = panX + orbitData[name].x[f] * zoom;
                    const y = panY + orbitData[name].y[f] * zoom;
                    if (f === startFrame) {{
                        ctx.moveTo(x, y);
                    }} else {{
                        ctx.lineTo(x, y);
                    }}
                }}
                ctx.stroke();
            }});
            
            ctx.globalAlpha = 1.0;
            
            // Draw Bodies
            names.forEach(name => {{
                if (!visibleBodies[name]) return;
                
                const x = panX + orbitData[name].x[frame] * zoom;
                const y = panY + orbitData[name].y[frame] * zoom;
                const r = radii[name] || 4;
                
                ctx.beginPath();
                ctx.arc(x, y, r, 0, 2 * Math.PI);
                ctx.fillStyle = colors[name];
                ctx.shadowColor = colors[name];
                ctx.shadowBlur = name === "Sun" ? 20 : (name === "RogueStar" ? 15 : 0);
                ctx.fill();
                ctx.shadowBlur = 0; // reset
                
                // Labels
                // Outer planets and Sun/RogueStar have labels always, inner planets only when zoomed in
                if (zoom > 5 || name === "Sun" || name === "RogueStar" || name === "Jupiter" || name === "Saturn" || name === "Neptune") {{
                    ctx.fillStyle = "#8b949e";
                    ctx.font = "500 12px 'Outfit', sans-serif";
                    ctx.fillText(name === "RogueStar" ? "Rogue Star" : name, x + r + 5, y + 4);
                }}
            }});
            
            // Update HUD text
            hudTime.innerText = `${{timeYears[frame].toFixed(2)}} yrs`;
            rogueDistVal.innerText = d_rogue[frame].toLocaleString(undefined, {{ minimumFractionDigits: 1, maximumFractionDigits: 1 }});
            
            // Draw sidebar distance chart
            drawDistanceChart();
            
            // Progress Frame
            if (isPlaying) {{
                frameFloat = (frameFloat + speed) % numFrames;
                frame = Math.floor(frameFloat) % numFrames;
            }}
            
            requestAnimationFrame(draw);
        }}
        
        requestAnimationFrame(draw);
    </script>
</body>
</html>
"""
    
    html_path = os.path.join(data_dir, "interactive_orbits.html")
    
    with open(html_path, "w") as f:
        f.write(html_content)
        
    print(f"🎉 Interactive dashboard created successfully at: {html_path}!")

if __name__ == "__main__":
    generate_dashboard()
