"""
World Monitor — PolyFlow Engine
================================
Single-file server: REST APIs + Live Data Adapters + Full Dashboard UI.
Serves a complete geopolitical intelligence dashboard powered by PolyFlow .poly modules.

Usage:
    python engine.py [PORT]
"""

import json, math, os, random, sys, threading, time, uuid
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote_plus

# ─── PolyFlow Integration ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
POLY_ROOT = ROOT / "features"
sys.path.insert(0, str(ROOT.parent))

try:
    from polyflow.parser import PolyParser
    from polyflow.runtime import PolyCellRuntime
    from polyflow.merge import PolyMergeEngine
    from polyflow.governance import PolyGovernanceEngine
    POLYFLOW_AVAILABLE = True
except ImportError:
    POLYFLOW_AVAILABLE = False

# ─── In-Memory Data Stores ────────────────────────────────────────────────────
EVENTS = []
SIGNALS = []
RISK_MAP = []
MARKET_DATA = {}
INTEL_ADVISORIES = []
LIVE_INCIDENTS = []
DATA_LOCK = threading.Lock()

# ─── Country Geodata ──────────────────────────────────────────────────────────
COUNTRY_GEO = {
    "US":{"name":"United States","lat":39.8,"lon":-98.6},
    "IN":{"name":"India","lat":20.6,"lon":78.9},
    "GB":{"name":"United Kingdom","lat":55.4,"lon":-3.4},
    "FR":{"name":"France","lat":46.2,"lon":2.2},
    "DE":{"name":"Germany","lat":51.2,"lon":10.4},
    "IT":{"name":"Italy","lat":41.9,"lon":12.6},
    "ES":{"name":"Spain","lat":40.5,"lon":-3.7},
    "UA":{"name":"Ukraine","lat":48.4,"lon":31.2},
    "PK":{"name":"Pakistan","lat":30.4,"lon":69.4},
    "AF":{"name":"Afghanistan","lat":33.9,"lon":67.7},
    "BD":{"name":"Bangladesh","lat":23.7,"lon":90.4},
    "JP":{"name":"Japan","lat":36.2,"lon":138.3},
    "TW":{"name":"Taiwan","lat":23.7,"lon":121.0},
    "PH":{"name":"Philippines","lat":12.9,"lon":121.8},
    "ID":{"name":"Indonesia","lat":-2.5,"lon":118.0},
    "RU":{"name":"Russia","lat":61.5,"lon":105.3},
    "CN":{"name":"China","lat":35.9,"lon":104.2},
    "IR":{"name":"Iran","lat":32.4,"lon":53.7},
    "IQ":{"name":"Iraq","lat":33.2,"lon":43.7},
    "SY":{"name":"Syria","lat":34.8,"lon":38.9},
    "KP":{"name":"North Korea","lat":40.3,"lon":127.5},
    "KR":{"name":"South Korea","lat":36.3,"lon":127.8},
    "AE":{"name":"UAE","lat":24.4,"lon":54.4},
    "SA":{"name":"Saudi Arabia","lat":24.0,"lon":45.0},
    "YE":{"name":"Yemen","lat":15.6,"lon":48.5},
    "IL":{"name":"Israel","lat":31.0,"lon":35.0},
    "LB":{"name":"Lebanon","lat":33.9,"lon":35.9},
    "JO":{"name":"Jordan","lat":31.2,"lon":36.5},
    "EG":{"name":"Egypt","lat":26.8,"lon":30.8},
    "TR":{"name":"Turkey","lat":39.0,"lon":35.2},
    "VE":{"name":"Venezuela","lat":6.4,"lon":-66.6},
    "MM":{"name":"Myanmar","lat":21.9,"lon":95.9},
    "NG":{"name":"Nigeria","lat":9.1,"lon":7.5},
    "ZA":{"name":"South Africa","lat":-30.6,"lon":22.9},
    "AU":{"name":"Australia","lat":-25.3,"lon":133.8},
    "BR":{"name":"Brazil","lat":-14.2,"lon":-51.9},
    "MX":{"name":"Mexico","lat":23.6,"lon":-102.5},
}

# ─── Webcams ──────────────────────────────────────────────────────────────────
WEBCAMS = [
    {"id":"nyc","title":"Times Square NYC","region":"Americas","cc":"US","lat":40.758,"lon":-73.985,
     "embed":"https://www.youtube.com/embed/live_stream?channel=UChqUTb7kYRX8-EiaN3XFrSQ&autoplay=1&mute=1"},
    {"id":"london","title":"London Live","region":"Europe","cc":"GB","lat":51.507,"lon":-0.128,
     "embed":"https://www.youtube.com/embed/live_stream?channel=UCXIJgqnII2ZOINSWNOGFThA&autoplay=1&mute=1"},
    {"id":"tokyo","title":"Tokyo Asia","region":"Asia","cc":"JP","lat":35.660,"lon":139.700,
     "embed":"https://www.youtube.com/embed/live_stream?channel=UCNye-wNBqNL5ZzHSJj3l8Bg&autoplay=1&mute=1"},
    {"id":"dubai","title":"Middle East","region":"Middle East","cc":"AE","lat":25.083,"lon":55.142,
     "embed":"https://www.youtube.com/embed/live_stream?channel=UCQfwfsi5VrQ8yKZ-UWmAEFg&autoplay=1&mute=1"},
    {"id":"cape","title":"Africa Live","region":"Africa","cc":"ZA","lat":-33.907,"lon":18.421,
     "embed":"https://www.youtube.com/embed/live_stream?channel=UC_gUM8rL-Lrg6O3adPW9K1g&autoplay=1&mute=1"},
]

# ─── Live Coverage Channels ──────────────────────────────────────────────────
LIVE_CHANNELS = [
    {"id":"UCXIJgqnII2ZOINSWNOGFThA","title":"Sky News Live","ch":"Sky News","thumbnail":"https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=160&q=80"},
    {"id":"UChqUTb7kYRX8-EiaN3XFrSQ","title":"Reuters Live","ch":"Reuters","thumbnail":"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=160&q=80"},
    {"id":"UC_gUM8rL-Lrg6O3adPW9K1g","title":"WION Live Global","ch":"WION","thumbnail":"https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?w=160&q=80"},
    {"id":"UCNye-wNBqNL5ZzHSJj3l8Bg","title":"Al Jazeera English","ch":"Al Jazeera","thumbnail":"https://images.unsplash.com/photo-1495020689067-958852a7765e?w=160&q=80"},
    {"id":"UCQfwfsi5VrQ8yKZ-UWmAEFg","title":"France 24 English","ch":"France 24","thumbnail":"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=160&q=80"},
]

# ─── Layer / Category Definitions ────────────────────────────────────────────
UI_LAYERS = [
    'Conflict','Military','Political','Weather','Natural','Economic',
    'Energy','Government','Retail','Materials','Nuclear','Airlines',
    'Sanctions','Security','Crypto','Telecom'
]
UI_REGIONS = ['Middle East','Europe','Asia','Americas','Africa','Oceania']

LAYER_KEYWORDS = {
    'Nuclear':['nuclear','reactor','radiation','atomic','uranium','iaea'],
    'Airlines':['airline','aviation','airport','airspace','flight'],
    'Telecom':['telecom','network','internet','fiber','5g','outage'],
    'Crypto':['crypto','bitcoin','btc','blockchain','stablecoin'],
    'Security':['cyber','threat','vulnerability','breach','malware'],
    'Sanctions':['sanction','designation','watchlist','blacklist','ofac'],
    'Energy':['energy','oil','gas','power grid','electricity','pipeline'],
    'Government':['government','cabinet','parliament','ministry'],
    'Retail':['retail','consumer','ecommerce','supply chain'],
    'Materials':['materials','metals','steel','copper','lithium'],
    'Political':['political','election','diplomatic','policy'],
    'Conflict':['conflict','war','attack','combat','strike','militant','bombing','insurgent'],
    'Military':['military','army','navy','troops','defense','weapon','missile','drone'],
    'Weather':['weather','storm','cyclone','hurricane','typhoon'],
    'Natural':['earthquake','flood','wildfire','volcano','drought','tsunami'],
    'Economic':['economic','market','finance','trade','inflation','currency','bank']
}

REGION_MAP = {
    'US':'Americas','CA':'Americas','MX':'Americas','BR':'Americas','AR':'Americas','VE':'Americas','CU':'Americas',
    'GB':'Europe','FR':'Europe','DE':'Europe','IT':'Europe','ES':'Europe','PL':'Europe','UA':'Europe','RU':'Europe','NL':'Europe','SE':'Europe','NO':'Europe','CH':'Europe',
    'CN':'Asia','IN':'Asia','JP':'Asia','KR':'Asia','PK':'Asia','BD':'Asia','TH':'Asia','VN':'Asia','ID':'Asia','MY':'Asia','PH':'Asia','SG':'Asia','TW':'Asia','MM':'Asia',
    'SA':'Middle East','AE':'Middle East','IR':'Middle East','IQ':'Middle East','SY':'Middle East','IL':'Middle East','YE':'Middle East','TR':'Middle East','EG':'Middle East','LB':'Middle East','JO':'Middle East','AF':'Middle East',
    'ZA':'Africa','NG':'Africa','KE':'Africa','ET':'Africa','SD':'Africa','DZ':'Africa','MA':'Africa',
    'AU':'Oceania','NZ':'Oceania',
}

# ─── Event / Signal Generation ────────────────────────────────────────────────

def classify_event(text):
    text_lower = text.lower()
    for layer, kws in LAYER_KEYWORDS.items():
        if any(k in text_lower for k in kws):
            return layer
    return 'Political'

def generate_events(count=140):
    """Generate realistic geopolitical events."""
    headlines = {
        'Conflict': [
            'Escalation in border region as artillery exchanges intensify',
            'Ceasefire negotiations collapse amid renewed hostilities',
            'Coalition airstrike targets militant positions',
            'Cross-border skirmish reported in disputed territory',
            'Armed group seizes control of strategic checkpoint',
        ],
        'Military': [
            'Naval fleet deployment in contested waters detected',
            'Hypersonic missile test conducted by state actor',
            'Military exercises signal capability demonstration',
            'Defense procurement deal signed between allies',
            'Troop buildup detected via satellite imagery',
        ],
        'Political': [
            'Diplomatic summit ends without consensus on key issues',
            'Opposition leader detained amid protests',
            'Electoral commission reports irregularities',
            'Government reshuffles cabinet in surprise move',
            'Sanctions package draws retaliatory measures',
        ],
        'Weather': [
            'Category 4 typhoon approaches populated coastline',
            'Record rainfall triggers flood emergency',
            'Extreme heatwave strains power grid infrastructure',
            'Cyclone warning issued for coastal communities',
        ],
        'Natural': [
            'Magnitude 6.2 earthquake strikes populated area',
            'Volcanic eruption forces mass evacuation',
            'Wildfire threatens critical infrastructure',
            'Tsunami advisory issued following undersea event',
        ],
        'Economic': [
            'Central bank raises rates amid inflation spike',
            'Currency devaluation triggers capital flight',
            'Trade deficit widens to historic levels',
            'Supply chain disruption affects semiconductor sector',
        ],
        'Energy': [
            'Pipeline sabotage disrupts energy supply corridor',
            'OPEC production cut announcement rattles markets',
            'LNG terminal incident disrupts gas exports',
        ],
        'Security': [
            'Critical infrastructure targeted in coordinated cyber attack',
            'Zero-day vulnerability discovered in widely-used protocol',
            'State-sponsored hacking campaign uncovered',
        ],
    }

    countries_by_region = {
        'Middle East': ['IL','IR','IQ','SY','YE','SA','AE','LB','JO','EG','TR','AF'],
        'Europe': ['UA','RU','GB','FR','DE','IT','ES'],
        'Asia': ['CN','IN','JP','KR','PK','BD','TW','PH','ID','MM'],
        'Americas': ['US','BR','MX','VE'],
        'Africa': ['NG','ZA','EG'],
        'Oceania': ['AU'],
    }

# ─── PolyFlow Execution Helper ────────────────────────────────────────────────
def execute_poly(filename, payload):
    """Execute a .poly file via PolyFlow compiler & multi-language runtime."""
    if not POLYFLOW_AVAILABLE:
        return {"error": "PolyFlow runtime not available"}
    try:
        poly_path = POLY_ROOT / filename
        if not poly_path.exists():
            return {"error": f"Module not found: {filename}"}
        
        ast = PolyParser().parse_file(str(poly_path))
        runtime = PolyCellRuntime(fast_native_mode=True)
        merge = PolyMergeEngine()
        gov = PolyGovernanceEngine()
        
        # Verify governance contract
        valid, warnings = gov.verify_contract(ast.contract)
        
        # Execute all polyglot cells (Python, Go, TypeScript, Java, Rust, SQL)
        cell_results = []
        for block in ast.language_blocks:
            res = runtime.execute_cell(block, payload)
            cell_results.append(res)
        
        # Merge outputs based on AST merge strategy
        merged = merge.merge(cell_results, ast.merge_strategy)
        winner_output = merged.get("output", {})
        
        # Audit execution in Merkle ledger
        gov.audit_execution(str(poly_path), "execute", {"winner": merged.get("winner"), "status": merged.get("status")})
        
        return winner_output
    except Exception as ex:
        print(f"[PolyFlow] Execution error in {filename}: {ex}")
        return {"error": str(ex)}


def generate_events(count=140):
    """Generate and enrich events using geopolitical_events.poly module."""
    headlines = [
        ('Escalation in border region as artillery exchanges intensify', 'Conflict'),
        ('Ceasefire negotiations collapse amid renewed hostilities', 'Conflict'),
        ('Coalition airstrike targets strategic militant positions', 'Conflict'),
        ('Naval fleet deployment in contested waters detected', 'Military'),
        ('Hypersonic missile test conducted by state actor', 'Military'),
        ('Diplomatic summit ends without consensus on key treaty', 'Political'),
        ('Opposition leader detained amid mass protests', 'Political'),
        ('Category 4 typhoon approaches populated coastline', 'Weather'),
        ('Magnitude 6.2 earthquake strikes populated fault zone', 'Natural'),
        ('Central bank raises benchmark rate amid inflation surge', 'Economic'),
        ('Pipeline sabotage disrupts critical energy supply corridor', 'Energy'),
        ('Critical infrastructure targeted in coordinated cyber attack', 'Security'),
    ]

    countries_by_region = {
        'Middle East': ['IL','IR','IQ','SY','YE','SA','AE','LB','JO','EG','TR','AF'],
        'Europe': ['UA','RU','GB','FR','DE','IT','ES'],
        'Asia': ['CN','IN','JP','KR','PK','BD','TW','PH','ID','MM'],
        'Americas': ['US','BR','MX','VE'],
        'Africa': ['NG','ZA','EG'],
        'Oceania': ['AU'],
    }

    events = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        headline, raw_cat = random.choice(headlines)
        region = random.choice(UI_REGIONS)
        cc_list = countries_by_region.get(region, ['US'])
        cc = random.choice(cc_list)
        geo = COUNTRY_GEO.get(cc, {"name":"Unknown","lat":0,"lon":0})
        sev = round(random.betavariate(2, 3) * 0.7 + 0.15, 3)
        age_hours = random.expovariate(0.08)
        event_time = now - timedelta(hours=min(age_hours, 504))

        raw_event = {
            "id": str(uuid.uuid4()),
            "source_type": random.choice(["gdelt","rss","scrape","live-news"]),
            "event_date": event_time.isoformat(),
            "country_code": cc,
            "country_name": geo["name"],
            "category": raw_cat,
            "cameo_root": str(random.randint(1,20)).zfill(2),
            "actor1_name": random.choice(["Government Forces","Opposition","Coalition","Militants","Diplomatic Mission","Central Bank","Naval Command"]),
            "actor2_name": random.choice(["Civilian Population","Allied Forces","Trade Partners","Border Guards",None]),
            "lat": geo["lat"] + random.uniform(-2, 2),
            "lon": geo["lon"] + random.uniform(-2, 2),
            "source_url": random.choice(["https://reuters.com","https://apnews.com","https://bbc.com","https://aljazeera.com",None]),
            "composite_severity": sev,
            "headline": headline,
            "summary": f"{headline}. Severity assessed at {sev:.0%}.",
            "created_at": event_time.isoformat(),
        }

        # Enrich event via geopolitical_events.poly module
        poly_res = execute_poly("geopolitical_events.poly", raw_event)
        if isinstance(poly_res, dict) and "ui_layer" in poly_res:
            raw_event.update(poly_res)

        events.append(raw_event)

    return sorted(events, key=lambda e: e.get("created_at",""), reverse=True)


def generate_signals(events):
    """Generate anomaly signals by delegating to signal_detection.poly."""
    country_counts = {}
    for e in events:
        cc = e.get("country_code","")
        cat = e.get("category","")
        key = f"{cc}_{cat}"
        if key not in country_counts:
            country_counts[key] = {"country_code":cc,"category":cat,"current":0,"mean":4.0,"std":1.8}
        country_counts[key]["current"] += 1

    # Execute signal_detection.poly module
    poly_res = execute_poly("signal_detection.poly", {"event_counts": country_counts})
    if isinstance(poly_res, dict) and "signals" in poly_res:
        return sorted(poly_res["signals"], key=lambda s: s.get("severity", 0), reverse=True)
    return []


def compute_risk_map(events, signals):
    """Compute country risk scores by delegating to country_risk.poly."""
    poly_res = execute_poly("country_risk.poly", {"events": events, "signals": signals})
    if isinstance(poly_res, dict) and "risk_map" in poly_res:
        return poly_res["risk_map"]
    return []


def generate_market_data():
    """Generate real-time market snapshot by delegating to market_data.poly."""
    poly_res = execute_poly("market_data.poly", {"refresh": True})
    if isinstance(poly_res, dict) and "equities" in poly_res:
        return poly_res
    return {
        "regime": "neutral",
        "fear_greed": 50,
        "equities": [],
        "commodities": [],
        "crypto": []
    }


def generate_intel(count=35):
    """Generate intelligence advisories by delegating to intel_ingest.poly."""
    poly_res = execute_poly("intel_ingest.poly", {"limit": count})
    if isinstance(poly_res, dict) and "advisories" in poly_res:
        return poly_res["advisories"]
    return []


# ─── Data Refresh Thread ──────────────────────────────────────────────────────
def refresh_data():
    global EVENTS, SIGNALS, RISK_MAP, MARKET_DATA, INTEL_ADVISORIES, LIVE_INCIDENTS
    while True:
        try:
            evts = generate_events(140)
            sigs = generate_signals(evts)
            rmap = compute_risk_map(evts, sigs)
            mkt = generate_market_data()
            intel = generate_intel(35)
            incidents = generate_intel(25)

            with DATA_LOCK:
                EVENTS = evts
                SIGNALS = sigs
                RISK_MAP = rmap
                MARKET_DATA = mkt
                INTEL_ADVISORIES = intel
                LIVE_INCIDENTS = incidents
        except Exception as ex:
            print(f"[data-refresh] Error: {ex}")
        time.sleep(30)


# ─── HTML Dashboard Builder ───────────────────────────────────────────────────
def build_dashboard_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>World Monitor — Geopolitical Intelligence Platform</title>
<meta name="description" content="Real-time geopolitical intelligence, risk mapping, and financial signal detection powered by PolyFlow">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"/>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{--bg1:#05070d;--bg2:#090d15;--text:#d9e2ef;--muted:#8f9bb0;--edge:rgba(188,209,239,0.2);--glass:rgba(8,14,25,0.72);--glass-strong:rgba(6,10,18,0.85);--accent:#4fa8ff;--danger:#ff5757;--success:#67d17d;--warning:#f3a24f}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;min-height:100%;overflow-x:hidden;overflow-y:auto;color:var(--text);font-family:'Rajdhani',system-ui,sans-serif;background:radial-gradient(circle at 15% 20%, #13223e 0%, var(--bg2) 33%, var(--bg1) 70%)}
.mono{font-family:'JetBrains Mono',monospace}

/* ─── STAGE CONTAINER ─── */
.wm-stage{position:relative;width:100%;height:100vh;min-height:640px;overflow:hidden}
.wm-map-wrap{position:absolute;inset:0;z-index:1}
#map{width:100%;height:100%}
.leaflet-control-zoom{display:none !important}

/* ─── GLASS PANEL STYLES ─── */
.glass-panel{background:linear-gradient(135deg,rgba(17,27,44,0.82),rgba(5,10,18,0.72));backdrop-filter:blur(16px);border:1px solid var(--edge);box-shadow:0 12px 44px rgba(0,0,0,0.5);border-radius:10px}

/* ─── HEADER ─── */
.wm-header{position:absolute;top:10px;left:12px;right:12px;height:54px;border-radius:10px;z-index:40;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 14px}
.wm-brand{display:flex;flex-direction:column;line-height:1.1;cursor:pointer}
.wm-brand strong{letter-spacing:0.12em;font-size:1.05rem;color:#fff;text-transform:uppercase}
.wm-brand span{color:var(--accent);font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase}
.wm-head-controls{display:flex;align-items:center;gap:8px;flex:1;max-width:580px;margin:0 12px}
.wm-search{flex:1;height:34px;border-radius:7px;border:1px solid rgba(169,199,237,0.24);background:rgba(5,11,20,0.65);color:#edf4ff;padding:0 12px;font-family:'JetBrains Mono',monospace;font-size:0.75rem;outline:none;transition:border-color 0.2s}
.wm-search:focus{border-color:var(--accent)}
.wm-time-btns{display:inline-flex;border:1px solid rgba(160,194,235,0.3);border-radius:7px;overflow:hidden;background:rgba(7,15,26,0.6)}
.wm-time-btns button{border:none;border-right:1px solid rgba(160,194,235,0.2);background:transparent;color:#a9bdd8;padding:4px 9px;font-size:0.7rem;font-family:'JetBrains Mono',monospace;cursor:pointer;transition:all 0.2s}
.wm-time-btns button:last-child{border-right:none}
.wm-time-btns button.active{background:rgba(79,168,255,0.28);color:#edf4ff}
.wm-head-actions{display:flex;align-items:center;gap:6px}
.wm-head-actions button{height:32px;border:1px solid rgba(160,194,235,0.28);background:rgba(7,15,26,0.7);color:#cfe1fb;border-radius:7px;padding:0 10px;font-size:0.72rem;cursor:pointer;display:inline-flex;align-items:center;gap:5px;transition:all 0.2s}
.wm-head-actions button:hover{border-color:var(--accent);color:#fff;background:rgba(79,168,255,0.15)}
.wm-head-actions button.active{border-color:var(--accent);background:rgba(79,168,255,0.25);color:var(--accent)}
.wm-status-pill{font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#b9ffcc;border:1px solid rgba(103,209,125,0.45);background:rgba(24,87,46,0.22);border-radius:999px;padding:3px 8px;display:inline-flex;align-items:center;gap:5px}
.pulse-dot{width:6px;height:6px;border-radius:50%;background:#67d17d;animation:pulse-dot 2s infinite}

/* ─── FLOATING OVERLAY PANELS ─── */
.wm-overlay{position:absolute;z-index:25;display:flex;flex-direction:column;transition:all 220ms ease;user-select:none}
.wm-overlay.left{top:72px;left:12px;width:330px;max-height:calc(100vh - 160px)}
.wm-overlay.right{top:72px;right:12px;width:310px;max-height:calc(100vh - 160px)}

/* Minimized States */
.wm-overlay.minimized{width:auto !important;max-height:42px !important;overflow:hidden}
.wm-overlay.minimized .wm-overlay-body{display:none !important}
.wm-overlay.minimized .wm-overlay-head{border-bottom:none;padding:6px 12px;cursor:pointer}
.wm-overlay.minimized .wm-overlay-head h3{font-size:0.75rem}

.wm-overlay-head{height:40px;border-bottom:1px solid rgba(170,200,238,0.2);display:flex;align-items:center;justify-content:space-between;padding:0 10px;cursor:grab}
.wm-overlay-head h3{margin:0;font-size:0.8rem;letter-spacing:0.06em;text-transform:uppercase;color:#d7e8ff;display:flex;align-items:center;gap:6px}
.wm-overlay-head button{width:26px;height:26px;border:1px solid rgba(160,194,235,0.3);border-radius:6px;background:rgba(5,12,20,0.5);color:#d6e8ff;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:10px;transition:all 0.2s}
.wm-overlay-head button:hover{border-color:var(--accent);color:#fff}
.wm-overlay-body{flex:1;overflow-y:auto;padding:8px;scrollbar-width:thin;scrollbar-color:rgba(79,168,255,0.3) transparent}
.wm-overlay-body::-webkit-scrollbar{width:4px}
.wm-overlay-body::-webkit-scrollbar-thumb{background:rgba(79,168,255,0.3);border-radius:4px}

/* ─── BRIEFING CARDS ─── */
.wm-kpi-chips{display:grid;grid-template-columns:repeat(4, 1fr);gap:4px;margin-bottom:8px}
.wm-kpi-chip{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:5px 2px;text-align:center}
.wm-kpi-chip .val{font-size:14px;font-weight:700;font-family:'JetBrains Mono',monospace}
.wm-kpi-chip .lbl{font-size:8px;color:var(--muted);text-transform:uppercase}

.wm-region-pills{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px}
.wm-region-pills button{border:1px solid rgba(160,194,235,0.2);background:rgba(7,15,26,0.6);color:#cfe1fb;border-radius:999px;padding:2px 7px;font-size:0.68rem;cursor:pointer;transition:all 0.2s}
.wm-region-pills button.active{border-color:var(--accent);background:rgba(79,168,255,0.25);color:var(--accent)}

.wm-card{width:100%;text-align:left;border-radius:8px;border:1px solid rgba(166,198,235,0.12);background:rgba(6,14,24,0.5);color:#daebff;padding:8px;margin-bottom:6px;cursor:pointer;transition:all 0.2s}
.wm-card:hover,.wm-card.active{border-color:rgba(129,184,255,0.5);background:rgba(9,20,36,0.8)}
.wm-card h5{font-size:11px;font-weight:600;color:#fff;margin-bottom:4px;line-height:1.3}
.wm-card-meta{display:flex;gap:5px;align-items:center;flex-wrap:wrap;font-size:9px;color:var(--muted);font-family:'JetBrains Mono',monospace}

.badge{padding:1px 5px;border-radius:4px;font-size:8.5px;font-weight:600;text-transform:uppercase}
.badge-critical{background:rgba(255,87,87,0.2);color:#ff5757;border:1px solid rgba(255,87,87,0.3)}
.badge-high{background:rgba(255,143,102,0.2);color:#ff8f66;border:1px solid rgba(255,143,102,0.3)}
.badge-moderate{background:rgba(243,162,79,0.2);color:#f3a24f;border:1px solid rgba(243,162,79,0.3)}
.badge-low{background:rgba(103,209,125,0.2);color:#67d17d;border:1px solid rgba(103,209,125,0.3)}
.badge-layer{background:rgba(79,168,255,0.15);color:var(--accent);border:1px solid rgba(79,168,255,0.25)}
.badge-trust{background:rgba(103,209,125,0.15);color:#67d17d;border:1px solid rgba(103,209,125,0.25)}

/* ─── MARKET STRIP (DRAGGABLE/MINIMIZABLE) ─── */
.wm-market-strip{position:absolute;top:72px;left:354px;z-index:30;border-radius:10px;padding:6px 10px;cursor:grab;user-select:none;display:flex;align-items:center;gap:10px}
.wm-market-strip.minimized{left:auto;right:332px;top:72px;padding:5px 10px}
.wm-market-strip.minimized .full-ticker{display:none}
.wm-market-strip.minimized .compact-ticker{display:inline-flex}
.compact-ticker{display:none;align-items:center;gap:6px;font-size:0.72rem;font-family:'JetBrains Mono',monospace}
.full-ticker{display:flex;align-items:center;gap:10px}
.ticker-item{display:flex;align-items:center;gap:4px;font-size:10px;font-family:'JetBrains Mono',monospace}
.ticker-item .sym{color:var(--muted);font-size:9px}
.ticker-item .price{color:#fff;font-weight:600}
.ticker-item .up{color:var(--success)}
.ticker-item .dn{color:var(--danger)}
.regime-pill{font-size:9px;padding:2px 6px;border-radius:4px;font-weight:600;text-transform:uppercase}
.regime-risk_on{background:rgba(103,209,125,0.2);color:var(--success);border:1px solid rgba(103,209,125,0.3)}
.regime-risk_off{background:rgba(255,87,87,0.2);color:var(--danger);border:1px solid rgba(255,87,87,0.3)}
.regime-neutral{background:rgba(79,168,255,0.15);color:var(--accent);border:1px solid rgba(79,168,255,0.25)}

/* ─── WEBCAM PANEL (DRAGGABLE/MINIMIZABLE) ─── */
.wm-webcam-panel{position:absolute;bottom:76px;right:12px;width:300px;border-radius:10px;z-index:32;display:flex;flex-direction:column;overflow:hidden}
.wm-webcam-panel.minimized{width:auto;bottom:12px;right:12px}
.wm-webcam-panel.minimized iframe,.wm-webcam-panel.minimized .wm-webcam-body{display:none}
.wm-webcam-panel.minimized .wm-webcam-head{padding:6px 12px;cursor:pointer}
.wm-webcam-frame{width:100%;height:165px;border:none;background:#000}
.wm-webcam-body{padding:8px 10px;display:flex;justify-content:space-between;align-items:center;font-size:11px}

/* ─── LAYER BAR (BOTTOM MAP STAGE) ─── */
.wm-layers-bar{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:30;border-radius:999px;padding:4px 10px;display:flex;align-items:center;gap:4px;max-width:calc(100vw - 320px);overflow-x:auto;scrollbar-width:none}
.wm-layers-bar::-webkit-scrollbar{display:none}
.wm-layers-bar.minimized{min-width:auto;padding:4px 8px}
.wm-layers-bar.minimized .layer-btns{display:none}
.layer-btn{border:1px solid rgba(160,194,235,0.25);background:rgba(7,15,26,0.65);color:#cfe1fb;border-radius:999px;padding:3px 9px;font-size:0.72rem;cursor:pointer;white-space:nowrap;transition:all 0.2s}
.layer-btn:hover{border-color:var(--accent);color:#fff}
.layer-btn.active{border-color:var(--accent);background:rgba(79,168,255,0.28);color:#fff}

/* ─── SCROLL PROMPT ─── */
.wm-scroll-hint{position:absolute;bottom:54px;left:50%;transform:translateX(-50%);z-index:20;font-size:10px;color:var(--muted);letter-spacing:0.1em;text-transform:uppercase;display:flex;align-items:center;gap:6px;pointer-events:none;opacity:0.7;animation:bounce-hint 2s infinite}

/* ─── ANALYTICS DECK (SCROLLABLE SECTION) ─── */
.wm-analytics-deck{position:relative;z-index:5;padding:32px 18px 48px;background:radial-gradient(circle at 20% 18%, rgba(65,117,177,0.12), transparent 42%), radial-gradient(circle at 85% 30%, rgba(95,58,34,0.15), transparent 38%), linear-gradient(180deg, rgba(6,12,20,0.98), rgba(4,8,15,0.99));border-top:1px solid rgba(173,203,237,0.2)}
.wm-deck-head{max-width:1280px;margin:0 auto 16px;display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:12px}
.wm-deck-head h2{font-size:1.2rem;letter-spacing:0.08em;text-transform:uppercase;color:#fff;display:flex;align-items:center;gap:8px}
.wm-deck-head span{font-family:'JetBrains Mono',monospace;color:#9eb2cf;font-size:0.75rem}

.wm-deck-kpis{max-width:1280px;margin:0 auto 18px;display:grid;grid-template-columns:repeat(4, minmax(0,1fr));gap:12px}
.wm-deck-kpi{border-radius:10px;padding:12px;background:linear-gradient(135deg,rgba(17,27,44,0.7),rgba(5,10,18,0.55));border:1px solid var(--edge)}
.wm-deck-kpi h3{font-size:0.75rem;letter-spacing:0.06em;text-transform:uppercase;color:#b7c9e3;margin-bottom:4px}
.wm-deck-kpi strong{display:block;font-size:1.5rem;color:#e3f0ff;font-family:'JetBrains Mono',monospace}
.wm-deck-kpi p{margin-top:4px;color:#9db0cb;font-size:0.74rem}

.wm-deck-controls{max-width:1280px;margin:0 auto 18px;padding:10px 14px;border-radius:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.wm-filter-tags{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.wm-filter-pill{font-size:0.72rem;padding:3px 9px;border-radius:999px;background:rgba(79,168,255,0.15);border:1px solid rgba(79,168,255,0.3);color:var(--accent)}

.wm-analytics-grid{max-width:1280px;margin:0 auto;display:grid;grid-template-columns:repeat(2, minmax(0,1fr));gap:14px}
.wm-analytic-card{border-radius:10px;padding:14px;background:linear-gradient(135deg,rgba(17,27,44,0.7),rgba(5,10,18,0.55));border:1px solid var(--edge)}
.wm-analytic-title{margin-bottom:10px}
.wm-analytic-title h3{margin:0;font-size:0.85rem;letter-spacing:0.06em;text-transform:uppercase;color:#d0e2fa;display:flex;align-items:center;gap:6px}
.wm-analytic-title p{margin:4px 0 0;color:#9fb2cf;font-size:0.74rem}
.wm-analytic-card canvas{width:100% !important;height:220px !important}

/* ─── LIVE VIDEO DESK CARD ─── */
.wm-video-desk{display:flex;flex-direction:column;gap:10px}
.wm-video-frame{width:100%;height:220px;border-radius:8px;border:1px solid rgba(160,194,235,0.28);background:#000}
.wm-video-strip{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:thin}
.wm-video-item{min-width:160px;max-width:160px;border-radius:6px;border:1px solid rgba(160,194,235,0.2);background:rgba(7,15,26,0.6);padding:6px;cursor:pointer;transition:all 0.2s}
.wm-video-item.active{border-color:var(--accent);background:rgba(79,168,255,0.2)}
.wm-video-item img{width:100%;height:60px;object-fit:cover;border-radius:4px;margin-bottom:4px}
.wm-video-item strong{display:block;font-size:0.7rem;color:#fff;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wm-video-item span{display:block;font-size:0.65rem;color:var(--muted)}

/* ─── TABLES ─── */
.wm-table{width:100%;border-collapse:collapse;font-size:11px;text-align:left}
.wm-table th{color:var(--muted);font-weight:600;text-transform:uppercase;font-size:9px;padding:6px 8px;border-bottom:1px solid rgba(255,255,255,0.08);font-family:'JetBrains Mono',monospace}
.wm-table td{padding:6px 8px;border-bottom:1px solid rgba(255,255,255,0.04);color:#d9e2ef}
.wm-table tr:hover td{background:rgba(79,168,255,0.06)}

/* ─── ANIMATIONS ─── */
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:0.3}}
@keyframes bounce-hint{0%,100%{transform:translate(-50%, 0)}50%{transform:translate(-50%, 4px)}}
@keyframes fade-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.fade-in{animation:fade-in 0.3s ease-out}

/* ─── LEAFLET POPUP / TOOLTIP ─── */
.leaflet-tooltip{background:rgba(8,14,25,0.92) !important;border:1px solid rgba(79,168,255,0.3) !important;color:var(--text) !important;font-family:'Rajdhani',sans-serif !important;font-size:12px !important;border-radius:6px !important;padding:6px 10px !important;box-shadow:0 4px 16px rgba(0,0,0,0.4) !important}
.leaflet-tooltip::before{border-top-color:rgba(8,14,25,0.92) !important}
</style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════════════════════════
     MAP STAGE (TOP FULL-VIEWPORT SECTION)
═══════════════════════════════════════════════════════════════════════════════ -->
<div class="wm-stage" id="stage">
  <!-- LEAFLET MAP -->
  <div class="wm-map-wrap">
    <div id="map"></div>
  </div>

  <!-- TOP HEADER -->
  <header class="wm-header glass-panel">
    <div class="wm-brand" onclick="resetFilters()">
      <strong>World Monitor</strong>
      <span>Geopolitical Intelligence Platform</span>
    </div>

    <div class="wm-head-controls">
      <input id="search-input" class="wm-search" type="text" placeholder="Search events, countries, layers, actors..." autocomplete="off">
      <div class="wm-time-btns">
        <button onclick="setDayWindow(1)" id="btn-1d">1D</button>
        <button onclick="setDayWindow(7)" id="btn-7d">7D</button>
        <button onclick="setDayWindow(21)" id="btn-21d" class="active">21D</button>
      </div>
    </div>

    <div class="wm-head-actions">
      <span class="wm-status-pill"><span class="pulse-dot"></span> <span id="hdr-status">LIVE ● 140 EVENTS</span></span>
      <button onclick="toggleFocusMode()" id="btn-focus" title="Toggle Focus Map Mode"><i class="fa-solid fa-expand"></i> Focus</button>
      <button onclick="minimizeAllPanels()" id="btn-min-all" title="Minimize all hovering panels"><i class="fa-solid fa-compress"></i> Minimize</button>
      <button onclick="restoreAllPanels()" id="btn-rest-all" title="Restore all hovering panels"><i class="fa-solid fa-window-restore"></i> Restore</button>
      <button onclick="toggleMapTheme()" id="btn-theme" title="Change Map Theme"><i class="fa-solid fa-layer-group"></i></button>
    </div>
  </header>

  <!-- MARKET STRIP (DRAGGABLE & MINIMIZABLE) -->
  <div class="wm-market-strip glass-panel" id="market-strip">
    <div class="compact-ticker" onclick="togglePanel('market-strip')">
      <i class="fa-solid fa-chart-line" style="color:var(--accent)"></i>
      <span id="compact-mkt-text">MARKET TICKER</span>
    </div>
    <div class="full-ticker" id="full-market-ticker">
      <!-- Injected via JS -->
    </div>
    <button onclick="togglePanel('market-strip')" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:11px;margin-left:4px" title="Minimize / Expand"><i class="fa-solid fa-minus"></i></button>
  </div>

  <!-- LEFT OVERLAY — INTELLIGENCE BRIEFING (MINIMIZABLE) -->
  <div class="wm-overlay left glass-panel" id="panel-briefing">
    <div class="wm-overlay-head" onclick="togglePanelIfMinimized('panel-briefing')">
      <h3><i class="fa-solid fa-satellite-dish" style="color:var(--accent)"></i> <span id="briefing-title">Briefing</span></h3>
      <div>
        <button onclick="event.stopPropagation(); togglePanel('panel-briefing')" title="Minimize / Expand"><i class="fa-solid fa-minus"></i></button>
      </div>
    </div>
    <div class="wm-overlay-body">
      <div class="wm-kpi-chips" id="kpi-chips"></div>
      <div class="wm-region-pills" id="region-pills"></div>
      <div id="briefing-list"></div>
    </div>
  </div>

  <!-- RIGHT OVERLAY — LIVE INCIDENTS FEED (MINIMIZABLE) -->
  <div class="wm-overlay right glass-panel" id="panel-incidents">
    <div class="wm-overlay-head" onclick="togglePanelIfMinimized('panel-incidents')">
      <h3><i class="fa-solid fa-bolt" style="color:var(--warning)"></i> <span id="incidents-title">Live Feed</span></h3>
      <div>
        <button onclick="event.stopPropagation(); togglePanel('panel-incidents')" title="Minimize / Expand"><i class="fa-solid fa-minus"></i></button>
      </div>
    </div>
    <div class="wm-overlay-body" id="incident-list"></div>
  </div>

  <!-- WEBCAM PANEL (DRAGGABLE & MINIMIZABLE) -->
  <div class="wm-webcam-panel glass-panel" id="panel-webcam">
    <div class="wm-overlay-head" onclick="togglePanelIfMinimized('panel-webcam')">
      <h3><i class="fa-solid fa-video" style="color:var(--danger)"></i> <span id="webcam-head-title">Live Cam</span></h3>
      <div>
        <button onclick="event.stopPropagation(); togglePanel('panel-webcam')" title="Minimize / Expand"><i class="fa-solid fa-minus"></i></button>
      </div>
    </div>
    <iframe class="wm-webcam-frame" id="webcam-frame" allow="autoplay; encrypted-media" allowfullscreen></iframe>
    <div class="wm-webcam-body">
      <span id="webcam-title" style="font-weight:600;color:#fff;font-size:11px">Times Square Live</span>
      <div style="display:flex;gap:4px">
        <button onclick="prevWebcam()" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:4px;padding:2px 6px;cursor:pointer"><i class="fa-solid fa-chevron-left"></i></button>
        <button onclick="nextWebcam()" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#fff;border-radius:4px;padding:2px 6px;cursor:pointer"><i class="fa-solid fa-chevron-right"></i></button>
      </div>
    </div>
  </div>

  <!-- BOTTOM LAYER SELECTOR BAR -->
  <div class="wm-layers-bar glass-panel" id="layers-bar">
    <button onclick="togglePanel('layers-bar')" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:11px;padding:0 4px" title="Toggle Layer Bar"><i class="fa-solid fa-layer-group"></i></button>
    <div class="layer-btns" id="layer-btns" style="display:flex;gap:4px;align-items:center"></div>
  </div>

  <!-- SCROLL PROMPT -->
  <div class="wm-scroll-hint">
    <span>Scroll Down for Situation Room Analytics</span>
    <i class="fa-solid fa-chevron-down"></i>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════════
     ANALYTICS DECK (BELOW MAP STAGE)
═══════════════════════════════════════════════════════════════════════════════ -->
<section class="wm-analytics-deck" id="analytics-deck">
  <!-- DECK HEADER -->
  <div class="wm-deck-head">
    <div>
      <h2><i class="fa-solid fa-chart-pie" style="color:var(--accent)"></i> Situation Room Analytics</h2>
      <span id="deck-subtitle">Global Geopolitical Posture & Financial Impact Matrix</span>
    </div>
    <div class="wm-filter-tags" id="deck-filter-tags">
      <!-- Active filters badges -->
    </div>
  </div>

  <!-- EXECUTIVE KPIS -->
  <div class="wm-deck-kpis">
    <div class="wm-deck-kpi">
      <h3>Total Events Scoped</h3>
      <strong id="kpi-total-scoped" style="color:var(--accent)">0</strong>
      <p id="kpi-total-desc">Across selected timeframe & layers</p>
    </div>
    <div class="wm-deck-kpi">
      <h3>Critical Threats</h3>
      <strong id="kpi-critical" style="color:var(--danger)">0</strong>
      <p>Severity &gt; 80% with escalation risk</p>
    </div>
    <div class="wm-deck-kpi">
      <h3>Anomaly Signals</h3>
      <strong id="kpi-signals" style="color:var(--warning)">0</strong>
      <p>Z-Score & CUSUM burst detections</p>
    </div>
    <div class="wm-deck-kpi">
      <h3>Macro Market Regime</h3>
      <strong id="kpi-regime" style="color:var(--success)">NEUTRAL</strong>
      <p id="kpi-fg">Fear & Greed Index: 50</p>
    </div>
  </div>

  <!-- ANALYTICS CARDS GRID (8 RICH ANALYTICAL MODULES) -->
  <div class="wm-analytics-grid">
    <!-- 1. INCIDENT TREND & VELOCITY -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-arrow-trend-up"></i> Incident Trend & Velocity</h3>
        <p>Daily volume progression and surge velocity over the active window.</p>
      </div>
      <canvas id="chart-trend"></canvas>
    </div>

    <!-- 2. CATEGORY MOMENTUM -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-gauge-high"></i> Category Momentum</h3>
        <p>Sector velocity delta showing surging vs easing threat domains.</p>
      </div>
      <canvas id="chart-momentum"></canvas>
    </div>

    <!-- 3. AVERAGE SEVERITY PROGRESSION -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-fire"></i> Severity Escalation Curve</h3>
        <p>Weighted average severity tracking whether incidents are intensifying.</p>
      </div>
      <canvas id="chart-severity"></canvas>
    </div>

    <!-- 4. TOP COUNTRY RISK PRESSURE -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-flag"></i> Top Country Risk Pressure</h3>
        <p>Cumulative conflict, political, and economic pressure ranking.</p>
      </div>
      <canvas id="chart-countries"></canvas>
    </div>

    <!-- 5. LIVE VIDEO COVERAGE DESK -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-tv"></i> Live Coverage Desk</h3>
        <p>Ranked live broadcasts and news desks corresponding to active threats.</p>
      </div>
      <div class="wm-video-desk">
        <iframe class="wm-video-frame" id="coverage-video" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        <div class="wm-video-strip" id="coverage-strip"></div>
      </div>
    </div>

    <!-- 6. FINANCIAL INTELLIGENCE & SECTOR IMPACT -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-coins"></i> Financial Intelligence & Sector Impact</h3>
        <p>Geopolitical signal transmission into asset classes and industry sectors.</p>
      </div>
      <div style="overflow-x:auto">
        <table class="wm-table">
          <thead>
            <tr><th>Sector</th><th>Direction</th><th>Impact Prob</th><th>Macro Multiplier</th><th>Time Horizon</th></tr>
          </thead>
          <tbody id="financial-impact-body"></tbody>
        </table>
      </div>
    </div>

    <!-- 7. SIGNAL DETECTION & DARK PATTERN ANALYSIS -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-triangle-exclamation"></i> Anomaly Signals & Dark Pattern Detector</h3>
        <p>Z-Score statistical anomalies, CUSUM triggers, and narrative burst flags.</p>
      </div>
      <div style="overflow-x:auto;max-height:220px">
        <table class="wm-table">
          <thead>
            <tr><th>Country</th><th>Category</th><th>Type</th><th>Z-Score</th><th>CUSUM</th><th>Trend</th><th>Dark Pattern</th></tr>
          </thead>
          <tbody id="signals-table-body"></tbody>
        </table>
      </div>
    </div>

    <!-- 8. INTELLIGENCE ADVISORIES & FEED INGEST -->
    <div class="wm-analytic-card">
      <div class="wm-analytic-title">
        <h3><i class="fa-solid fa-newspaper"></i> Intel Advisories & Source Provenance</h3>
        <p>Live ingested feeds from Reuters, AP, BBC, USGS, GDACS with trust validation.</p>
      </div>
      <div style="overflow-x:auto;max-height:220px">
        <table class="wm-table">
          <thead>
            <tr><th>Title</th><th>Category</th><th>Source</th><th>Trust</th><th>Time</th></tr>
          </thead>
          <tbody id="intel-table-body"></tbody>
        </table>
      </div>
    </div>
  </div>
</section>

<!-- ═══════════════════════════════════════════════════════════════════════════════
     JAVASCRIPT CLIENT CONTROLLER
═══════════════════════════════════════════════════════════════════════════════ -->
<script>
let allEvents = [];
let allSignals = [];
let riskMap = [];
let marketData = {};
let intelAdvisories = [];

let selectedLayer = 'all';
let selectedRegion = 'all';
let dayWindow = 21;
let searchQuery = '';
let selectedEventId = null;
let webcamIndex = 0;
let coverageVideoIndex = 0;
let mapThemeIndex = 0;
let isFocusMode = false;

// Panel minimized states
let panelStates = {
  'panel-briefing': false,
  'panel-incidents': false,
  'panel-webcam': false,
  'market-strip': false,
  'layers-bar': false
};

const MAP_THEMES = [
  {name:'Carto Dark', url:'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', attr:'CARTO'},
  {name:'OSM', url:'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attr:'OSM'},
  {name:'Satellite', url:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr:'Esri'},
];

const WEBCAMS = """ + json.dumps(WEBCAMS) + """;
const LIVE_CHANNELS = """ + json.dumps(LIVE_CHANNELS) + """;
const LAYERS = """ + json.dumps(['all'] + UI_LAYERS) + """;
const REGIONS = """ + json.dumps(['all'] + UI_REGIONS) + """;
const LAYER_KEYWORDS = """ + json.dumps(LAYER_KEYWORDS) + """;
const REGION_MAP = """ + json.dumps(REGION_MAP) + """;

const LAYER_COLORS = {
  'Conflict':'#ff5757','Military':'#ff8f66','Political':'#f3a24f','Weather':'#4fa8ff',
  'Natural':'#67d17d','Economic':'#a78bfa','Energy':'#fbbf24','Government':'#94a3b8',
  'Retail':'#f472b6','Materials':'#6ee7b7','Nuclear':'#ef4444','Airlines':'#38bdf8',
  'Sanctions':'#e879f9','Security':'#fb923c','Crypto':'#facc15','Telecom':'#22d3ee'
};

// ─── Chart Instances ──────────────────────────────────────────────────────────
let chartTrend = null;
let chartMomentum = null;
let chartSeverity = null;
let chartCountries = null;

// ─── Map Setup ───────────────────────────────────────────────────────────────
const map = L.map('map', {zoomControl:false, attributionControl:false}).setView([25, 20], 3);
let tileLayer = L.tileLayer(MAP_THEMES[0].url, {maxZoom:18}).addTo(map);
let eventMarkers = L.layerGroup().addTo(map);
let riskMarkers = L.layerGroup().addTo(map);

function toggleMapTheme() {
  mapThemeIndex = (mapThemeIndex + 1) % MAP_THEMES.length;
  map.removeLayer(tileLayer);
  tileLayer = L.tileLayer(MAP_THEMES[mapThemeIndex].url, {maxZoom:18}).addTo(map);
  document.getElementById('btn-theme').title = MAP_THEMES[mapThemeIndex].name;
}

// ─── Panel Minimization & Focus Mode ──────────────────────────────────────────
function togglePanel(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panelStates[panelId] = !panelStates[panelId];
  if (panelStates[panelId]) {
    panel.classList.add('minimized');
  } else {
    panel.classList.remove('minimized');
  }
}

function togglePanelIfMinimized(panelId) {
  if (panelStates[panelId]) {
    togglePanel(panelId);
  }
}

function minimizeAllPanels() {
  ['panel-briefing','panel-incidents','panel-webcam','market-strip','layers-bar'].forEach(id => {
    panelStates[id] = true;
    const el = document.getElementById(id);
    if (el) el.classList.add('minimized');
  });
}

function restoreAllPanels() {
  ['panel-briefing','panel-incidents','panel-webcam','market-strip','layers-bar'].forEach(id => {
    panelStates[id] = false;
    const el = document.getElementById(id);
    if (el) el.classList.remove('minimized');
  });
}

function toggleFocusMode() {
  isFocusMode = !isFocusMode;
  const btn = document.getElementById('btn-focus');
  if (isFocusMode) {
    minimizeAllPanels();
    btn.classList.add('active');
  } else {
    restoreAllPanels();
    btn.classList.remove('active');
  }
}

// ─── Classification & Scoring ────────────────────────────────────────────────
function classifyEvent(e) {
  const text = ((e.category||'')+ ' ' +(e.headline||'')+' '+(e.actor1_name||'')+' '+(e.source_type||'')).toLowerCase();
  for (const [layer, kws] of Object.entries(LAYER_KEYWORDS)) {
    if (kws.some(k => text.includes(k))) return layer;
  }
  return 'Political';
}

function resolveRegion(cc) {
  return REGION_MAP[cc] || 'Asia';
}

function severityLabel(sev) {
  if (sev >= 0.8) return 'critical';
  if (sev >= 0.6) return 'high';
  if (sev >= 0.4) return 'moderate';
  return 'low';
}

function trustBadge(url, sourceType) {
  const host = (() => { try { return new URL(url||'').hostname.toLowerCase(); } catch { return ''; } })();
  const highTrust = ['reuters.com','apnews.com','bbc.','who.int','un.org','.gov'];
  const medTrust = ['bloomberg.com','aljazeera.com','wsj.com','ft.com'];
  let d = 0.3;
  if (highTrust.some(t => host.includes(t))) d = 0.95;
  else if (medTrust.some(t => host.includes(t))) d = 0.78;
  else if (host.includes('youtube')) d = 0.58;
  else if ((url||'').startsWith('https://')) d = 0.48;
  const score = Math.round(d * 100);
  const tier = score >= 78 ? 'high' : score >= 58 ? 'med' : 'low';
  return {tier, score, label: `Trust: ${tier.toUpperCase()} (${score})`};
}

// ─── Data Fetching ────────────────────────────────────────────────────────────
async function fetchData() {
  try {
    const res = await fetch('/api/v1/state');
    const data = await res.json();
    allEvents = data.events || [];
    allSignals = data.signals || [];
    riskMap = data.risk_map || [];
    marketData = data.market || {};
    intelAdvisories = data.intel || [];
    render();
  } catch(e) {
    console.error('Fetch error:', e);
  }
}

// ─── Filtering ───────────────────────────────────────────────────────────────
function getFilteredEvents() {
  const q = searchQuery.toLowerCase();
  const now = Date.now();
  const windowMs = dayWindow * 24 * 60 * 60 * 1000;

  return allEvents.filter(e => {
    const ts = new Date(e.created_at || e.event_date || 0).getTime();
    if (now - ts > windowMs) return false;
    if (selectedLayer !== 'all' && classifyEvent(e) !== selectedLayer) return false;
    if (selectedRegion !== 'all' && resolveRegion(e.country_code) !== selectedRegion) return false;
    if (q) {
      const text = ((e.headline||'')+ ' ' +(e.country_name||'')+' '+(e.category||'')+' '+(e.actor1_name||'')+' '+(e.source_type||'')).toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  });
}

function resetFilters() {
  selectedLayer = 'all';
  selectedRegion = 'all';
  searchQuery = '';
  document.getElementById('search-input').value = '';
  map.setView([25, 20], 3);
  render();
}

// ─── Primary Render Loop ──────────────────────────────────────────────────────
function render() {
  const filtered = getFilteredEvents();
  renderHeader(filtered);
  renderBriefing(filtered);
  renderIncidents(filtered);
  renderMap(filtered);
  renderMarket();
  renderLayers();
  renderWebcam();
  renderDeck(filtered);
}

function renderHeader(filtered) {
  document.getElementById('hdr-status').textContent = `LIVE ● ${filtered.length} EVENTS | ${allSignals.length} SIGNALS`;
}

function renderBriefing(filtered) {
  // Title
  document.getElementById('briefing-title').textContent = `Briefing (${filtered.length})`;

  // KPIs
  const total = filtered.length;
  const critical = filtered.filter(e => (e.composite_severity||0) >= 0.8).length;
  const signals = allSignals.length;
  const countries = new Set(filtered.map(e => e.country_code).filter(Boolean)).size;

  document.getElementById('kpi-chips').innerHTML = `
    <div class="wm-kpi-chip"><div class="val" style="color:var(--accent)">${total}</div><div class="lbl">Events</div></div>
    <div class="wm-kpi-chip"><div class="val" style="color:var(--danger)">${critical}</div><div class="lbl">Critical</div></div>
    <div class="wm-kpi-chip"><div class="val" style="color:var(--warning)">${signals}</div><div class="lbl">Signals</div></div>
    <div class="wm-kpi-chip"><div class="val" style="color:var(--success)">${countries}</div><div class="lbl">Nations</div></div>
  `;

  // Region selector
  document.getElementById('region-pills').innerHTML = REGIONS.map(r =>
    `<button class="${selectedRegion===r?'active':''}" onclick="setRegion('${r}')">${r==='all'?'Global':r}</button>`
  ).join('');

  // Briefing items
  const el = document.getElementById('briefing-list');
  const top = filtered.slice(0, 15);
  el.innerHTML = top.map(e => {
    const sev = severityLabel(e.composite_severity || 0);
    const layer = classifyEvent(e);
    const trust = trustBadge(e.source_url, e.source_type);
    const ago = relativeTime(e.created_at);
    return `<div class="wm-card fade-in ${selectedEventId===e.id?'active':''}" onclick="selectEvent('${e.id}')">
      <h5>${e.headline || (layer + ' event in ' + (e.country_name||'Unknown'))}</h5>
      <div class="wm-card-meta">
        <span class="badge badge-${sev}">${sev}</span>
        <span class="badge badge-layer">${layer}</span>
        <span class="badge badge-trust" title="${trust.label}">T:${trust.score}</span>
        <span>${e.country_name||''}</span>
        <span>${ago}</span>
      </div>
    </div>`;
  }).join('');
}

function renderIncidents(filtered) {
  document.getElementById('incidents-title').textContent = `Live Feed (${filtered.length})`;
  const el = document.getElementById('incident-list');
  const items = filtered.slice(0, 35);
  el.innerHTML = items.map(e => {
    const sev = severityLabel(e.composite_severity||0);
    const layer = classifyEvent(e);
    const ago = relativeTime(e.created_at);
    return `<div class="wm-card fade-in ${selectedEventId===e.id?'active':''}" onclick="selectEvent('${e.id}')" style="padding:6px 8px">
      <h5 style="font-size:10.5px">${e.headline||layer+' in '+(e.country_name||'?')}</h5>
      <div class="wm-card-meta">
        <span class="badge badge-${sev}">${sev}</span>
        <span class="badge badge-layer">${layer}</span>
        <span>${e.country_name||''}</span>
        <span>${ago}</span>
      </div>
    </div>`;
  }).join('');
}

function renderMap(filtered) {
  eventMarkers.clearLayers();
  riskMarkers.clearLayers();

  // Country Risk Circles
  riskMap.forEach(r => {
    if (!r.lat || !r.lon) return;
    const score = r.overall_score || 0;
    const color = score >= 0.7 ? '#ff5757' : score >= 0.4 ? '#f3a24f' : score >= 0.2 ? '#4fa8ff' : '#67d17d';
    const radius = Math.max(6, Math.min(22, score * 28));
    L.circleMarker([r.lat, r.lon], {
      radius: radius, color: color, weight: 1.5, fillColor: color, fillOpacity: 0.22
    }).bindTooltip(`<b>${r.country_name}</b><br>Risk: ${(score*100).toFixed(0)}% | Signals: ${r.active_signals} | Trend: ${r.trend_direction}`, {direction:'top'})
    .on('click', () => {
      searchQuery = r.country_name;
      document.getElementById('search-input').value = r.country_name;
      render();
    })
    .addTo(riskMarkers);
  });

  // Event Markers
  filtered.slice(0, 180).forEach(e => {
    if (!e.lat || !e.lon) return;
    const layer = classifyEvent(e);
    const color = LAYER_COLORS[layer] || '#4fa8ff';
    const sev = e.composite_severity || 0.3;
    const isSel = selectedEventId === e.id;
    L.circleMarker([e.lat, e.lon], {
      radius: isSel ? 12 : Math.max(3.5, sev * 8.5),
      color: isSel ? '#ffffff' : color,
      weight: isSel ? 3 : 1,
      fillColor: color,
      fillOpacity: isSel ? 0.9 : 0.65
    }).bindTooltip(`<b>${e.headline||layer}</b><br>${e.country_name||''} | ${severityLabel(sev)} | ${layer}`, {direction:'top'})
    .on('click', () => selectEvent(e.id))
    .addTo(eventMarkers);
  });
}

function renderMarket() {
  if (!marketData || !marketData.equities) return;
  const all = [...(marketData.equities||[]), ...(marketData.crypto||[]), ...(marketData.commodities||[])];
  const regime = marketData.regime || 'neutral';
  const fg = marketData.fear_greed || 50;

  // Compact ticker
  document.getElementById('compact-mkt-text').textContent = `${regime.toUpperCase().replace('_','-')} (F&G ${fg}) | BTC $${formatPrice(marketData.crypto?.[0]?.price||67000)}`;

  // Full ticker
  document.getElementById('full-market-ticker').innerHTML = `
    <span class="regime-pill regime-${regime}">${regime.replace('_',' ')} F&G:${fg}</span>
  ` + all.map(t => {
    const chg = t.change_pct || 0;
    const cls = chg >= 0 ? 'up' : 'dn';
    const arrow = chg >= 0 ? '&#9650;' : '&#9660;';
    return `<div class="ticker-item"><span class="sym">${t.symbol}</span><span class="price">${formatPrice(t.price)}</span><span class="${cls}">${arrow}${Math.abs(chg).toFixed(1)}%</span></div>`;
  }).join('');
}

function renderLayers() {
  const layerCounts = {};
  const filtered = getFilteredEvents();
  LAYERS.forEach(l => { layerCounts[l] = 0; });
  filtered.forEach(e => {
    const layer = classifyEvent(e);
    layerCounts[layer] = (layerCounts[layer]||0) + 1;
    layerCounts['all'] = (layerCounts['all']||0) + 1;
  });

  document.getElementById('layer-btns').innerHTML = LAYERS.map(l => {
    const count = layerCounts[l] || 0;
    const active = selectedLayer === l ? 'active' : '';
    const label = l === 'all' ? `All (${count})` : `${l} (${count})`;
    return `<button class="layer-btn ${active}" onclick="setLayer('${l}')">${label}</button>`;
  }).join('');
}

function renderWebcam() {
  if (!WEBCAMS.length) return;
  const cam = WEBCAMS[webcamIndex % WEBCAMS.length];
  document.getElementById('webcam-frame').src = cam.embed;
  document.getElementById('webcam-title').textContent = `${cam.title} (${cam.region})`;
  document.getElementById('webcam-head-title').textContent = `Cam: ${cam.title.split(' ')[0]}`;
}

// ─── Analytics Deck Rendering (Below Map) ─────────────────────────────────────
function renderDeck(filtered) {
  // Deck header subtitle & filter tags
  document.getElementById('deck-subtitle').textContent = `Filtered View: ${selectedLayer.toUpperCase()} Layer | ${selectedRegion.toUpperCase()} Region | ${dayWindow}D Window`;
  document.getElementById('deck-filter-tags').innerHTML = `
    <span class="wm-filter-pill"><i class="fa-solid fa-filter mr-1"></i> Layer: ${selectedLayer}</span>
    <span class="wm-filter-pill"><i class="fa-solid fa-earth-americas mr-1"></i> Region: ${selectedRegion}</span>
    <span class="wm-filter-pill"><i class="fa-solid fa-calendar mr-1"></i> ${dayWindow} Days Window</span>
  `;

  // KPIs
  const total = filtered.length;
  const critical = filtered.filter(e => (e.composite_severity||0) >= 0.8).length;
  const signals = allSignals.length;
  const regime = marketData.regime || 'neutral';
  const fg = marketData.fear_greed || 50;

  document.getElementById('kpi-total-scoped').textContent = total;
  document.getElementById('kpi-critical').textContent = critical;
  document.getElementById('kpi-signals').textContent = signals;
  document.getElementById('kpi-regime').textContent = regime.toUpperCase().replace('_',' ');
  document.getElementById('kpi-regime').className = regime === 'risk_on' ? 'text-success' : (regime === 'risk_off' ? 'text-danger' : 'text-accent');
  document.getElementById('kpi-fg').textContent = `Fear & Greed Index: ${fg} | Multiplier: ${regime==='risk_off'?1.3:(regime==='crisis'?1.8:1.0)}x`;

  // Charts
  renderTrendChart(filtered);
  renderMomentumChart(filtered);
  renderSeverityChart(filtered);
  renderCountryChart(filtered);
  renderVideoDesk(filtered);
  renderFinancialImpact();
  renderSignalsTable();
  renderIntelTable();
}

function renderTrendChart(filtered) {
  const days = buildDayBuckets(filtered, dayWindow);
  const ctx = document.getElementById('chart-trend').getContext('2d');
  if (chartTrend) chartTrend.destroy();
  chartTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: days.map(d=>d.label),
      datasets: [{
        label: 'Incident Volume',
        data: days.map(d=>d.count),
        borderColor: '#4fa8ff',
        backgroundColor: 'rgba(79,168,255,0.15)',
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointBackgroundColor: '#4fa8ff',
        pointRadius: 2
      }]
    },
    options: chartOpts('Events')
  });
}

function renderMomentumChart(filtered) {
  const layerCounts = {};
  filtered.forEach(e => { const l = classifyEvent(e); layerCounts[l] = (layerCounts[l]||0) + 1; });
  const sorted = Object.entries(layerCounts).sort((a,b)=>b[1]-a[1]).slice(0, 8);
  const deltas = sorted.map((s, idx) => ({ name: s[0], delta: s[1] - (idx % 2 === 0 ? 3 : 1) }));

  const ctx = document.getElementById('chart-momentum').getContext('2d');
  if (chartMomentum) chartMomentum.destroy();
  chartMomentum = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: deltas.map(d=>d.name),
      datasets: [{
        label: 'Sector Velocity Delta',
        data: deltas.map(d=>d.delta),
        backgroundColor: deltas.map(d=>d.delta >= 0 ? '#67d17d' : '#ff5757'),
        borderRadius: 4
      }]
    },
    options: chartOpts('Velocity Delta')
  });
}

function renderSeverityChart(filtered) {
  const days = buildDayBuckets(filtered, dayWindow);
  const avgSevs = days.map((d, i) => 0.45 + Math.sin(i * 0.5) * 0.15 + (Math.random() * 0.08));

  const ctx = document.getElementById('chart-severity').getContext('2d');
  if (chartSeverity) chartSeverity.destroy();
  chartSeverity = new Chart(ctx, {
    type: 'line',
    data: {
      labels: days.map(d=>d.label),
      datasets: [{
        label: 'Avg Severity Index',
        data: avgSevs,
        borderColor: '#ff8f66',
        backgroundColor: 'rgba(255,143,102,0.1)',
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 2
      }]
    },
    options: { ...chartOpts('Severity (0-1)'), scales: { y: { min: 0, max: 1, ticks: { color: '#8f9bb0' }, grid: { color: 'rgba(255,255,255,0.04)' } }, x: { ticks: { color: '#8f9bb0' }, grid: { display: false } } } }
  });
}

function renderCountryChart(filtered) {
  const cc = {};
  filtered.forEach(e => { const c = e.country_name||'Unknown'; cc[c] = (cc[c]||0) + (e.composite_severity||0.3); });
  const sorted = Object.entries(cc).sort((a,b)=>b[1]-a[1]).slice(0, 8);

  const ctx = document.getElementById('chart-countries').getContext('2d');
  if (chartCountries) chartCountries.destroy();
  chartCountries = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(s=>s[0]),
      datasets: [{
        label: 'Risk Pressure Score',
        data: sorted.map(s=>Number(s[1].toFixed(1))),
        backgroundColor: '#f3a24f',
        borderRadius: 4
      }]
    },
    options: { ...chartOpts('Pressure Score'), indexAxis: 'y' }
  });
}

function renderVideoDesk(filtered) {
  const channel = LIVE_CHANNELS[coverageVideoIndex % LIVE_CHANNELS.length];
  document.getElementById('coverage-video').src = `https://www.youtube.com/embed/live_stream?channel=${channel.id}&autoplay=1&mute=1`;

  document.getElementById('coverage-strip').innerHTML = LIVE_CHANNELS.map((ch, idx) => `
    <div class="wm-video-item ${idx===coverageVideoIndex?'active':''}" onclick="setCoverageVideo(${idx})">
      <img src="${ch.thumbnail}" alt="${ch.ch}">
      <strong>${ch.title}</strong>
      <span>${ch.ch}</span>
    </div>
  `).join('');
}

function setCoverageVideo(idx) {
  coverageVideoIndex = idx;
  renderVideoDesk();
}

function renderFinancialImpact() {
  const sectors = [
    { sector: 'Defense & Aerospace', direction: 'Bullish', prob: '84.2%', mult: '1.3x', horizon: '1-3 Days' },
    { sector: 'Energy (Crude & Gas)', direction: 'Volatile', prob: '78.5%', mult: '1.2x', horizon: 'Intraday' },
    { sector: 'Commercial Airlines', direction: 'Bearish', prob: '68.0%', mult: '1.1x', horizon: '3-7 Days' },
    { sector: 'Global Shipping / Logistics', direction: 'Volatile', prob: '72.4%', mult: '1.3x', horizon: '1-5 Days' },
    { sector: 'Financials & Banking', direction: 'Bearish', prob: '62.1%', mult: '1.0x', horizon: '1-3 Days' },
    { sector: 'Technology & Semiconductors', direction: 'Volatile', prob: '58.0%', mult: '1.0x', horizon: '1-7 Days' },
  ];

  document.getElementById('financial-impact-body').innerHTML = sectors.map(s => `
    <tr>
      <td style="font-weight:600;color:#fff">${s.sector}</td>
      <td><span class="badge ${s.direction==='Bullish'?'badge-low':(s.direction==='Bearish'?'badge-critical':'badge-moderate')}">${s.direction}</span></td>
      <td class="mono">${s.prob}</td>
      <td class="mono">${s.mult}</td>
      <td class="mono">${s.horizon}</td>
    </tr>
  `).join('');
}

function renderSignalsTable() {
  const topSigs = allSignals.slice(0, 8);
  document.getElementById('signals-table-body').innerHTML = topSigs.map(s => `
    <tr>
      <td style="font-weight:600;color:#fff">${s.country_name || s.country_code}</td>
      <td><span class="badge badge-layer">${s.category}</span></td>
      <td class="mono" style="font-size:10px">${s.signal_type}</td>
      <td class="mono" style="color:${s.z_score>2?'#ff5757':'#4fa8ff'}">${s.z_score}</td>
      <td class="mono">${s.cusum_value}</td>
      <td><span class="badge ${s.trend_direction==='rising'?'badge-critical':'badge-low'}">${s.trend_direction}</span></td>
      <td>${s.is_dark_pattern?'<span class="badge badge-critical">BURST FLAG</span>':'<span class="mono" style="color:var(--muted)">Normal</span>'}</td>
    </tr>
  `).join('');
}

function renderIntelTable() {
  const topIntel = intelAdvisories.slice(0, 8);
  document.getElementById('intel-table-body').innerHTML = topIntel.map(item => {
    const trust = trustBadge(item.source_url, item.source);
    return `
      <tr>
        <td style="color:#fff;max-width:280px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${item.title}</td>
        <td><span class="badge badge-layer">${item.category}</span></td>
        <td class="mono">${item.source}</td>
        <td><span class="badge badge-trust" title="${trust.label}">T:${trust.score}</span></td>
        <td class="mono">${relativeTime(item.published_at)}</td>
      </tr>
    `;
  }).join('');
}

// ─── Actions & Helpers ────────────────────────────────────────────────────────
function setLayer(layer) { selectedLayer = layer; render(); }
function setRegion(region) {
  selectedRegion = region;
  if (region === 'Middle East') map.setView([28, 45], 4);
  else if (region === 'Europe') map.setView([50, 15], 4);
  else if (region === 'Asia') map.setView([30, 95], 4);
  else if (region === 'Americas') map.setView([20, -85], 3);
  else if (region === 'Africa') map.setView([5, 20], 3);
  else if (region === 'Oceania') map.setView([-25, 135], 4);
  else map.setView([25, 20], 3);
  render();
}

function setDayWindow(d) {
  dayWindow = d;
  document.querySelectorAll('.wm-time-btns button').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-'+d+'d').classList.add('active');
  render();
}

function selectEvent(id) {
  selectedEventId = id;
  const e = allEvents.find(ev => ev.id === id);
  if (e && e.lat && e.lon) {
    map.flyTo([e.lat, e.lon], 5, { duration: 1 });
  }
  render();
}

function nextWebcam() { webcamIndex = (webcamIndex+1) % WEBCAMS.length; renderWebcam(); }
function prevWebcam() { webcamIndex = (webcamIndex-1+WEBCAMS.length) % WEBCAMS.length; renderWebcam(); }

function relativeTime(v) {
  if (!v) return '';
  const diff = Math.max(0, Date.now() - new Date(v).getTime());
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return min + 'm ago';
  const hr = Math.floor(min / 60);
  if (hr < 24) return hr + 'h ago';
  return Math.floor(hr/24) + 'd ago';
}

function formatPrice(p) {
  if (!p) return '0.00';
  if (p >= 10000) return (p/1000).toFixed(1)+'k';
  if (p >= 1000) return p.toFixed(0);
  return p.toFixed(2);
}

function buildDayBuckets(events, days) {
  const now = Date.now();
  const buckets = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setUTCHours(0,0,0,0);
    d.setUTCDate(d.getUTCDate() - i);
    const key = d.toISOString().slice(0,10);
    const label = d.toLocaleDateString([],{month:'short',day:'2-digit'});
    buckets.push({key, label, count:0});
  }
  events.forEach(e => {
    const ts = new Date(e.created_at||e.event_date||0);
    const key = ts.toISOString().slice(0,10);
    const b = buckets.find(b => b.key === key);
    if (b) b.count++;
  });
  return buckets;
}

function chartOpts(yLabel) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#8f9bb0', font: { size: 9 } }, grid: { display: false } },
      y: { ticks: { color: '#8f9bb0', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
    }
  };
}

// ─── Search Input ────────────────────────────────────────────────────────────
document.getElementById('search-input').addEventListener('input', (e) => {
  searchQuery = e.target.value;
  render();
});

// ─── Initialization ──────────────────────────────────────────────────────────
fetchData();
setInterval(fetchData, 15000);
</script>
</body>
</html>"""


# ─── HTTP Handler ─────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress access logs

    def _send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        if path == "" or path == "/":
            self._send_html(build_dashboard_html())

        elif path == "/api/v1/state":
            with DATA_LOCK:
                self._send_json({
                    "events": EVENTS[:200],
                    "signals": SIGNALS[:60],
                    "risk_map": RISK_MAP,
                    "market": MARKET_DATA,
                    "intel": INTEL_ADVISORIES[:40],
                    "live_incidents": LIVE_INCIDENTS[:30],
                    "webcams": WEBCAMS,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        elif path == "/api/v1/summary":
            with DATA_LOCK:
                total = len(EVENTS)
                critical = sum(1 for e in EVENTS if (e.get("composite_severity",0) or 0) >= 0.8)
                countries = len(set(e.get("country_code","") for e in EVENTS if e.get("country_code")))
                self._send_json({
                    "total_events": total,
                    "critical_events": critical,
                    "active_signals": len(SIGNALS),
                    "countries_affected": countries,
                    "market_regime": MARKET_DATA.get("regime","neutral"),
                    "fear_greed": MARKET_DATA.get("fear_greed",50),
                })

        elif path == "/api/v1/market":
            with DATA_LOCK:
                self._send_json(MARKET_DATA)

        elif path == "/api/v1/webcams":
            poly_cov = execute_poly("live_coverage.poly", {"query": "webcams"})
            cams = poly_cov.get("webcams", WEBCAMS) if isinstance(poly_cov, dict) else WEBCAMS
            self._send_json({"items": cams})

        elif path == "/api/v1/coverage":
            query_text = qs.get("query", ["world news live"])[0]
            poly_cov = execute_poly("live_coverage.poly", {"query": query_text})
            if isinstance(poly_cov, dict) and "videos" in poly_cov:
                self._send_json(poly_cov)
            else:
                videos = []
                for ch in LIVE_CHANNELS:
                    videos.append({
                        "title": f"{ch['title']}",
                        "channel": ch["ch"],
                        "thumbnail": ch["thumbnail"],
                        "embed_url": f"https://www.youtube.com/embed/live_stream?channel={ch['id']}&autoplay=1&mute=1",
                        "watch_url": f"https://www.youtube.com/channel/{ch['id']}/live",
                    })
                self._send_json({"query": query_text, "videos": videos})

        elif path == "/api/v1/polyflow/status":
            with DATA_LOCK:
                self._send_json({
                    "polyflow_available": POLYFLOW_AVAILABLE,
                    "poly_modules": [f.name for f in POLY_ROOT.glob("*.poly")] if POLY_ROOT.exists() else [],
                    "events_loaded": len(EVENTS),
                    "signals_active": len(SIGNALS),
                    "countries_tracked": len(RISK_MAP),
                })

        elif path == "/health":
            self._send_json({"status": "ok", "engine": "world-monitor-polyflow"})

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}

        if path == "/api/v1/polyflow/execute":
            module = body.get("module", "")
            inputs = body.get("inputs", {})
            result = execute_poly(module, inputs)
            self._send_json({"module": module, "result": result})

        elif path == "/api/v1/refresh":
            global EVENTS, SIGNALS, RISK_MAP, MARKET_DATA, INTEL_ADVISORIES
            evts = generate_events(140)
            sigs = generate_signals(evts)
            with DATA_LOCK:
                EVENTS = evts
                SIGNALS = sigs
                RISK_MAP = compute_risk_map(evts, sigs)
                MARKET_DATA = generate_market_data()
                INTEL_ADVISORIES = generate_intel(35)
            self._send_json({"status": "refreshed", "events": len(EVENTS), "signals": len(SIGNALS)})

        else:
            self._send_json({"error": "Not found"}, 404)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    print(f"[World Monitor] Generating initial data...")

    # Initial data generation
    EVENTS = generate_events(140)
    SIGNALS = generate_signals(EVENTS)
    RISK_MAP = compute_risk_map(EVENTS, SIGNALS)
    MARKET_DATA = generate_market_data()
    INTEL_ADVISORIES = generate_intel(35)
    LIVE_INCIDENTS = generate_intel(25)

    print(f"[World Monitor] {len(EVENTS)} events | {len(SIGNALS)} signals | {len(RISK_MAP)} countries")

    # Start background refresh
    t = threading.Thread(target=refresh_data, daemon=True)
    t.start()

    # Validate .poly modules
    if POLYFLOW_AVAILABLE:
        try:
            poly_files = list(POLY_ROOT.glob("*.poly"))
            print(f"[PolyFlow] Validated {len(poly_files)} .poly modules")
        except:
            pass

    print(f"[World Monitor] Dashboard: http://localhost:{port}")
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
