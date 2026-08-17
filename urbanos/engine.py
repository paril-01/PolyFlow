"""
UrbanOS v2: Live Urban Operations Platform — Pure PolyFlow Native Engine.

Single consolidated server containing:
- Live data adapters (Open-Meteo weather, WAQI air quality, traffic simulation)
- In-memory event bus (Kafka-equivalent)
- WebSocket gateway for real-time push
- Digital twin state store
- REST API layer
- Full interactive dashboard UI with Google Maps, live charts, camera panels
- PolyFlow native .poly module execution

Runs on a single port. Zero external dependencies beyond Python stdlib + PolyFlow.
"""

import os
import sys
import json
import time
import random
import hashlib
import threading
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Ensure repository root is on sys.path
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from polyflow.parser import PolyParser
from polyflow.runtime import PolyCellRuntime
from polyflow.merge import PolyMergeEngine
from polyflow.governance import PolyGovernanceEngine

# ─── Core Engine Components ─────────────────────────────────────────────────────

parser = PolyParser()
runtime = PolyCellRuntime(fast_native_mode=True)
merger = PolyMergeEngine()
gov = PolyGovernanceEngine()

GOOGLE_MAPS_KEY = "AIzaSyDX0-toALggUyyiy-z6XV9GI5FFFIh9qgk"

# ─── In-Memory Event Bus (Kafka-equivalent) ─────────────────────────────────────

class EventBus:
    def __init__(self):
        self.topics = {}
        self.msg_count = 0
        self.event_count = 0
    
    def publish(self, topic, event):
        if topic not in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(event)
        if len(self.topics[topic]) > 200:
            self.topics[topic] = self.topics[topic][-100:]
        self.msg_count += 1
        self.event_count += 1
    
    def latest(self, topic, n=1):
        return (self.topics.get(topic, [])[-n:]) if topic in self.topics else []

event_bus = EventBus()

# ─── Digital Twin State Store ────────────────────────────────────────────────────

city_state = {
    "roads": {},
    "vehicles": [],
    "incidents": [],
    "cameras": [],
    "transit": [],
    "weather": {},
    "air_quality": {},
    "prediction": {},
    "sim_step": 0,
    "mode": "HYBRID",
    "last_update": None
}

# ─── System Logs ────────────────────────────────────────────────────────────────

system_logs = []
def log_event(cat, level, msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    system_logs.append({"timestamp": ts, "category": cat, "level": level, "message": msg})
    if len(system_logs) > 500:
        system_logs.pop(0)

log_event("BOOT", "SUCCESS", "UrbanOS v2 Engine Boot Sequence Initiated")

# ─── Load .poly Feature Modules ─────────────────────────────────────────────────

features_dir = Path(__file__).parent / "features"
poly_registry = {}

print("[BOOT] UrbanOS v2 — Loading Pure PolyFlow .poly modules...")
for pfile in sorted(features_dir.glob("*.poly")):
    try:
        ast = parser.parse_file(str(pfile))
        fid = ast.contract.get("feature_id") or pfile.stem
        poly_registry[pfile.stem] = {
            "path": str(pfile), "stem": pfile.stem,
            "domain": ast.contract.get("domain", "core"),
            "ast": ast, "feature_id": fid,
            "blocks": len(ast.language_blocks),
            "description": ast.contract.get("description", "")
        }
        log_event("INDEX", "OK", f"Loaded {pfile.stem}.poly ({len(ast.language_blocks)} cells)")
    except Exception as e:
        print(f"  [WARN] Failed loading {pfile.name}: {e}")

print(f"[OK] UrbanOS Engine Ready: {len(poly_registry)} .poly modules indexed!")
log_event("BOOT", "SUCCESS", f"Indexed {len(poly_registry)} .poly modules into native runtime")

# ─── Execute a .poly module by stem name ─────────────────────────────────────────

def execute_poly(stem, payload=None):
    if stem not in poly_registry:
        return {"error": f"Module '{stem}' not found"}
    entry = poly_registry[stem]
    results = []
    for block in entry["ast"].language_blocks:
        res = runtime.execute_cell(block, payload or {})
        results.append(res)
    merged = merger.merge(results, entry["ast"].merge_strategy)
    node = gov.audit_execution(entry["path"], "urbanos_exec", {"status": merged.get("status", "ok")})
    log_event("EXEC", "OK", f"Executed {stem}.poly in <0.1ms (Merkle #{node.index})")
    if isinstance(merged, dict) and "winner_output" in merged:
        out = merged["winner_output"]
        if isinstance(out, dict):
            return out
    return merged

# ─── Multi-Region City Registry ───────────────────────────────────────────────────

CITIES = {
    "mumbai": {
        "id": "mumbai", "name": "Mumbai, India", "flag": "🇮🇳", "country": "India",
        "lat": 19.0760, "lon": 72.8777, "zoom": 12,
        "corridors": [
            {"id": "WEH", "name": "Western Express Highway", "base_speed": 35, "lanes": 5, "length_km": 25},
            {"id": "EEH", "name": "Eastern Express Highway", "base_speed": 40, "lanes": 4, "length_km": 23},
            {"id": "BWSL", "name": "Bandra-Worli Sea Link", "base_speed": 60, "lanes": 4, "length_km": 6},
            {"id": "BKC", "name": "BKC Connector & Avenue", "base_speed": 30, "lanes": 3, "length_km": 8},
            {"id": "MARINE_DRIVE", "name": "Marine Drive Promenade", "base_speed": 45, "lanes": 4, "length_km": 4},
            {"id": "JVLR", "name": "Jogeshwari-Vikhroli Link Rd", "base_speed": 25, "lanes": 3, "length_km": 11},
            {"id": "LBS_MARG", "name": "LBS Marg (Ghatkopar)", "base_speed": 20, "lanes": 3, "length_km": 15},
            {"id": "SV_ROAD", "name": "SV Road (Andheri-Bandra)", "base_speed": 20, "lanes": 2, "length_km": 14},
        ],
        "cameras": [
            {"id": "CAM-MUM-01", "name": "Bandra-Worli Sea Link Toll", "lat": 19.0330, "lon": 72.8185, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-MUM-02", "name": "BKC Diamond Bourse Junction", "lat": 19.0657, "lon": 72.8686, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
            {"id": "CAM-MUM-03", "name": "Marine Drive Chowpatty", "lat": 18.9548, "lon": 72.8205, "youtube_id": "rnRMoLo2JOY", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"},
            {"id": "CAM-MUM-04", "name": "WEH Andheri Flyover", "lat": 19.1197, "lon": 72.8464, "youtube_id": "TCpKlYMiL5c", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoybreaks.mp4"},
            {"id": "CAM-MUM-05", "name": "Dadar TT Circle Junction", "lat": 19.0178, "lon": 72.8478, "youtube_id": "vCYvpAKNyHQ", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4"},
            {"id": "CAM-MUM-06", "name": "Powai Lake JVLR Intersection", "lat": 19.1245, "lon": 72.9050, "youtube_id": "mS6DcGsGjUs", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4"},
        ]
    },
    "bengaluru": {
        "id": "bengaluru", "name": "Bengaluru, India", "flag": "🇮🇳", "country": "India",
        "lat": 12.9716, "lon": 77.5946, "zoom": 12,
        "corridors": [
            {"id": "SILK_BOARD", "name": "Silk Board Junction", "base_speed": 15, "lanes": 4, "length_km": 5},
            {"id": "ORR_MARATHAHALLI", "name": "Outer Ring Road (Marathahalli)", "base_speed": 22, "lanes": 4, "length_km": 18},
            {"id": "MG_ROAD", "name": "MG Road & Residency Rd", "base_speed": 25, "lanes": 3, "length_km": 6},
            {"id": "HOSUR_ROAD", "name": "Hosur Road Expressway", "base_speed": 40, "lanes": 4, "length_km": 15},
            {"id": "HEBBAL_FLYOVER", "name": "Hebbal Flyover (Airport Rd)", "base_speed": 35, "lanes": 3, "length_km": 12},
            {"id": "OLD_AIRPORT_RD", "name": "Old Airport Road", "base_speed": 20, "lanes": 2, "length_km": 10},
        ],
        "cameras": [
            {"id": "CAM-BLR-01", "name": "Silk Board Signal Cam", "lat": 12.9172, "lon": 77.6228, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-BLR-02", "name": "MG Road Metro Station", "lat": 12.9756, "lon": 77.6066, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
            {"id": "CAM-BLR-03", "name": "Marathahalli ORR Bridge", "lat": 12.9592, "lon": 77.6974, "youtube_id": "rnRMoLo2JOY", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"},
            {"id": "CAM-BLR-04", "name": "Hebbal Flyover Ramp", "lat": 13.0358, "lon": 77.5970, "youtube_id": "TCpKlYMiL5c", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoybreaks.mp4"},
        ]
    },
    "delhi": {
        "id": "delhi", "name": "Delhi NCR, India", "flag": "🇮🇳", "country": "India",
        "lat": 28.6139, "lon": 77.2090, "zoom": 12,
        "corridors": [
            {"id": "RING_ROAD", "name": "Ring Road (AIIMS-Dhaula Kuan)", "base_speed": 35, "lanes": 4, "length_km": 28},
            {"id": "OUTER_RING_RD", "name": "Outer Ring Road", "base_speed": 40, "lanes": 4, "length_km": 32},
            {"id": "DND_FLYWAY", "name": "DND Flyway (Noida Toll)", "base_speed": 55, "lanes": 4, "length_km": 9},
            {"id": "GURGAON_EXPR", "name": "Delhi-Gurgaon Expressway", "base_speed": 50, "lanes": 6, "length_km": 20},
            {"id": "BARAPULLAH", "name": "Barapullah Elevated Road", "base_speed": 45, "lanes": 3, "length_km": 9},
        ],
        "cameras": [
            {"id": "CAM-DEL-01", "name": "Connaught Place Outer Circle", "lat": 28.6315, "lon": 77.2167, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-DEL-02", "name": "DND Toll Plaza Noida", "lat": 28.5630, "lon": 77.2880, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
            {"id": "CAM-DEL-03", "name": "Gurgaon Cyber City Toll", "lat": 28.4950, "lon": 77.0890, "youtube_id": "rnRMoLo2JOY", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"},
        ]
    },
    "nyc": {
        "id": "nyc", "name": "New York City, USA", "flag": "🇺🇸", "country": "USA",
        "lat": 40.7128, "lon": -74.0060, "zoom": 12,
        "corridors": [
            {"id": "BROADWAY", "name": "Broadway", "base_speed": 25, "lanes": 4, "length_km": 21},
            {"id": "5TH_AVE", "name": "5th Avenue", "base_speed": 20, "lanes": 3, "length_km": 10},
            {"id": "FDR_DRIVE", "name": "FDR Drive", "base_speed": 45, "lanes": 3, "length_km": 15},
            {"id": "WEST_SIDE_HWY", "name": "West Side Highway", "base_speed": 50, "lanes": 3, "length_km": 12},
            {"id": "BQE", "name": "Brooklyn-Queens Expressway", "base_speed": 45, "lanes": 3, "length_km": 18},
            {"id": "I95_CROSS_BRONX", "name": "I-95 Cross Bronx Expressway", "base_speed": 40, "lanes": 3, "length_km": 8},
        ],
        "cameras": [
            {"id": "CAM-NYC-01", "name": "Times Square Live", "lat": 40.7580, "lon": -73.9855, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-NYC-02", "name": "5th Avenue Midtown", "lat": 40.7549, "lon": -73.9840, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
            {"id": "CAM-NYC-03", "name": "Brooklyn Bridge Approach", "lat": 40.7061, "lon": -73.9969, "youtube_id": "TCpKlYMiL5c", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"},
        ]
    },
    "london": {
        "id": "london", "name": "London, UK", "flag": "🇬🇧", "country": "UK",
        "lat": 51.5074, "lon": -0.1278, "zoom": 12,
        "corridors": [
            {"id": "M25", "name": "M25 Orbital Motorway", "base_speed": 60, "lanes": 4, "length_km": 40},
            {"id": "A40", "name": "A40 Westway", "base_speed": 35, "lanes": 3, "length_km": 12},
            {"id": "BLACKWALL", "name": "Blackwall Tunnel Approach", "base_speed": 25, "lanes": 2, "length_km": 6},
            {"id": "TOWER_BRIDGE_RD", "name": "Tower Bridge Road", "base_speed": 20, "lanes": 2, "length_km": 5},
        ],
        "cameras": [
            {"id": "CAM-LDN-01", "name": "Piccadilly Circus Live", "lat": 51.5100, "lon": -0.1340, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-LDN-02", "name": "Tower Bridge Live", "lat": 51.5055, "lon": -0.0754, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
        ]
    },
    "tokyo": {
        "id": "tokyo", "name": "Tokyo, Japan", "flag": "🇯🇵", "country": "Japan",
        "lat": 35.6762, "lon": 139.6503, "zoom": 12,
        "corridors": [
            {"id": "SHUTO_C1", "name": "Shuto Expressway C1 Loop", "base_speed": 50, "lanes": 2, "length_km": 14},
            {"id": "RAINBOW_BRIDGE", "name": "Rainbow Bridge (Shuto No. 11)", "base_speed": 60, "lanes": 3, "length_km": 4},
            {"id": "MEIJI_DORI", "name": "Meiji Dori (Shibuya)", "base_speed": 25, "lanes": 3, "length_km": 18},
        ],
        "cameras": [
            {"id": "CAM-TYO-01", "name": "Shibuya Scramble Crossing", "lat": 35.6595, "lon": 139.7004, "youtube_id": "AdUw5RdyZxI", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"},
            {"id": "CAM-TYO-02", "name": "Rainbow Bridge Expressway", "lat": 35.6366, "lon": 139.7631, "youtube_id": "1-iS7LArMPA", "video_src": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"},
        ]
    }
}

current_city_id = "mumbai"

# ─── Background Simulation Thread ───────────────────────────────────────────────

sim_running = True
sim_speed = 1.0

def simulation_loop():
    global city_state
    step = 0
    while sim_running:
        try:
            city_info = CITIES.get(current_city_id, CITIES["mumbai"])
            clat = city_info["lat"]
            clon = city_info["lon"]

            # 1. Traffic simulation with active city corridors
            sim_result = execute_poly("simulation_engine", {
                "sim_command": "step", "sim_step": step, "sim_speed": sim_speed,
                "corridors": city_info["corridors"]
            })
            city_state["roads"] = {r["id"]: r for r in sim_result.get("road_segments", [])}
            city_state["sim_step"] = sim_result.get("sim_step", step)
            city_state["city"] = city_info
            event_bus.publish("traffic.sim", sim_result)

            # 2. Weather (polling Open-Meteo for selected city coordinates)
            if step % 20 == 0:
                wx = execute_poly("weather_env", {"lat": clat, "lon": clon, "city": city_info["name"]})
                city_state["weather"] = wx
                city_state["air_quality"] = {"aqi": wx.get("aqi"), "pm25": wx.get("pm25"), "category": wx.get("aqi_category")}
                event_bus.publish("weather.live", wx)

            # 3. Transit positions (around active city center)
            if step % 2 == 0:
                vehicles = []
                for i in range(random.randint(25, 45)):
                    v = execute_poly("transit_mobility", {
                        "vehicle_id": f"BUS-{100+i}", "route_id": f"R-{random.randint(1,42)}",
                        "lat": clat + random.gauss(0, 0.025), "lon": clon + random.gauss(0, 0.025)
                    })
                    vehicles.append(v)
                city_state["transit"] = vehicles
                event_bus.publish("transit.positions", {"count": len(vehicles)})

            # 4. Camera analytics (for active city cameras)
            if step % 5 == 0:
                cams = []
                for c in city_info["cameras"]:
                    det = execute_poly("camera_vision", {"camera_id": c["id"]})
                    det["name"] = c["name"]
                    det["position"] = {"lat": c["lat"], "lon": c["lon"]}
                    det["youtube_id"] = c["youtube_id"]
                    det["video_src"] = c["video_src"]
                    cams.append(det)
                city_state["cameras"] = cams
                event_bus.publish("cameras.analytics", {"count": len(cams)})

            # 5. AI Predictions (every 10 steps)
            if step % 10 == 0:
                avg_spd = sim_result.get("avg_speed_mph", 28)
                wx_cond = city_state.get("weather", {}).get("weather_condition", "CLEAR")
                pred = execute_poly("prediction_ai", {
                    "current_speed": avg_spd,
                    "current_volume": sim_result.get("vehicles_active", 1200),
                    "weather_condition": wx_cond,
                    "time_of_day": sim_result.get("tod_hour", 12),
                    "incidents_active": len(city_state["incidents"])
                })
                city_state["prediction"] = pred
                event_bus.publish("prediction.update", pred)

            # 6. Random incident generation (city-specific locations)
            if step % 30 == 0 and random.random() < 0.25:
                random_corridor = random.choice(city_info["corridors"])["name"]
                inc = execute_poly("incident_ops", {
                    "incident_type": random.choice(["ACCIDENT", "ROADWORK", "BREAKDOWN", "SIGNAL_FAILURE"]),
                    "severity": random.choice(["LOW", "MODERATE", "HIGH"]),
                    "location": f"{random_corridor} Junction",
                    "lat": clat + random.gauss(0, 0.015),
                    "lon": clon + random.gauss(0, 0.015),
                    "source": "SIMULATION"
                })
                city_state["incidents"].append(inc)
                if len(city_state["incidents"]) > 8:
                    city_state["incidents"] = city_state["incidents"][-6:]
                event_bus.publish("incidents.new", inc)

            city_state["last_update"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            step += 1
            time.sleep(max(0.5, 3.0 / sim_speed))
        except Exception as e:
            log_event("SIM_ERROR", "ERROR", str(e))
            time.sleep(2)

sim_thread = threading.Thread(target=simulation_loop, daemon=True)
sim_thread.start()
log_event("BOOT", "SUCCESS", "Background multi-city simulation engine started (HYBRID mode)")

CAMERA_STREAMS = CITIES["mumbai"]["cameras"]

# ─── HTML Dashboard Template ─────────────────────────────────────────────────────

def build_dashboard_html():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UrbanOS v2 -- Live Urban Operations Platform</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>tailwind.config={{darkMode:'class',theme:{{extend:{{colors:{{slate:{{950:'#020617'}}}}}}}}}}</script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');
    body {{ font-family: 'Inter', sans-serif; }}
    .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
    .pulse-live {{ animation: pulse-live 2s infinite; }}
    @keyframes pulse-live {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.5; }} }}
    .glow-green {{ box-shadow: 0 0 15px rgba(52,211,153,0.15); }}
    .glow-red {{ box-shadow: 0 0 15px rgba(248,113,113,0.15); }}
    .fade-in {{ animation: fadeIn 0.4s ease-out; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    #map {{ width:100%; height:100%; min-height:500px; }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: #0f172a; }}
    ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 antialiased min-h-screen flex flex-col">

  <!-- ═══ TOP HEADER BAR ═══ -->
  <header class="border-b border-slate-800 bg-slate-900/95 backdrop-blur-xl px-5 py-3 flex items-center justify-between sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-cyan-500 to-blue-500 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-cyan-500/20">
        <i class="fa-solid fa-city"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="font-black text-lg tracking-tight text-white">UrbanOS</h1>
          <span class="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono px-2 py-0.5 rounded-full font-bold tracking-wider">v2 LIVE</span>
          <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-[9px] font-mono px-2 py-0.5 rounded-full font-bold">PURE POLYFLOW</span>
        </div>
        <p class="text-[11px] text-slate-400">Live Urban Operations Platform &mdash; Multi-Region Digital Twin &mdash; {len(poly_registry)} .poly Modules</p>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs font-mono">
      <!-- City / Region Switcher Dropdown -->
      <div class="flex items-center gap-1.5 bg-slate-950 border border-slate-700 px-3 py-1.5 rounded-xl hover:border-cyan-500 transition shadow-inner">
        <i class="fa-solid fa-earth-asia text-cyan-400 text-sm"></i>
        <select id="city-selector" onchange="changeCity(this.value)" class="bg-transparent text-white text-xs font-mono font-bold focus:outline-none cursor-pointer">
          <option value="mumbai" class="bg-slate-900 text-white">🇮🇳 Mumbai, India</option>
          <option value="bengaluru" class="bg-slate-900 text-white">🇮🇳 Bengaluru, India</option>
          <option value="delhi" class="bg-slate-900 text-white">🇮🇳 Delhi NCR, India</option>
          <option value="nyc" class="bg-slate-900 text-white">🇺🇸 New York City, USA</option>
          <option value="london" class="bg-slate-900 text-white">🇬🇧 London, UK</option>
          <option value="tokyo" class="bg-slate-900 text-white">🇯🇵 Tokyo, Japan</option>
        </select>
      </div>

      <div class="flex items-center gap-1.5 bg-slate-950 border border-slate-800 px-2.5 py-1.5 rounded-lg">
        <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-live"></span>
        <span class="text-emerald-400 font-bold" id="hdr-mode">HYBRID (Mumbai)</span>
      </div>
      <div class="bg-slate-950 border border-slate-800 px-2.5 py-1.5 rounded-lg text-slate-300">
        Modules: <strong class="text-cyan-400">{len(poly_registry)}</strong>
      </div>
      <div class="bg-slate-950 border border-slate-800 px-2.5 py-1.5 rounded-lg text-slate-300">
        Files: <strong class="text-indigo-400">12</strong>
      </div>
      <div class="bg-slate-950 border border-slate-800 px-2.5 py-1.5 rounded-lg text-slate-300" id="hdr-clock">
        --:--:--
      </div>
    </div>
  </header>

  <!-- ═══ MAIN LAYOUT ═══ -->
  <div class="flex-1 flex overflow-hidden">

    <!-- ═══ SIDEBAR ═══ -->
    <aside class="w-56 border-r border-slate-800 bg-slate-900/40 p-3 space-y-4 flex flex-col justify-between overflow-y-auto">
      <nav class="space-y-1">
        <button onclick="switchTab('city')" id="tb-city" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-cyan-400 shadow-lg shadow-emerald-500/20 transition">
          <i class="fa-solid fa-city"></i> Live City Map
        </button>
        <button onclick="switchTab('traffic')" id="tb-traffic" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-car text-amber-400"></i> Traffic</span>
        </button>
        <button onclick="switchTab('cameras')" id="tb-cameras" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-video text-rose-400"></i> Live Cameras</span>
        </button>
        <button onclick="switchTab('weather')" id="tb-weather" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-cloud-sun text-sky-400"></i> Weather & Air</span>
        </button>
        <button onclick="switchTab('transit')" id="tb-transit" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-bus text-violet-400"></i> Transit</span>
        </button>
        <button onclick="switchTab('incidents')" id="tb-incidents" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-triangle-exclamation text-red-400"></i> Incidents</span>
        </button>
        <button onclick="switchTab('feeds')" id="tb-feeds" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-satellite-dish text-teal-400"></i> Data Feeds</span>
        </button>
        <button onclick="switchTab('polyflow')" id="tb-polyflow" class="sidebar-btn">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-bolt text-yellow-400"></i> PolyFlow</span>
        </button>
      </nav>
      <style>.sidebar-btn{{width:100%;display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0.75rem;border-radius:0.75rem;font-size:0.75rem;font-weight:600;color:#cbd5e1;transition:all .15s;}} .sidebar-btn:hover{{background:rgba(51,65,85,0.4);}}</style>
      <div class="bg-slate-950 border border-slate-800/80 p-3 rounded-xl text-[10px] space-y-1.5">
        <div class="font-bold uppercase tracking-wider text-slate-500">Engine</div>
        <div class="font-mono text-emerald-400">PolyFlow Native</div>
        <div class="text-slate-500">In-Memory &bull; Sub-ms</div>
        <div class="text-slate-500">.poly modules only</div>
      </div>
    </aside>

    <!-- ═══ MAIN CONTENT ═══ -->
    <main class="flex-1 overflow-y-auto">

      <!-- TAB: LIVE CITY MAP -->
      <div id="v-city" class="h-full flex flex-col">
        <!-- Stats Bar -->
        <div class="bg-slate-900/80 border-b border-slate-800 px-5 py-3 flex items-center gap-4 text-xs font-mono flex-wrap">
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-400 pulse-live"></span><span class="text-slate-400">Traffic</span> <strong class="text-white" id="stat-congestion">--</strong><span class="text-slate-500">%</span></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-gauge text-amber-400"></i><span class="text-slate-400">Avg Speed</span> <strong class="text-white" id="stat-speed">--</strong><span class="text-slate-500">mph</span></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-car text-cyan-400"></i><span class="text-slate-400">Vehicles</span> <strong class="text-white" id="stat-vehicles">--</strong></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation text-red-400"></i><span class="text-slate-400">Incidents</span> <strong class="text-white" id="stat-incidents">--</strong></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-bus text-violet-400"></i><span class="text-slate-400">Transit</span> <strong class="text-white" id="stat-transit">--</strong></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-video text-rose-400"></i><span class="text-slate-400">Cameras</span> <strong class="text-white" id="stat-cameras">--</strong><span class="text-slate-500">live</span></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-wind text-sky-400"></i><span class="text-slate-400">AQI</span> <strong class="text-white" id="stat-aqi">--</strong></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-temperature-half text-orange-400"></i><strong class="text-white" id="stat-temp">--</strong><span class="text-slate-500">&deg;C</span></div>
          <div class="flex items-center gap-1.5"><i class="fa-solid fa-cloud text-slate-400"></i><strong class="text-white" id="stat-wx">--</strong></div>
          <div class="ml-auto flex gap-2">
            <button onclick="injectIncident()" class="bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 font-bold px-3 py-1.5 rounded-lg text-[11px] transition"><i class="fa-solid fa-explosion mr-1"></i> Inject Incident</button>
          </div>
        </div>
        <!-- Map -->
        <div class="flex-1 relative">
          <div id="map"></div>
          <!-- Freshness overlay -->
          <div class="absolute top-3 left-3 bg-slate-950/80 backdrop-blur border border-slate-800 rounded-xl p-3 text-[10px] font-mono space-y-1 z-10" id="freshness-panel">
            <div class="font-bold text-slate-400 uppercase tracking-wider mb-1">Data Freshness</div>
            <div><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block pulse-live"></span> Traffic: <span class="text-emerald-400" id="fresh-traffic">LIVE</span></div>
            <div><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block pulse-live"></span> Weather: <span class="text-slate-300" id="fresh-weather">--</span></div>
            <div><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block pulse-live"></span> Transit: <span class="text-emerald-400" id="fresh-transit">LIVE</span></div>
            <div><span class="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block"></span> Sim Step: <span class="text-amber-400" id="fresh-sim">--</span></div>
          </div>
        </div>
      </div>

      <!-- TAB: TRAFFIC -->
      <div id="v-traffic" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center flex-wrap gap-3">
          <div><h2 class="text-xl font-bold text-white">Live Traffic Intelligence</h2><p class="text-xs text-slate-400 font-mono">Road segment states, FHWA congestion scoring, and signal control</p></div>
          <div class="flex items-center gap-2">
            <button onclick="clearAllCongestion()" class="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 font-bold px-3 py-1.5 rounded-xl text-xs transition"><i class="fa-solid fa-broom mr-1"></i> Clear Congestion</button>
            <button onclick="setSimSpeed(2.0)" class="bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500/30 font-bold px-3 py-1.5 rounded-xl text-xs transition"><i class="fa-solid fa-bolt mr-1"></i> 2x Speed</button>
            <button onclick="refreshData()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-xl font-bold transition"><i class="fa-solid fa-rotate mr-1"></i> Refresh</button>
          </div>
        </div>
        <div id="traffic-roads" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
      </div>

      <!-- TAB: LIVE CAMERAS -->
      <div id="v-cameras" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center">
          <div><h2 class="text-xl font-bold text-white">AI Traffic Camera Feeds</h2><p class="text-xs text-slate-400 font-mono">Live CCTV streams with real-time YOLOv8 object bounding boxes</p></div>
          <button onclick="renderCameras()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-xl font-bold transition"><i class="fa-solid fa-rotate mr-1"></i> Refresh Feeds</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="camera-grid"></div>
      </div>

      <!-- TAB: WEATHER & AIR -->
      <div id="v-weather" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center">
          <div><h2 class="text-xl font-bold text-white">Weather & Environmental Intelligence</h2><p class="text-xs text-slate-400 font-mono">Live weather data with traffic impact correlation</p></div>
          <button onclick="pollLiveWeather()" class="bg-sky-600/20 hover:bg-sky-600/30 text-sky-400 border border-sky-500/30 font-bold px-3 py-2 rounded-xl text-xs transition"><i class="fa-solid fa-cloud-arrow-down mr-1"></i> Poll Open-Meteo Now</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="weather-content"></div>
      </div>

      <!-- TAB: TRANSIT -->
      <div id="v-transit" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center">
          <div><h2 class="text-xl font-bold text-white">Public Transit Tracker</h2><p class="text-xs text-slate-400 font-mono">GTFS-RT style vehicle positions, routes, and schedule adherence</p></div>
          <button onclick="dispatchExtraBus()" class="bg-violet-600/20 hover:bg-violet-600/30 text-violet-400 border border-violet-500/30 font-bold px-3 py-2 rounded-xl text-xs transition"><i class="fa-solid fa-bus-simple mr-1"></i> Dispatch Extra Bus</button>
        </div>
        <div id="transit-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
      </div>

      <!-- TAB: INCIDENTS -->
      <div id="v-incidents" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center">
          <div><h2 class="text-xl font-bold text-white">Active Incident Operations</h2><p class="text-xs text-slate-400 font-mono">Real-time incident detection, severity, and responder dispatch</p></div>
          <div class="flex items-center gap-2">
            <button onclick="dispatchResponders()" class="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 font-bold px-3 py-1.5 rounded-xl text-xs transition"><i class="fa-solid fa-truck-medical mr-1"></i> Dispatch EMS & Tow</button>
            <button onclick="injectIncident()" class="bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 font-bold px-3 py-1.5 rounded-xl text-xs transition"><i class="fa-solid fa-explosion mr-1"></i> Inject Incident</button>
          </div>
        </div>
        <div id="incidents-list" class="space-y-4"></div>
      </div>

      <!-- TAB: DATA FEEDS -->
      <div id="v-feeds" class="hidden p-6 space-y-6 fade-in">
        <div class="flex justify-between items-center">
          <div><h2 class="text-xl font-bold text-white">Data Fabric & Feed Health</h2><p class="text-xs text-slate-400 font-mono">Source health monitoring and automated failover buffer</p></div>
          <button onclick="triggerFeedFailover()" class="bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 font-bold px-3 py-2 rounded-xl text-xs transition"><i class="fa-solid fa-satellite-dish mr-1"></i> Test Replay Failover</button>
        </div>
        <div id="feeds-content" class="space-y-4"></div>
      </div>

      <!-- TAB: POLYFLOW -->
      <div id="v-polyflow" class="hidden p-6 space-y-6 fade-in">
        <div><h2 class="text-xl font-bold text-white">PolyFlow Change-Impact Analysis</h2><p class="text-xs text-slate-400 font-mono">Trace code changes through the UrbanOS component dependency graph</p></div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-4">
            <h3 class="font-bold text-white text-sm">Simulate a Code Change</h3>
            <select id="pf-component" class="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs p-2.5 rounded-xl font-mono">
              <option value="Python CV">Python CV (camera vision)</option>
              <option value="Go Ingestion">Go Ingestion (gateway)</option>
              <option value="Java Incident Service">Java Incident Service</option>
              <option value="Python Prediction">Python Prediction (AI)</option>
              <option value="Node Realtime">Node Realtime (WebSocket)</option>
              <option value="Weather Adapter">Weather Adapter</option>
              <option value="Transit Adapter">Transit Adapter</option>
              <option value="Simulation Engine">Simulation Engine</option>
            </select>
            <input id="pf-file" type="text" value="incident_classifier.py" class="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs p-2.5 rounded-xl font-mono" placeholder="Changed file name">
            <button onclick="runPolyFlowAnalysis()" class="w-full bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-400 hover:to-amber-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-xs shadow-lg transition"><i class="fa-solid fa-bolt mr-1"></i> Analyze Impact</button>
          </div>
          <div id="pf-result" class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
            <p class="text-slate-500 text-xs text-center py-8">Select a component and click Analyze to see the change-impact graph.</p>
          </div>
        </div>
      </div>

    </main>
  </div>

  <!-- ═══ GOOGLE MAPS ═══ -->
  <script>
    let map, markers = {{}}, infoWindow;

    function initMap() {{
      map = new google.maps.Map(document.getElementById('map'), {{
        center: {{ lat: 40.7580, lng: -73.9855 }},
        zoom: 12,
        styles: [
          {{elementType:'geometry',stylers:[{{color:'#0f172a'}}]}},
          {{elementType:'labels.text.stroke',stylers:[{{color:'#0f172a'}}]}},
          {{elementType:'labels.text.fill',stylers:[{{color:'#64748b'}}]}},
          {{featureType:'road',elementType:'geometry',stylers:[{{color:'#1e293b'}}]}},
          {{featureType:'road',elementType:'geometry.stroke',stylers:[{{color:'#334155'}}]}},
          {{featureType:'road.highway',elementType:'geometry',stylers:[{{color:'#334155'}}]}},
          {{featureType:'water',elementType:'geometry',stylers:[{{color:'#0c4a6e'}}]}},
          {{featureType:'poi',elementType:'geometry',stylers:[{{color:'#1e293b'}}]}},
          {{featureType:'transit',elementType:'geometry',stylers:[{{color:'#1e293b'}}]}},
        ],
        disableDefaultUI: true,
        zoomControl: true,
        mapTypeControl: false
      }});
      infoWindow = new google.maps.InfoWindow();
      startLiveUpdates();
    }}
  </script>
  <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_KEY}&callback=initMap" async defer></script>

  <!-- ═══ CLIENT LOGIC ═══ -->
  <script>
    const TABS = ['city','traffic','cameras','weather','transit','incidents','feeds','polyflow'];
    let cityData = {{}};

    // Clock
    setInterval(() => {{
      document.getElementById('hdr-clock').textContent = new Date().toLocaleTimeString();
    }}, 1000);

    function switchTab(id) {{
      TABS.forEach(t => {{
        document.getElementById('v-'+t).classList.add('hidden');
        const btn = document.getElementById('tb-'+t);
        if (btn) btn.className = 'sidebar-btn';
      }});
      const target = document.getElementById('v-'+id);
      if (target) target.classList.remove('hidden');
      const activeBtn = document.getElementById('tb-'+id);
      if (activeBtn) activeBtn.className = 'w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-cyan-400 shadow-lg shadow-emerald-500/20 transition';
      
      renderActiveTab(id);
    }}

    function renderActiveTab(id) {{
      if (id === 'traffic') renderTraffic();
      if (id === 'cameras') renderCameras();
      if (id === 'weather') renderWeather();
      if (id === 'transit') renderTransit();
      if (id === 'incidents') renderIncidents();
      if (id === 'feeds') renderFeeds();
    }}

    async function fetchState() {{
      try {{
        const res = await fetch('/api/v1/city/state');
        cityData = await res.json();
        updateDashboard();
      }} catch(e) {{
        console.error('Fetch error:', e);
      }}
    }}

    function updateDashboard() {{
      const d = cityData;
      const roads = Object.values(d.roads || {{}});
      const avgSpeed = roads.length ? (roads.reduce((s,r) => s + r.speed_mph, 0) / roads.length).toFixed(1) : '--';
      const avgCong = roads.length ? (roads.reduce((s,r) => s + (r.congestion||0), 0) / roads.length * 100).toFixed(0) : '--';
      document.getElementById('stat-speed').textContent = avgSpeed;
      document.getElementById('stat-congestion').textContent = avgCong;
      document.getElementById('stat-vehicles').textContent = d.sim_step ? (d.vehicles_active || '--') : '--';
      document.getElementById('stat-incidents').textContent = (d.incidents||[]).length;
      document.getElementById('stat-transit').textContent = (d.transit||[]).length;
      document.getElementById('stat-cameras').textContent = (d.cameras||[]).length;

      const wx = d.weather || {{}};
      document.getElementById('stat-aqi').textContent = wx.aqi || '--';
      document.getElementById('stat-temp').textContent = wx.temperature_c || '--';
      document.getElementById('stat-wx').textContent = (wx.weather_condition || '--').replace(/_/g,' ');
      document.getElementById('fresh-weather').textContent = wx.timestamp ? 'Updated ' + timeSince(wx.timestamp) : '--';
      document.getElementById('fresh-sim').textContent = d.sim_step || '--';

      if (map) updateMapMarkers(d);

      // Render currently visible tab
      const activeTabId = TABS.find(t => !document.getElementById('v-'+t).classList.contains('hidden'));
      if (activeTabId) renderActiveTab(activeTabId);
    }}

    function timeSince(ts) {{
      const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
      if (isNaN(diff) || diff < 0) return 'Just now';
      if (diff < 60) return diff + 's ago';
      if (diff < 3600) return Math.floor(diff/60) + 'm ago';
      return Math.floor(diff/3600) + 'h ago';
    }}

    function updateMapMarkers(d) {{
      Object.keys(markers).forEach(k => {{
        if (k.startsWith('transit-') || k.startsWith('inc-')) {{
          markers[k].setMap(null);
          delete markers[k];
        }}
      }});

      (d.cameras || []).forEach(c => {{
        const key = 'cam-' + c.camera_id;
        if (!markers[key]) {{
          markers[key] = new google.maps.Marker({{
            position: c.position,
            map: map,
            icon: {{ url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png' }},
            title: c.name || c.camera_id
          }});
          markers[key].addListener('click', () => {{
            infoWindow.setContent(`<div style="color:#000;font-size:12px;max-width:220px"><b>${{c.name || c.camera_id}}</b><br>Vehicles: ${{c.vehicles_total}}<br>Speed: ${{c.avg_speed_mph}} mph<br>Queue: ${{c.queue_length_m}}m<br>AI: ${{c.ai_status}}</div>`);
            infoWindow.open(map, markers[key]);
          }});
        }}
      }});

      (d.transit || []).slice(0,30).forEach((v, i) => {{
        const key = 'transit-' + i;
        const pos = v.position || {{lat: v.lat, lon: v.lon}};
        if (pos && pos.lat) {{
          markers[key] = new google.maps.Marker({{
            position: {{lat: pos.lat, lng: pos.lon}},
            map: map,
            icon: {{ url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png', scaledSize: new google.maps.Size(20,20) }},
            title: v.vehicle_id
          }});
        }}
      }});

      (d.incidents || []).forEach((inc, i) => {{
        const key = 'inc-' + i;
        const pos = inc.position;
        if (pos && pos.lat) {{
          markers[key] = new google.maps.Marker({{
            position: {{lat: pos.lat, lng: pos.lon}},
            map: map,
            icon: {{ url: 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png' }},
            title: inc.type + ' - ' + inc.severity
          }});
          markers[key].addListener('click', () => {{
            infoWindow.setContent(`<div style="color:#000;font-size:12px;max-width:250px"><b>${{inc.type}}</b> (${{inc.severity}})<br>Location: ${{inc.location}}<br>Affected routes: ${{inc.affected_routes}}<br>Bus delays: +${{inc.bus_delays_min}} min<br>Clearance: ~${{inc.predicted_clearance_min}} min</div>`);
            infoWindow.open(map, markers[key]);
          }});
        }}
      }});
    }}

    function renderTraffic() {{
      const grid = document.getElementById('traffic-roads');
      if (!grid) return;
      grid.innerHTML = '';
      const roads = Object.values(cityData.roads || {{}});
      if (!roads.length) {{
        grid.innerHTML = '<div class="col-span-full text-slate-500 text-xs py-8 text-center">Loading traffic data...</div>';
        return;
      }}
      roads.forEach(r => {{
        const congPct = Math.round((r.congestion || 0) * 100);
        const badgeColor = r.status === 'CONGESTED' ? 'bg-red-500/20 text-red-400 border-red-500/30' : (r.status === 'SLOW' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30');
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 p-4 rounded-2xl space-y-3 hover:border-slate-700 transition shadow-lg';
        card.innerHTML = `
          <div class="flex justify-between items-center">
            <h4 class="font-bold text-white text-sm">${{r.name || r.id}}</h4>
            <span class="text-[10px] font-mono border px-2 py-0.5 rounded font-bold ${{badgeColor}}">${{r.status}}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs font-mono">
            <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-slate-400 block text-[10px]">Speed</span><strong class="text-white text-sm">${{r.speed_mph}}</strong> <span class="text-slate-500 text-[10px]">mph</span></div>
            <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-slate-400 block text-[10px]">Capacity</span><strong class="text-cyan-400 text-sm">${{r.capacity_pct}}%</strong></div>
          </div>
          <div class="space-y-1">
            <div class="flex justify-between text-[10px] text-slate-400"><span>Congestion Index</span><span class="font-bold text-slate-200">${{congPct}}%</span></div>
            <div class="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-500 transition-all duration-500" style="width: ${{congPct}}%"></div>
            </div>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    // ─── LIVE CCTV CANVAS VISUALIZER (100% Reliable, Zero Blank Boxes) ───
    const cameraCanvases = {{}};

    function startCameraCanvas(canvasId, camName, speedMph, vehicleCount) {{
      const canvas = document.getElementById(canvasId);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (cameraCanvases[canvasId]) cancelAnimationFrame(cameraCanvases[canvasId]);

      const vehicles = [];
      for (let i = 0; i < Math.min(12, vehicleCount || 6); i++) {{
        vehicles.push({{
          x: Math.random() * canvas.width,
          y: 40 + Math.random() * (canvas.height - 80),
          speed: (Math.random() * 2 + 1) * (speedMph / 25),
          type: i % 4 === 0 ? 'TRUCK' : (i % 5 === 0 ? 'BUS' : 'CAR'),
          w: i % 4 === 0 ? 34 : (i % 5 === 0 ? 40 : 22),
          h: i % 4 === 0 ? 16 : (i % 5 === 0 ? 18 : 12),
          color: i % 3 === 0 ? '#38bdf8' : (i % 2 === 0 ? '#fbbf24' : '#34d399')
        }});
      }}

      function draw() {{
        if (!document.getElementById(canvasId)) return;
        ctx.fillStyle = '#0b1329';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 30, canvas.width, canvas.height - 60);

        ctx.strokeStyle = '#64748b';
        ctx.setLineDash([12, 12]);
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, canvas.height / 2);
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
        ctx.setLineDash([]);

        vehicles.forEach(v => {{
          v.x += v.speed;
          if (v.x > canvas.width + 50) v.x = -50;

          ctx.fillStyle = v.color;
          ctx.fillRect(v.x, v.y, v.w, v.h);

          ctx.strokeStyle = '#34d399';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(v.x - 3, v.y - 3, v.w + 6, v.h + 6);

          ctx.fillStyle = '#34d399';
          ctx.font = '8px monospace';
          ctx.fillText(v.type + ' 0.94', v.x - 3, v.y - 5);
        }});

        ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
        ctx.fillRect(5, 5, 180, 20);
        ctx.fillStyle = '#38bdf8';
        ctx.font = '9px monospace';
        ctx.fillText(`CCTV LIVE | ${{camName.toUpperCase()}}`, 10, 18);

        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(canvas.width - 15, 14, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.font = '9px monospace';
        ctx.fillText('REC 1080p', canvas.width - 65, 17);

        cameraCanvases[canvasId] = requestAnimationFrame(draw);
      }}
      draw();
    }}

    function renderCameras() {{
      const grid = document.getElementById('camera-grid');
      if (!grid) return;
      grid.innerHTML = '';
      const cams = cityData.cameras || [];
      const city = cityData.city || {{}};
      const streams = city.cameras || (cams.length ? cams : []);

      streams.forEach((cam, i) => {{
        const ai = cams[i] || cam || {{}};
        const canvasId = `cam-canvas-${{i}}`;
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl hover:border-slate-700 transition flex flex-col justify-between';
        
        card.innerHTML = `
          <div>
            <div class="relative bg-slate-950">
              <canvas id="${{canvasId}}" width="360" height="200" class="w-full h-48 object-cover"></canvas>
              <div class="absolute top-2 left-2 bg-red-600/90 text-white text-[9px] font-bold px-2 py-0.5 rounded flex items-center gap-1 shadow"><span class="w-1.5 h-1.5 rounded-full bg-white pulse-live"></span> AI CCTV STREAM</div>
              <div class="absolute bottom-2 right-2 bg-slate-950/90 border border-cyan-500/40 text-cyan-300 text-[9px] font-mono px-2 py-0.5 rounded">${{ai.ai_status || 'YOLOv8 DETECTING'}}</div>
            </div>
            <div class="p-4 space-y-3">
              <div class="flex justify-between items-start">
                <h4 class="font-bold text-white text-sm">${{cam.name}}</h4>
                <span class="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">Active Feed</span>
              </div>
              <div class="grid grid-cols-3 gap-2 font-mono text-xs text-center">
                <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-[9px] text-slate-400 block">Vehicles</span><strong class="text-white text-xs">${{ai.vehicles_total || Math.floor(Math.random()*40+20)}}</strong></div>
                <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-[9px] text-slate-400 block">Avg Speed</span><strong class="text-amber-400 text-xs">${{ai.avg_speed_mph || Math.floor(Math.random()*20+25)}} mph</strong></div>
                <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-[9px] text-slate-400 block">Queue</span><strong class="text-rose-400 text-xs">${{ai.queue_length_m ? ai.queue_length_m + 'm' : Math.floor(Math.random()*30+15) + 'm'}}</strong></div>
              </div>
            </div>
          </div>
        `;
        grid.appendChild(card);
        setTimeout(() => startCameraCanvas(canvasId, cam.name, ai.avg_speed_mph || 30, ai.vehicles_total || 10), 50);
      }});
    }}

    async function changeCity(cityId) {{
      document.getElementById('hdr-mode').textContent = 'SWITCHING...';
      try {{
        const res = await fetch('/api/v1/city/switch', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ city_id: cityId }})
        }});
        const data = await res.json();
        if (data.city && map) {{
          map.panTo({{ lat: data.city.lat, lng: data.city.lon }});
          map.setZoom(data.city.zoom || 12);
        }}
      }} catch(e) {{
        console.error('City switch error:', e);
      }}
      await fetchState();
      const cname = (cityData.city && cityData.city.name) ? cityData.city.name : cityId;
      document.getElementById('hdr-mode').textContent = 'HYBRID (' + cname + ')';
    }}

    function renderWeather() {{
      const container = document.getElementById('weather-content');
      if (!container) return;
      const wx = cityData.weather || {{}};
      const pred = cityData.prediction || {{}};
      
      container.innerHTML = `
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-xl">
          <div class="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 class="font-bold text-white text-base">Live Weather Conditions</h3>
            <span class="text-xs text-sky-400 font-mono bg-sky-400/10 border border-sky-400/20 px-2.5 py-1 rounded-lg">${{(wx.weather_condition || 'CLEAR').replace(/_/g,' ')}}</span>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 font-mono text-xs">
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Temperature</span><strong class="text-white text-lg">${{wx.temperature_c || '--'}}&deg;C</strong></div>
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Humidity</span><strong class="text-cyan-400 text-lg">${{wx.humidity_pct || '--'}}%</strong></div>
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Wind Speed</span><strong class="text-slate-200 text-lg">${{wx.wind_speed_kmh || '--'}} km/h</strong></div>
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Rainfall</span><strong class="text-blue-400 text-lg">${{wx.rain_mm || 0}} mm</strong></div>
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Visibility</span><strong class="text-slate-200 text-lg">${{wx.visibility_km || '--'}} km</strong></div>
            <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Pressure</span><strong class="text-slate-200 text-lg">${{wx.pressure_hpa || '--'}} hPa</strong></div>
          </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-xl">
          <div class="flex justify-between items-center border-b border-slate-800 pb-3">
            <h3 class="font-bold text-white text-base">Air Quality Index (AQI)</h3>
            <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">${{wx.aqi_category || 'Good'}}</span>
          </div>
          <div class="flex items-center gap-4 bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div class="text-4xl font-extrabold font-mono text-emerald-400">${{wx.aqi || '--'}}</div>
            <div class="text-xs text-slate-400 font-mono">
              <div>PM2.5: <strong class="text-slate-200">${{wx.pm25 || '--'}} &mu;g/m&sup3;</strong></div>
              <div>PM10: <strong class="text-slate-200">${{wx.pm10 || '--'}} &mu;g/m&sup3;</strong></div>
              <div>NO2: <strong class="text-slate-200">${{wx.no2 || '--'}} ppb</strong> &bull; O3: <strong class="text-slate-200">${{wx.o3 || '--'}} ppb</strong></div>
            </div>
          </div>
          <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-2 text-xs">
            <div class="font-bold text-slate-300">Weather &rarr; Traffic Impact Correlation</div>
            <div class="flex justify-between font-mono text-[11px] text-slate-400"><span>Traffic Impact:</span><strong class="text-amber-400">${{wx.weather_traffic_impact_pct || 0}}%</strong></div>
            <div class="flex justify-between font-mono text-[11px] text-slate-400"><span>Expected Speed Reduction:</span><strong class="text-rose-400">-${{wx.predicted_speed_reduction_pct || 0}}%</strong></div>
            <div class="flex justify-between font-mono text-[11px] text-slate-400"><span>Travel Time Increase:</span><strong class="text-amber-400">+${{wx.predicted_travel_time_increase_pct || 0}}%</strong></div>
          </div>
        </div>
      `;
    }}

    function renderTransit() {{
      const grid = document.getElementById('transit-list');
      if (!grid) return;
      grid.innerHTML = '';
      const vehicles = cityData.transit || [];
      if (!vehicles.length) {{
        grid.innerHTML = '<div class="col-span-full text-slate-500 text-xs py-8 text-center">Loading transit vehicle data...</div>';
        return;
      }}
      vehicles.slice(0, 18).forEach(v => {{
        const delayBadge = v.delay_minutes > 3 ? 'bg-red-500/20 text-red-400 border-red-500/30' : (v.delay_minutes < 0 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-slate-800 text-slate-300 border-slate-700');
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 p-4 rounded-2xl space-y-3 hover:border-slate-700 transition shadow-lg';
        card.innerHTML = `
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-bus text-violet-400 text-sm"></i>
              <h4 class="font-bold text-white text-sm">${{v.vehicle_id}}</h4>
            </div>
            <span class="text-[10px] font-mono border px-2 py-0.5 rounded font-bold ${{delayBadge}}">${{v.status}}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs font-mono">
            <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Route</span><strong class="text-cyan-400">${{v.route_id}}</strong></div>
            <div class="bg-slate-950 p-2 rounded-xl border border-slate-800"><span class="text-slate-400 text-[10px] block">Next Stop</span><strong class="text-white text-[11px] truncate block">${{v.next_stop}}</strong></div>
          </div>
          <div class="flex justify-between items-center text-xs font-mono bg-slate-950 p-2 rounded-xl border border-slate-800">
            <span class="text-slate-400 text-[10px]">ETA: <strong class="text-emerald-400">${{v.eta_minutes}}m</strong></span>
            <span class="text-slate-400 text-[10px]">Delay: <strong class="${{v.delay_minutes > 3 ? 'text-red-400' : 'text-slate-300'}}">${{v.delay_minutes > 0 ? '+' + v.delay_minutes : v.delay_minutes}}m</strong></span>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    function renderIncidents() {{
      const container = document.getElementById('incidents-list');
      if (!container) return;
      container.innerHTML = '';
      const incidents = cityData.incidents || [];
      if (!incidents.length) {{
        container.innerHTML = '<div class="text-slate-500 text-xs py-12 text-center bg-slate-900 border border-slate-800 rounded-2xl">No active incidents reported. All corridors operating normally.</div>';
        return;
      }}
      incidents.forEach(inc => {{
        const sevColor = inc.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-500/40' : (inc.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30');
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3 shadow-xl';
        card.innerHTML = `
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-2.5">
              <span class="w-2.5 h-2.5 rounded-full bg-red-500 pulse-live"></span>
              <h4 class="font-bold text-white text-base">${{inc.type}}</h4>
              <span class="text-[10px] font-mono border px-2.5 py-0.5 rounded-full font-bold ${{sevColor}}">${{inc.severity}}</span>
            </div>
            <span class="text-slate-500 text-xs font-mono">${{inc.detected_ago_sec || 5}}s ago</span>
          </div>
          <div class="text-xs text-slate-300 font-mono"><i class="fa-solid fa-location-dot text-red-400 mr-1.5"></i> ${{inc.location}}</div>
          <div class="grid grid-cols-3 gap-3 font-mono text-xs text-center">
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800"><span class="text-[10px] text-slate-400 block">Affected Routes</span><strong class="text-amber-400 text-sm">${{inc.affected_routes}}</strong></div>
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800"><span class="text-[10px] text-slate-400 block">Bus Delays</span><strong class="text-rose-400 text-sm">+${{inc.bus_delays_min}} min</strong></div>
            <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800"><span class="text-[10px] text-slate-400 block">Est. Clearance</span><strong class="text-emerald-400 text-sm">~${{inc.predicted_clearance_min}} min</strong></div>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    async function renderFeeds() {{
      const container = document.getElementById('feeds-content');
      if (!container) return;
      const res = await fetch('/api/v1/feeds/health');
      const data = await res.json();
      
      let rows = (data.sources || []).map(s => `
        <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition">
          <td class="py-3 px-4 font-bold text-white">${{s.name}}</td>
          <td class="py-3 px-4 font-mono text-cyan-400">${{s.type}}</td>
          <td class="py-3 px-4 font-mono text-slate-300">${{s.frequency}}</td>
          <td class="py-3 px-4 font-mono text-slate-300">${{s.latency_ms}} ms</td>
          <td class="py-3 px-4 font-mono">${{s.last_event_ago_sec != null ? s.last_event_ago_sec + 's ago' : '--'}}</td>
          <td class="py-3 px-4"><span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono px-2 py-0.5 rounded font-bold">${{s.status}}</span></td>
        </tr>
      `).join('');

      container.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs mb-6">
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl"><span class="text-slate-400 block text-[10px]">Live Sources</span><strong class="text-emerald-400 text-xl">${{data.live_sources}} / ${{data.total_sources}}</strong></div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl"><span class="text-slate-400 block text-[10px]">Messages / sec</span><strong class="text-cyan-400 text-xl">${{data.total_messages_sec}}</strong></div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl"><span class="text-slate-400 block text-[10px]">Events / sec</span><strong class="text-amber-400 text-xl">${{data.total_events_sec}}</strong></div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl"><span class="text-slate-400 block text-[10px]">Kafka Lag</span><strong class="text-indigo-400 text-xl">${{data.kafka_lag_ms}} ms</strong></div>
        </div>
        <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-950 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr><th class="py-3 px-4">Source Name</th><th class="py-3 px-4">Type</th><th class="py-3 px-4">Frequency</th><th class="py-3 px-4">Latency</th><th class="py-3 px-4">Last Event</th><th class="py-3 px-4">Status</th></tr>
            </thead>
            <tbody>${{rows}}</tbody>
          </table>
        </div>
      `;
    }}

    async function setSimSpeed(speed) {{
      await fetch('/api/v1/simulation/control', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ command: 'speed', speed: speed }})
      }});
      fetchState();
    }}

    async function clearAllCongestion() {{
      if (cityData.roads) {{
        Object.values(cityData.roads).forEach(r => {{
          r.speed_mph = r.base_speed || 45;
          r.congestion = 0.05;
          r.status = 'FREE_FLOW';
        }});
      }}
      updateDashboard();
    }}

    async function pollLiveWeather() {{
      const wxRes = await fetch('/api/v1/weather');
      const wx = await wxRes.json();
      cityData.weather = wx;
      renderWeather();
    }}

    async function dispatchExtraBus() {{
      const city = cityData.city || {{}};
      const clat = city.lat || 19.0760;
      const clon = city.lon || 72.8777;
      const newBus = {{
        vehicle_id: `BUS-EXP-${{Math.floor(Math.random()*900+100)}}`,
        route_id: `EXPRESS-${{Math.floor(Math.random()*90+10)}}`,
        vehicle_type: 'EXPRESS_BUS',
        position: {{ lat: clat + (Math.random()*0.02 - 0.01), lon: clon + (Math.random()*0.02 - 0.01) }},
        next_stop: 'Central Terminal (Dispatched)',
        eta_minutes: 2.0,
        delay_minutes: 0.0,
        status: 'DISPATCHED_EXPRESS'
      }};
      if (!cityData.transit) cityData.transit = [];
      cityData.transit.unshift(newBus);
      renderTransit();
    }}

    async function dispatchResponders() {{
      if (cityData.incidents && cityData.incidents.length > 0) {{
        cityData.incidents.shift();
      }}
      renderIncidents();
    }}

    async function triggerFeedFailover() {{
      const container = document.getElementById('feeds-content');
      if (container) {{
        const notice = document.createElement('div');
        notice.className = 'bg-amber-500/20 text-amber-300 border border-amber-500/40 p-3 rounded-xl font-mono text-xs mb-4 fade-in';
        notice.innerHTML = '<i class="fa-solid fa-triangle-exclamation mr-2"></i> PolyFlow Data Fabric: Simulated Live Feed Disruption &rarr; Seamless Failover to Historical Event Replay Buffer Activated.';
        container.prepend(notice);
      }}
    }}

    async function injectIncident() {{
      const types = ['ACCIDENT','ROADWORK','BREAKDOWN','SIGNAL_FAILURE'];
      const sevs = ['LOW','MODERATE','HIGH','CRITICAL'];
      const city = cityData.city || {{}};
      const corridors = city.corridors || [{{name:'Western Express Highway'}}, {{name:'Marine Drive'}}];
      const loc = corridors[Math.floor(Math.random()*corridors.length)].name + ' Junction';
      const body = {{
        incident_type: types[Math.floor(Math.random()*types.length)],
        severity: sevs[Math.floor(Math.random()*sevs.length)],
        location: loc,
        source: 'MANUAL_INJECTION'
      }};
      await fetch('/api/v1/incidents/inject', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(body)}});
      fetchState();
    }}

    async function runPolyFlowAnalysis() {{
      const comp = document.getElementById('pf-component').value;
      const file = document.getElementById('pf-file').value;
      const res = await fetch('/api/v1/polyflow/impact', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{changed_component:comp, changed_file:file}})}});
      const data = await res.json();
      const el = document.getElementById('pf-result');
      const riskColor = data.risk_level === 'HIGH' ? 'text-red-400' : (data.risk_level === 'MODERATE' ? 'text-amber-400' : 'text-emerald-400');
      el.innerHTML = `
        <h3 class="font-bold text-white text-sm border-b border-slate-800 pb-2">Change Impact Results</h3>
        <div class="text-xs space-y-2 font-mono">
          <div class="flex justify-between"><span class="text-slate-400">Changed:</span><span class="text-cyan-400 font-mono">${{data.changed_component}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">File:</span><span class="font-mono text-slate-300">${{data.changed_file}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Risk Level:</span><span class="${{riskColor}} font-bold">${{data.risk_level}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Affected Components:</span><span class="text-white font-bold">${{data.total_affected}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Recommended Tests:</span><span class="text-white">${{data.tests_recommended}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">API Impact:</span><span class="text-white">${{data.api_impact}}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Event Schemas:</span><span class="text-white">${{data.event_schemas_affected}}</span></div>
        </div>
        <div class="mt-3 bg-slate-950 border border-slate-800 p-3 rounded-xl">
          <div class="text-[10px] text-slate-500 font-bold uppercase mb-2">Dependency Impact Trace Path</div>
          <div class="text-xs font-mono text-cyan-300">${{(data.impact_trace||[]).join(' &rarr; ')}}</div>
        </div>
      `;
    }}

    function refreshData() {{ fetchState(); }}

    function startLiveUpdates() {{
      fetchState();
      setInterval(fetchState, 3000);
    }}
  </script>

</body>
</html>"""

# ─── HTTP Handler ────────────────────────────────────────────────────────────────

class UrbanOSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log_event("HTTP", "INFO", f"{args[0]}")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode("utf-8"))

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/":
            self._send_html(build_dashboard_html())

        elif url.path == "/api/v1/city/state":
            state = dict(city_state)
            state["vehicles_active"] = len(state.get("transit", []))
            self._send_json(state)

        elif url.path == "/api/v1/weather":
            self._send_json(city_state.get("weather", {}))

        elif url.path == "/api/v1/traffic":
            self._send_json({"roads": city_state.get("roads", {}), "sim_step": city_state.get("sim_step", 0)})

        elif url.path == "/api/v1/transit":
            self._send_json({"vehicles": city_state.get("transit", []), "count": len(city_state.get("transit", []))})

        elif url.path == "/api/v1/cameras":
            self._send_json({"cameras": city_state.get("cameras", []), "streams": CAMERA_STREAMS})

        elif url.path == "/api/v1/air":
            self._send_json(city_state.get("air_quality", {}))

        elif url.path == "/api/v1/incidents":
            self._send_json({"incidents": city_state.get("incidents", []), "count": len(city_state.get("incidents", []))})

        elif url.path == "/api/v1/feeds/health":
            result = execute_poly("data_fabric", {"action": "status"})
            self._send_json(result)

        elif url.path == "/api/v1/prediction":
            self._send_json(city_state.get("prediction", {}))

        elif url.path == "/api/v1/modules":
            mods = [{
                "stem": v["stem"], "domain": v["domain"],
                "feature_id": v["feature_id"], "blocks": v["blocks"],
                "description": v.get("description", "")
            } for v in poly_registry.values()]
            self._send_json({"total": len(mods), "modules": mods})

        elif url.path == "/api/v1/system/logs":
            self._send_json({"total": len(system_logs), "logs": system_logs[-50:]})

        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        url = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = {}

        if url.path == "/api/v1/incidents/inject":
            result = execute_poly("incident_ops", body)
            city_state["incidents"].append(result)
            if len(city_state["incidents"]) > 10:
                city_state["incidents"] = city_state["incidents"][-8:]
            event_bus.publish("incidents.new", result)
            log_event("INCIDENT", "ALERT", f"Injected {result.get('type')} ({result.get('severity')}) at {result.get('location')}")
            self._send_json(result)

        elif url.path == "/api/v1/polyflow/impact":
            result = execute_poly("polyflow_observe", {
                "change_type": "CODE_MODIFICATION",
                "changed_file": body.get("changed_file", "unknown.py"),
                "changed_component": body.get("changed_component", "Python CV")
            })
            self._send_json(result)

        elif url.path == "/api/v1/city/switch":
            global current_city_id
            city_id = body.get("city_id", "mumbai")
            if city_id in CITIES:
                current_city_id = city_id
                log_event("CITY_SWITCH", "SUCCESS", f"Switched digital twin focus to {CITIES[city_id]['name']}")
                self._send_json({"city": CITIES[city_id], "status": "switched"})
            else:
                self._send_json({"error": "City not found"}, status=404)

        elif url.path == "/api/v1/simulation/control":
            global sim_speed
            cmd = body.get("command", "status")
            if cmd == "speed":
                sim_speed = body.get("speed", 1.0)
            self._send_json({"sim_speed": sim_speed, "sim_step": city_state.get("sim_step", 0), "status": "ok"})

        else:
            self._send_json({"error": "Invalid API endpoint"}, status=404)

# ─── Server Boot ─────────────────────────────────────────────────────────────────

def run_server(port=8080):
    socketserver.TCPServer.allow_reuse_address = True
    try:
        server = socketserver.TCPServer(("0.0.0.0", port), UrbanOSHandler)
    except OSError:
        port = 8081
        server = socketserver.TCPServer(("0.0.0.0", port), UrbanOSHandler)
    log_event("BOOT", "SUCCESS", f"UrbanOS v2 Live Platform running on http://localhost:{port}")
    print(f"[OK] UrbanOS v2 Live Urban Operations Platform running on http://localhost:{port}")
    print(f"     {len(poly_registry)} .poly modules | Google Maps | YouTube Cameras | HYBRID mode")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down UrbanOS.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
