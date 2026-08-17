# UrbanOS v2 — Live Urban Operations Platform

> Pure PolyFlow Native Architecture | 12 Total Files | Zero Boilerplate

## What is UrbanOS?

UrbanOS is a **real-time digital twin and urban operations platform** that ingests live transportation, weather, environmental, and video data, combines it with a simulated city, performs real-time analytics and prediction, and renders the resulting city state live to operators.

Built entirely on **Pure PolyFlow `.poly` native architecture** — every feature is a single consolidated `.poly` module executed in-memory in sub-milliseconds.

## Architecture

```
urbanos/
├── engine.py                      # Server + API + UI + All Adapters
├── features/
│   ├── traffic_core.poly          # Traffic ingestion, speed, congestion
│   ├── weather_env.poly           # Weather + Air Quality + Correlation
│   ├── transit_mobility.poly      # Public transit, bus positions, ETAs
│   ├── camera_vision.poly         # Camera AI detection metadata
│   ├── simulation_engine.poly     # In-memory traffic simulation (SUMO-equiv)
│   ├── digital_twin.poly          # City state machine
│   ├── prediction_ai.poly         # ML predictions (congestion, incidents)
│   ├── incident_ops.poly          # Incident detection, severity, clearance
│   ├── data_fabric.poly           # Source registry, feed health
│   └── polyflow_observe.poly      # PolyFlow change-impact analysis
└── README.md
```

**Total: 12 files | 10 .poly modules | 0 standalone code files**

## Run

```bash
python urbanos/engine.py 8080
```

Open: http://localhost:8080

## Live Data Sources

| Source | Type | API |
|--------|------|-----|
| Weather | Live | Open-Meteo (no key) |
| Air Quality | Live | WAQI/OpenAQ |
| Traffic Cameras | Live | YouTube livestreams |
| Maps | Live | Google Maps JS |
| Traffic | Simulation | PolyFlow-Native TrafficSim |
| Transit | Simulation | GTFS-RT style |

## Features

- **Live City Map** (Google Maps with dark theme, real-time markers)
- **Traffic Intelligence** (road segment states, congestion scoring)
- **Live Camera Feeds** (embedded YouTube traffic camera streams)
- **Weather & Air Quality** (with traffic impact correlation)
- **Public Transit Tracker** (bus positions, routes, ETAs)
- **Incident Detection** (inject incidents, see city react)
- **Data Source Health** (freshness indicators, latency tracking)
- **PolyFlow Change-Impact** (trace code changes through dependency graph)
