# World Monitor — PolyFlow Polyglot Intelligence Platform

Real-time geopolitical intelligence, risk mapping, and financial signal detection powered by **multi-language PolyFlow `.poly` modules**.

## Polyglot Architecture

Each feature module is implemented in multiple languages (Python, Go, TypeScript, Java, Rust, SQL) with `@contract`, `@schema`, and `@merge` strategies:

```
world-monitor/
  engine.py                          # Thin server & REST orchestrator (delegates all logic to .poly files)
  features/
    geopolitical_events.poly         # [Python, Go, TypeScript, Java] - Event classification & regional taxonomy
    signal_detection.poly            # [Python, Go, Rust, TypeScript] - Anscombe transform, Z-score, CUSUM detection
    financial_intelligence.poly      # [Python, Go, Java, TypeScript] - Sector transmission & regime multipliers
    country_risk.poly                # [Python, Go, SQL, Rust] - Geospatial composite risk & spatial clustering
    trust_scoring.poly               # [Python, TypeScript, Go, Java] - Domain trust & exponential recency decay
    market_data.poly                 # [Python, Go, TypeScript] - Real-time market ticker & volatility analysis
    intel_ingest.poly                # [Python, Go, Java] - Multi-feed ingestion & entity location enrichment
    live_coverage.poly               # [Python, TypeScript, Go] - Live video stream resolution & webcam registry
  README.md
```

## Language Matrix

| Module (`.poly`) | Languages Implemented | Primary Responsibilities |
|---|---|---|
| `geopolitical_events.poly` | **Python, Go, TypeScript, Java** | 16 layer classifications, keyword vector matching, 6 region mappings |
| `signal_detection.poly` | **Python, Go, Rust, TypeScript** | Anscombe variance-stabilizing transform, Z-score anomalies, CUSUM accumulation |
| `financial_intelligence.poly` | **Python, Go, Java, TypeScript** | Sector impact mapping, macro regime multipliers (Risk-On/Risk-Off/Crisis) |
| `country_risk.poly` | **Python, Go, SQL, Rust** | 37-nation geospatial risk indexing, Haversine spatial clustering, SQL view schemas |
| `trust_scoring.poly` | **Python, TypeScript, Go, Java** | Domain authority scoring, exponential recency decay, multi-source corroboration |
| `market_data.poly` | **Python, Go, TypeScript** | Ticker price synthesis, Fear & Greed index, orderbook volatility |
| `intel_ingest.poly` | **Python, Go, Java** | RSS, GDACS, USGS entity normalization and severity ranking |
| `live_coverage.poly` | **Python, TypeScript, Go** | YouTube live news stream ranking, embed URL resolution, global webcam registry |

## Quick Start

```bash
# Validate all .poly modules with PolyFlow guards & governance
python -m polyflow validate world-monitor/features

# Run the World Monitor engine
python world-monitor/engine.py 8888

# Open http://localhost:8888 in browser
```

## Features

- **Full-viewport Leaflet Map Stage** with Carto Dark / OSM / Satellite tile layers.
- **Minimizable Floating Panels**:
  - `Intelligence Briefing` (left): Minimizable to compact floating pill `📡 Briefing (140)`.
  - `Live Incidents Feed` (right): Minimizable to compact floating pill `⚡ Live Feed (140)`.
  - `Market Ticker Strip`: Draggable & minimizable to compact badge `📈 Market: RISK-ON | BTC $67.4k`.
  - `Webcam Panel`: Draggable & minimizable with global CCTV feeds.
  - `Layer Selector Bar`: Minimizable bottom pill selector with 16 categories.
- **Quick Action Controls**:
  - `Focus Mode`: Hides all overlays for a 100% unobstructed full-screen map.
  - `Minimize All`: Collapses all floating panels to compact tabs.
  - `Restore All`: Expands all panels back to full view.
  - `1D / 7D / 21D`: Instant time window recalculation.
- **Situation Room Analytics Deck (Scroll Down)**:
  - 4 Executive KPI Cards (Total Scoped Events, Critical Threats, Anomaly Signals, Market Regime).
  - 8 Interactive Analytics Cards:
    1. Incident Trend & Velocity (Line & Area chart over 1d/7d/21d)
    2. Category Momentum (Delta velocity bar chart)
    3. Severity Escalation Curve (Line chart)
    4. Top Country Risk Pressure (Horizontal ranking bar chart)
    5. Live Coverage Video Desk (Interactive player + playlist strip)
    6. Financial Intelligence & Sector Impact Matrix
    7. Signal Detection & Dark Pattern Anomaly Table
    8. Intel Advisories & Source Provenance Feed Table
