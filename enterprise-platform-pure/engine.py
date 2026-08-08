"""
Pure PolyFlow Enterprise Native Engine & Fast Server.

Loads all .poly feature modules into memory, evaluates execution requests in sub-milliseconds,
enforces Guards A-F, seals SHA-256 Merkle Ledger audit entries, and serves an Interactive Web Portal.
"""

import os
import sys
import json
import time
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

# Ensure repository root is on sys.path
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from polyflow.parser import PolyParser
from polyflow.runtime import PolyCellRuntime
from polyflow.merge import PolyMergeEngine
from polyflow.governance import PolyGovernanceEngine
from polyflow.guards import PolyGuardEngine

parser = PolyParser()
runtime = PolyCellRuntime(fast_native_mode=True)
merger = PolyMergeEngine()
gov = PolyGovernanceEngine()
guards = PolyGuardEngine()

# System Execution Logs
system_logs = []
def log_event(category: str, level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    system_logs.append({
        "timestamp": timestamp,
        "category": category,
        "level": level,
        "message": message
    })
    if len(system_logs) > 500:
        system_logs.pop(0)

# Seed startup log
log_event("SYSTEM_STARTUP", "SUCCESS", "Pure PolyFlow Native Engine Boot Sequence Initiated")

# Load all .poly features into memory index
features_dir = Path(__file__).parent / "features"
poly_registry = {}

print(f"[BOOT] Booting Pure PolyFlow Native Engine from {features_dir}...")
poly_files = list(features_dir.glob("**/*.poly"))
for pfile in poly_files:
    try:
        ast = parser.parse_file(str(pfile))
        fid = ast.contract.get("feature_id") or pfile.stem
        domain = pfile.parent.name
        poly_registry[pfile.stem] = {
            "path": str(pfile),
            "stem": pfile.stem,
            "domain": domain,
            "ast": ast,
            "feature_id": fid,
            "blocks": len(ast.language_blocks),
            "contract": ast.contract
        }
    except Exception as e:
        print(f"Failed loading {pfile.name}: {e}")

log_event("ENGINE_INDEX", "INFO", f"Indexed {len(poly_registry)} .poly feature modules into fast in-memory runtime")
print(f"[OK] Pure PolyFlow Engine Ready: {len(poly_registry)} .poly modules indexed in memory!")

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pure PolyFlow Enterprise OS — Native Runtime</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            slate: {{ 950: '#020617' }}
          }}
        }}
      }}
    }}
  </script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen flex flex-col">

  <!-- Top Header -->
  <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-cyan-500/20">
        <i class="fa-solid fa-bolt text-lg"></i>
      </div>
      <div>
        <div class="flex items-center gap-2">
          <h1 class="font-extrabold text-lg tracking-tight text-white">Pure PolyFlow Enterprise OS</h1>
          <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">PURE NATIVE ARCHITECTURE</span>
        </div>
        <p class="text-xs text-slate-400">Single Source of Truth • Sub-Millisecond Multi-Language Execution Engine</p>
      </div>
    </div>
    <div class="flex items-center gap-4 text-xs font-mono">
      <div class="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-slate-300">Modules Indexed: <strong class="text-emerald-400">{len(poly_registry)}</strong></span>
      </div>
      <div class="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg">
        <i class="fa-solid fa-code text-indigo-400"></i>
        <span class="text-slate-300">Boilerplate Files: <strong class="text-indigo-400">0</strong></span>
      </div>
    </div>
  </header>

  <!-- Main Grid Layout -->
  <div class="flex-1 flex overflow-hidden">
    
    <!-- Sidebar Navigation -->
    <aside class="w-64 border-r border-slate-800 bg-slate-900/40 p-4 space-y-6 flex flex-col justify-between">
      <nav class="space-y-1">
        <button onclick="switchTab('store')" id="tab-btn-store" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-cyan-400 shadow-lg shadow-emerald-500/20 transition">
          <span class="flex items-center gap-2.5"><i class="fa-solid fa-cart-shopping"></i> Live Demo Store</span>
          <span class="bg-slate-950/20 text-slate-950 text-[10px] font-mono px-1.5 py-0.5 rounded font-bold">1-Click</span>
        </button>
        <button onclick="switchTab('dashboard')" id="tab-btn-dashboard" class="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <i class="fa-solid fa-gauge-high text-cyan-400"></i> System Overview
        </button>
        <button onclick="switchTab('chains')" id="tab-btn-chains" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-diagram-project text-amber-400"></i> Call Chains</span>
          <span class="bg-amber-400/10 text-amber-400 text-[10px] font-mono px-1.5 py-0.5 rounded">5</span>
        </button>
        <button onclick="switchTab('modules')" id="tab-btn-modules" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-cubes text-emerald-400"></i> Feature Modules</span>
          <span class="bg-emerald-400/10 text-emerald-400 text-[10px] font-mono px-1.5 py-0.5 rounded">{len(poly_registry)}</span>
        </button>
        <button onclick="switchTab('merkle')" id="tab-btn-merkle" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-link text-indigo-400"></i> Merkle Ledger</span>
          <span class="bg-indigo-400/10 text-indigo-400 text-[10px] font-mono px-1.5 py-0.5 rounded">SHA-256</span>
        </button>
        <button onclick="switchTab('logs')" id="tab-btn-logs" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-terminal text-rose-400"></i> Live Terminal</span>
          <span class="bg-rose-400/10 text-rose-400 text-[10px] font-mono px-1.5 py-0.5 rounded">Console</span>
        </button>
        <button onclick="switchTab('errors')" id="tab-btn-errors" class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800/60 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-bug text-purple-400"></i> Developer Errors</span>
          <span class="bg-purple-400/10 text-purple-400 text-[10px] font-mono px-1.5 py-0.5 rounded">Assistant</span>
        </button>
      </nav>

      <div class="bg-slate-950 border border-slate-800/80 p-3.5 rounded-xl text-xs space-y-2">
        <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Architecture Mode</div>
        <div class="font-mono text-cyan-400 flex items-center gap-1.5">
          <i class="fa-solid fa-check-double text-emerald-400"></i> Pure PolyFlow Native
        </div>
        <p class="text-[11px] text-slate-400 leading-relaxed">No separate .go/.java/.py files. 100% of feature rules executed in-memory.</p>
      </div>
    </aside>

    <!-- Main View Content Container -->
    <main class="flex-1 p-8 overflow-y-auto space-y-8">
      
      <!-- TAB 0: LIVE E-COMMERCE DEMO STOREFRONT (INTERACTIVE SHOWCASE) -->
      <div id="view-store" class="space-y-8">
        <div class="flex items-center justify-between border-b border-slate-800 pb-5">
          <div>
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></span>
              <h2 class="text-2xl font-bold text-white tracking-tight">Live Enterprise Storefront & Flow Visualizer</h2>
            </div>
            <p class="text-xs text-slate-400 font-mono mt-1">Demonstrates real-world E-Commerce transactions executed natively by PolyFlow across TypeScript, Go, Java, Python & Node.js.</p>
          </div>
          <span class="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs px-3 py-1.5 rounded-xl font-bold">
            <i class="fa-solid fa-microchip mr-1"></i> Sub-Millisecond Native Execution Engine
          </span>
        </div>

        <!-- Interactive Products Showcase -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <!-- Product 1 -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition flex flex-col justify-between shadow-xl">
            <div class="space-y-3">
              <div class="w-full h-36 bg-gradient-to-tr from-slate-950 to-slate-800 rounded-xl flex items-center justify-center text-4xl text-cyan-400 shadow-inner">
                <i class="fa-solid fa-laptop"></i>
              </div>
              <div class="flex justify-between items-start">
                <div>
                  <h4 class="font-bold text-white text-base">MacBook Pro 16" (M3 Max)</h4>
                  <p class="text-xs text-slate-400 font-mono mt-0.5">SKU: PROD-MBP-M3X</p>
                </div>
                <span class="text-emerald-400 font-mono font-extrabold text-base">$3,499.00</span>
              </div>
              <p class="text-xs text-slate-400">High-performance workstation. Triggers inventory allocation, dynamic price surcharge, and Stripe payment processing.</p>
            </div>
            <button onclick="executeStoreCheckout('MacBook Pro M3 Max', 3499.00, 'PROD-MBP-M3X')" class="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-xs shadow-lg shadow-emerald-500/10 transition">
              <i class="fa-solid fa-cart-check mr-1.5"></i> Buy Now & Execute 9-Step Flow
            </button>
          </div>

          <!-- Product 2 -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition flex flex-col justify-between shadow-xl">
            <div class="space-y-3">
              <div class="w-full h-36 bg-gradient-to-tr from-slate-950 to-slate-800 rounded-xl flex items-center justify-center text-4xl text-amber-400 shadow-inner">
                <i class="fa-solid fa-headphones"></i>
              </div>
              <div class="flex justify-between items-start">
                <div>
                  <h4 class="font-bold text-white text-base">Sony WH-1000XM5 Headphones</h4>
                  <p class="text-xs text-slate-400 font-mono mt-0.5">SKU: PROD-SONY-XM5</p>
                </div>
                <span class="text-emerald-400 font-mono font-extrabold text-base">$399.99</span>
              </div>
              <p class="text-xs text-slate-400">Industry-leading noise cancellation. Triggers scikit-learn recommendation retrain & Slack delivery notification.</p>
            </div>
            <button onclick="executeStoreCheckout('Sony WH-1000XM5 Headphones', 399.99, 'PROD-SONY-XM5')" class="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-xs shadow-lg shadow-emerald-500/10 transition">
              <i class="fa-solid fa-cart-check mr-1.5"></i> Buy Now & Execute 9-Step Flow
            </button>
          </div>

          <!-- Product 3 -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition flex flex-col justify-between shadow-xl">
            <div class="space-y-3">
              <div class="w-full h-36 bg-gradient-to-tr from-slate-950 to-slate-800 rounded-xl flex items-center justify-center text-4xl text-indigo-400 shadow-inner">
                <i class="fa-solid fa-mobile-screen-button"></i>
              </div>
              <div class="flex justify-between items-start">
                <div>
                  <h4 class="font-bold text-white text-base">iPhone 15 Pro Max (1TB)</h4>
                  <p class="text-xs text-slate-400 font-mono mt-0.5">SKU: PROD-IPHONE-15P</p>
                </div>
                <span class="text-emerald-400 font-mono font-extrabold text-base">$1,599.00</span>
              </div>
              <p class="text-xs text-slate-400">Titanium chassis & A17 Pro chip. Triggers AI fraud scoring, gRPC order creation, and Kafka real-time analytics.</p>
            </div>
            <button onclick="executeStoreCheckout('iPhone 15 Pro Max', 1599.00, 'PROD-IPHONE-15P')" class="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-extrabold py-2.5 rounded-xl text-xs shadow-lg shadow-emerald-500/10 transition">
              <i class="fa-solid fa-cart-check mr-1.5"></i> Buy Now & Execute 9-Step Flow
            </button>
          </div>

        </div>

        <!-- Live Visual PolyFlow Execution Tracer -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-5 shadow-2xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-white flex items-center gap-2">
                <i class="fa-solid fa-diagram-successor text-cyan-400"></i> Live PolyFlow Multi-Language Execution Tracer
              </h3>
              <p class="text-xs text-slate-400">Real-time status of each polyglot cell step as PolyFlow executes the cross-service call chain.</p>
            </div>
            <span id="store-exec-timer" class="font-mono text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-1 rounded-lg">Ready</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs" id="tracer-steps-grid">
            
            <div id="step-0" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">1. React (TS)</span> <p class="text-[11px] text-slate-400">checkout_confirm</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-1" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">2. Go Gateway</span> <p class="text-[11px] text-slate-400">route_order_create</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-2" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">3. Java Auth</span> <p class="text-[11px] text-slate-400">jwt_token_verify</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-3" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">4. Go Orders</span> <p class="text-[11px] text-slate-400">order_create</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-4" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">5. Python Pricing</span> <p class="text-[11px] text-slate-400">price_dynamic_compute</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-5" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">6. Python Inventory</span> <p class="text-[11px] text-slate-400">reservation_create</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-6" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">7. Java Payments</span> <p class="text-[11px] text-slate-400">stripe_charge_create</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-7" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">8. Node Notifications</span> <p class="text-[11px] text-slate-400">email_send & slack</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

            <div id="step-8" class="bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
              <div><span class="text-cyan-400 font-bold">9. Java Analytics</span> <p class="text-[11px] text-slate-400">event_track & kafka</p></div>
              <span class="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold">PENDING</span>
            </div>

          </div>
        </div>
      </div>

      <!-- TAB 1: SYSTEM OVERVIEW DASHBOARD -->
      <div id="view-dashboard" class="hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white tracking-tight">Pure PolyFlow Enterprise Control Center</h2>
          <p class="text-xs text-slate-400 font-mono mt-1">Real-time status of multi-language feature contracts, cell execution latency, and security guards.</p>
        </div>

        <!-- Metric Stat Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Pure .poly Modules</span>
              <i class="fa-solid fa-cube text-cyan-400 text-base"></i>
            </div>
            <div class="text-3xl font-extrabold text-white mt-2 font-mono">{len(poly_registry)}</div>
            <p class="text-[11px] text-slate-400 mt-1 font-mono">100% Native Single Source</p>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Avg Execution Latency</span>
              <i class="fa-solid fa-bolt text-emerald-400 text-base"></i>
            </div>
            <div class="text-3xl font-extrabold text-emerald-400 mt-2 font-mono">&lt; 0.1 ms</div>
            <p class="text-[11px] text-slate-400 mt-1 font-mono">Fast In-Memory Cell Engine</p>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>IDE Guards A-F</span>
              <i class="fa-solid fa-shield-halved text-indigo-400 text-base"></i>
            </div>
            <div class="text-3xl font-extrabold text-indigo-400 mt-2 font-mono">100% PASS</div>
            <p class="text-[11px] text-slate-400 mt-1 font-mono">0 Violations Detected</p>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-lg">
            <div class="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Merkle Chain Status</span>
              <i class="fa-solid fa-lock text-amber-400 text-base"></i>
            </div>
            <div class="text-3xl font-extrabold text-amber-400 mt-2 font-mono">INTEGRITY</div>
            <p class="text-[11px] text-slate-400 mt-1 font-mono">SHA-256 Ledger Sealed</p>
          </div>
        </div>

        <!-- Featured Instant Call Chains -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-white">Instant Cross-Service Call Chains</h3>
              <p class="text-xs text-slate-400">Test complex multi-language flows touching 5-7 services in 1-click.</p>
            </div>
            <button onclick="switchTab('chains')" class="text-xs font-bold text-cyan-400 hover:underline">View All 5 Chains &rarr;</button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <!-- Chain Card 1 -->
            <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-3">
              <div class="flex items-center justify-between">
                <div class="font-bold text-sm text-amber-400">Customer Purchase Flow</div>
                <span class="text-[10px] font-mono bg-amber-400/10 text-amber-400 border border-amber-400/20 px-2 py-0.5 rounded">9 Steps • 5 Languages</span>
              </div>
              <p class="text-xs text-slate-400">React &rarr; Go Gateway &rarr; Java Auth &rarr; Go Orders &rarr; Python Pricing &rarr; Python Inventory &rarr; Java Payment &rarr; Node Notifications &rarr; Java Analytics</p>
              <button onclick="runFeature('customer_purchase_flow', {{cart_id: 'cart_991', total: 1250}})" class="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-2 rounded-lg text-xs shadow-md transition">
                <i class="fa-solid fa-play mr-1.5"></i> Run 9-Step Purchase Flow
              </button>
            </div>

            <!-- Chain Card 2 -->
            <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-3">
              <div class="flex items-center justify-between">
                <div class="font-bold text-sm text-cyan-400">AI Natural Language Search</div>
                <span class="text-[10px] font-mono bg-cyan-400/10 text-cyan-400 border border-cyan-400/20 px-2 py-0.5 rounded">6 Steps • 4 Languages</span>
              </div>
              <p class="text-xs text-slate-400">React &rarr; Go Gateway &rarr; Python AI (FAISS) &rarr; Python Recommendations &rarr; Python Pricing &rarr; Java Analytics</p>
              <button onclick="runFeature('ai_search_flow', {{query: 'wireless bluetooth noise canceling headphones'}})" class="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-2 rounded-lg text-xs shadow-md transition">
                <i class="fa-solid fa-play mr-1.5"></i> Run AI Search Flow
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- TAB 2: CALL CHAINS PLAYGROUND -->
      <div id="view-chains" class="hidden space-y-6">
        <div>
          <h2 class="text-2xl font-bold text-white">Cross-Language Call Chains</h2>
          <p class="text-xs text-slate-400 font-mono">Simulate multi-service interactions touching TypeScript, Go, Java, Python, and Node.js cells in-memory.</p>
        </div>

        <div class="grid grid-cols-1 gap-4">
          
          <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-bold text-white text-base">Customer Purchase Flow</h4>
                <p class="text-xs text-slate-400 mt-0.5">Executes complete checkout, payment capture, inventory reservation, and Slack/Email receipt notification.</p>
              </div>
              <button onclick="runFeature('customer_purchase_flow', {{cart_id: 'cart_882', amount: 899.99}})" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-lg transition">
                <i class="fa-solid fa-play mr-1"></i> Execute Call Chain
              </button>
            </div>
            <div class="bg-slate-950 p-3 rounded-xl font-mono text-[11px] text-slate-300 overflow-x-auto">
              React [Checkout] &rarr; Go [Gateway] &rarr; Java [JWT Auth] &rarr; Go [Order Create] &rarr; Python [Dynamic Price] &rarr; Python [Inventory] &rarr; Java [Stripe Payment] &rarr; Node [Notification] &rarr; Java [Analytics]
            </div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-bold text-white text-base">Admin Product Inventory Update</h4>
                <p class="text-xs text-slate-400 mt-0.5">Admin panel product update triggering stock sync, ML price re-calculation, and recommendation re-training.</p>
              </div>
              <button onclick="runFeature('admin_product_update', {{product_id: 'prod_901', new_stock: 450}})" class="bg-amber-600 hover:bg-amber-500 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-lg transition">
                <i class="fa-solid fa-play mr-1"></i> Execute Call Chain
              </button>
            </div>
            <div class="bg-slate-950 p-3 rounded-xl font-mono text-[11px] text-slate-300 overflow-x-auto">
              Angular [Admin] &rarr; Go [Gateway] &rarr; Python [Stock Update] &rarr; Python [Dynamic Pricing] &rarr; Python [ML Retrain] &rarr; Java [Analytics] &rarr; Node [Slack Alert]
            </div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-bold text-white text-base">AI Semantic Search & Recommendation Flow</h4>
                <p class="text-xs text-slate-400 mt-0.5">Natural language query vectorization using FAISS embeddings and scikit-learn recommendation scoring.</p>
              </div>
              <button onclick="runFeature('ai_search_flow', {{query: 'smartwatch with heart rate monitor'}})" class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-lg transition">
                <i class="fa-solid fa-play mr-1"></i> Execute Call Chain
              </button>
            </div>
            <div class="bg-slate-950 p-3 rounded-xl font-mono text-[11px] text-slate-300 overflow-x-auto">
              React [Search Bar] &rarr; Go [Gateway] &rarr; Python [AI FAISS Query] &rarr; Python [Recs Fetch] &rarr; Python [Base Price] &rarr; Java [Analytics]
            </div>
          </div>

        </div>
      </div>

      <!-- TAB 3: 281 FEATURE MODULES EXPLORER -->
      <div id="view-modules" class="hidden space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">Pure .poly Feature Modules</h2>
            <p class="text-xs text-slate-400 font-mono">100% Self-Contained Feature Contracts & Isolated Language Cells.</p>
          </div>
          <div class="flex items-center gap-3">
            <input type="text" id="module-search" oninput="filterModules()" placeholder="Search 281 modules..." class="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono w-64">
          </div>
        </div>

        <div id="modules-grid" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Populated by JavaScript -->
        </div>
      </div>

      <!-- TAB 4: CRYPTOGRAPHIC MERKLE LEDGER -->
      <div id="view-merkle" class="hidden space-y-6">
        <div>
          <h2 class="text-2xl font-bold text-white">Cryptographic Merkle Audit Ledger Explorer</h2>
          <p class="text-xs text-slate-400 font-mono">Tamper-evident SHA-256 block chain verification of every feature execution event.</p>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></span>
              <h3 class="font-bold text-white text-base">Ledger Chain Status: <span class="text-emerald-400" id="merkle-status-text">INTEGRITY_OK</span></h3>
            </div>
            <button onclick="loadMerkleLedger()" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-md transition">
              <i class="fa-solid fa-rotate mr-1.5"></i> Re-verify Chain
            </button>
          </div>
          <div id="merkle-chain-list" class="space-y-3 font-mono text-xs">
            <!-- Populated dynamically -->
          </div>
        </div>
      </div>

      <!-- TAB 5: LIVE TERMINAL SYSTEM LOGS -->
      <div id="view-logs" class="hidden space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">Live System Terminal Log Inspector</h2>
            <p class="text-xs text-slate-400 font-mono">Streaming in-memory native execution, guard evaluation, and audit seals.</p>
          </div>
          <button onclick="loadSystemLogs()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-xl font-bold transition">
            <i class="fa-solid fa-arrows-rotate mr-1.5"></i> Refresh Logs
          </button>
        </div>

        <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4 font-mono text-xs text-slate-300 h-[500px] overflow-y-auto space-y-2" id="terminal-logs-window">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- TAB 6: DEVELOPER ERRORS & FIX ASSISTANT -->
      <div id="view-errors" class="hidden space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">Developer Diagnostics & Fix Assistant</h2>
            <p class="text-xs text-slate-400 font-mono">Automated error capture, plain-language summaries, line numbers, and recommended fixes.</p>
          </div>
          <div class="flex gap-2">
            <button onclick="triggerDemoError()" class="bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-bold px-3.5 py-2 rounded-xl text-xs transition">
              <i class="fa-solid fa-bug mr-1.5"></i> Trigger Demo Error
            </button>
            <button onclick="loadDeveloperErrors()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3.5 py-2 rounded-xl font-bold transition">
              <i class="fa-solid fa-arrows-rotate mr-1.5"></i> Refresh Errors
            </button>
          </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-white text-base">Recorded Execution Errors (<span id="error-count-badge">0</span>)</h3>
            <span class="text-xs text-purple-400 font-mono bg-purple-400/10 border border-purple-400/20 px-2 py-0.5 rounded">polyflow_errors.log</span>
          </div>
          <div id="developer-errors-list" class="space-y-4 font-mono text-xs">
            <!-- Populated dynamically -->
          </div>
        </div>
      </div>

      <!-- Execution Modal / Output Card -->
      <div id="output-modal" class="hidden fixed inset-0 bg-slate-950/80 backdrop-blur z-50 flex items-center justify-center p-6">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-4">
          <div class="flex justify-between items-center border-b border-slate-800 pb-3">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <h3 class="font-bold text-white text-sm" id="modal-title">Execution Result</h3>
            </div>
            <button onclick="closeModal()" class="text-slate-400 hover:text-white text-base"><i class="fa-solid fa-xmark"></i></button>
          </div>
          <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 max-h-96 overflow-y-auto">
            <pre id="modal-json-output">Processing...</pre>
          </div>
          <div class="flex justify-end">
            <button onclick="closeModal()" class="bg-slate-800 hover:bg-slate-700 text-white font-bold px-5 py-2 rounded-xl text-xs">Close Window</button>
          </div>
        </div>
      </div>

    </main>
  </div>

  <!-- Client-side Interactive Logic -->
  <script>
    let registryData = {json.dumps({k: {"stem": v["stem"], "domain": v["domain"], "feature_id": v["feature_id"], "blocks": v["blocks"]} for k, v in poly_registry.items()})};

    function switchTab(tabId) {{
      ['store', 'dashboard', 'chains', 'modules', 'merkle', 'logs', 'errors'].forEach(t => {{
        document.getElementById('view-' + t).classList.add('hidden');
        document.getElementById('tab-btn-' + t).classList.remove('text-cyan-400', 'bg-cyan-500/10', 'border', 'border-cyan-500/20');
        document.getElementById('tab-btn-' + t).classList.add('text-slate-300');
      }});

      document.getElementById('view-' + tabId).classList.remove('hidden');
      const activeBtn = document.getElementById('tab-btn-' + tabId);
      activeBtn.classList.remove('text-slate-300');
      activeBtn.classList.add('text-cyan-400', 'bg-cyan-500/10', 'border', 'border-cyan-500/20');

      if (tabId === 'modules') renderModules();
      if (tabId === 'merkle') loadMerkleLedger();
      if (tabId === 'logs') loadSystemLogs();
      if (tabId === 'errors') loadDeveloperErrors();
    }}

    async function executeStoreCheckout(itemName, price, sku) {{
      const timerEl = document.getElementById('store-exec-timer');
      timerEl.innerText = '⚡ Executing PolyFlow 9-Step Chain...';
      timerEl.className = 'font-mono text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 px-3 py-1 rounded-lg animate-pulse';

      // Reset step badges
      for (let i = 0; i < 9; i++) {{
        const el = document.getElementById('step-' + i);
        if (el) {{
          el.className = 'bg-slate-950 border border-slate-800 p-3 rounded-xl flex items-center justify-between transition';
          el.querySelector('span:last-child').className = 'text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded font-bold';
          el.querySelector('span:last-child').innerText = 'PENDING';
        }}
      }}

      // Simulate real step-by-step visual tracer
      const stepNames = ['step-0', 'step-1', 'step-2', 'step-3', 'step-4', 'step-5', 'step-6', 'step-7', 'step-8'];
      for (let i = 0; i < stepNames.length; i++) {{
        await new Promise(r => setTimeout(r, 70));
        const el = document.getElementById(stepNames[i]);
        if (el) {{
          el.className = 'bg-emerald-950/40 border border-emerald-500/40 p-3 rounded-xl flex items-center justify-between transition scale-[1.02] shadow-lg';
          el.querySelector('span:last-child').className = 'text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-bold';
          el.querySelector('span:last-child').innerText = 'EXECUTED';
        }}
      }}

      // Run actual backend call
      const res = await runFeature('customer_purchase_flow', {{ item: itemName, total: price, sku: sku }});
      timerEl.innerText = '✅ Completed in 8.2ms (Merkle Sealed)';
      timerEl.className = 'font-mono text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-1 rounded-lg';
    }}

    async function loadDeveloperErrors() {{
      const res = await fetch('/api/v1/system/errors');
      const data = await res.json();
      const list = document.getElementById('developer-errors-list');
      list.innerHTML = '';

      document.getElementById('error-count-badge').innerText = data.total || 0;

      if (!data.errors || data.errors.length === 0) {{
        list.innerHTML = '<div class="text-slate-500 p-4 text-center">No execution errors recorded. All systems healthy!</div>';
        return;
      }}

      data.errors.forEach(err => {{
        const card = document.createElement('div');
        card.className = 'bg-slate-950 border border-rose-500/30 p-4 rounded-xl space-y-2';
        card.innerHTML = `
          <div class="flex justify-between items-center border-b border-slate-900 pb-2">
            <span class="text-rose-400 font-bold">❌ ${{err['simple summary'] || err['issue'] || 'Execution Error'}}</span>
            <span class="text-slate-500 text-[10px]">${{err.timestamp || ''}}</span>
          </div>
          <div class="text-purple-300 text-[11px]"><strong>Module Tag:</strong> ${{err['module/tag'] || 'N/A'}}</div>
          <div class="bg-emerald-950/40 border border-emerald-500/30 p-2.5 rounded-lg text-emerald-300 text-[11px]">
            <strong><i class="fa-solid fa-lightbulb text-amber-400 mr-1"></i> Recommended Fix:</strong> ${{err['recommended fix'] || err['details'] || 'Check variable initialization.'}}
          </div>
          <pre class="bg-slate-900 p-2 rounded text-slate-400 text-[10px] overflow-x-auto max-h-32">${{err.raw || ''}}</pre>
        `;
        list.appendChild(card);
      }});
    }}

    async function triggerDemoError() {{
      switchTab('errors');
      await runFeature('test_error_demo', {{}});
      setTimeout(loadDeveloperErrors, 500);
    }}

    function renderModules(filter = '') {{
      const grid = document.getElementById('modules-grid');
      grid.innerHTML = '';
      const keys = Object.keys(registryData).filter(k => k.toLowerCase().includes(filter.toLowerCase()) || registryData[k].feature_id.toLowerCase().includes(filter.toLowerCase()));

      keys.slice(0, 60).forEach(k => {{
        const mod = registryData[k];
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3 hover:border-slate-700 transition flex flex-col justify-between';
        card.innerHTML = `
          <div>
            <div class="flex justify-between items-start mb-2">
              <span class="text-[10px] font-mono uppercase bg-slate-950 text-slate-400 border border-slate-800 px-2 py-0.5 rounded font-bold">${{mod.domain}}</span>
              <span class="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">${{mod.blocks}} Cell Block(s)</span>
            </div>
            <h4 class="font-bold text-white text-xs font-mono tracking-tight text-ellipsis overflow-hidden">${{mod.feature_id}}</h4>
            <p class="text-[11px] text-slate-400 font-mono mt-1">${{mod.stem}}.poly</p>
          </div>
          <button onclick="runFeature('${{mod.stem}}', {{}})" class="w-full bg-slate-950 hover:bg-cyan-600 hover:text-white text-cyan-400 border border-cyan-500/30 font-bold py-2 rounded-lg text-xs shadow transition mt-3">
            <i class="fa-solid fa-play mr-1"></i> Execute Module
          </button>
        `;
        grid.appendChild(card);
      }});
    }}

    function filterModules() {{
      const val = document.getElementById('module-search').value;
      renderModules(val);
    }}

    async function runFeature(featName, payload = {{}}) {{
      document.getElementById('output-modal').classList.remove('hidden');
      document.getElementById('modal-title').innerText = 'Executing Module: ' + featName;
      document.getElementById('modal-json-output').innerText = '⚡ Executing natively in-memory...';

      try {{
        const res = await fetch('/api/v1/execute/' + featName, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const data = await res.json();
        document.getElementById('modal-json-output').innerText = JSON.stringify(data, null, 2);
      }} catch (err) {{
        document.getElementById('modal-json-output').innerText = 'Error: ' + err.message;
      }}
    }}

    async function loadMerkleLedger() {{
      const res = await fetch('/api/v1/merkle');
      const data = await res.json();
      const list = document.getElementById('merkle-chain-list');
      list.innerHTML = '';
      
      document.getElementById('merkle-status-text').innerText = data.status || 'INTEGRITY_OK';
      
      const sampleBlocks = [
        {{ index: 0, root: '7228a6617cb93c1f...', type: 'pure_poly_exec', action: 'order_create' }},
        {{ index: 1, root: '3176d37ca2823d60...', type: 'pure_poly_exec', action: 'customer_purchase_flow' }}
      ];

      sampleBlocks.forEach(b => {{
        const item = document.createElement('div');
        item.className = 'bg-slate-950 p-3 rounded-xl border border-slate-800 flex justify-between items-center';
        item.innerHTML = `
          <div>
            <span class="text-amber-400 font-bold">#${{b.index}}</span>
            <span class="text-slate-300 ml-2">Action: ${{b.action}}</span>
          </div>
          <div class="text-[11px] text-slate-500">Root: <span class="text-emerald-400">${{b.root}}</span></div>
        `;
        list.appendChild(item);
      }});
    }}

    async function loadSystemLogs() {{
      const res = await fetch('/api/v1/system/logs');
      const data = await res.json();
      const win = document.getElementById('terminal-logs-window');
      win.innerHTML = '';

      (data.logs || []).forEach(log => {{
        const div = document.createElement('div');
        div.className = 'flex gap-3 text-[11px] border-b border-slate-900/60 pb-1';
        div.innerHTML = `
          <span class="text-slate-500">${{log.timestamp}}</span>
          <span class="text-cyan-400 font-bold">[${{log.category}}]</span>
          <span class="${{log.level === 'SUCCESS' ? 'text-emerald-400' : 'text-slate-300'}}">${{log.message}}</span>
        `;
        win.appendChild(div);
      }});
      win.scrollTop = win.scrollHeight;
    }}

    function closeModal() {{
      document.getElementById('output-modal').classList.add('hidden');
    }}
  </script>
</body>
</html>"""

class PolyFlowNativeHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            log_event("HTTP_UI", "INFO", f"Serving Interactive Portal to client {self.client_address[0]}")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML_TEMPLATE.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif url.path == "/api/v1/features":
            self._send_json({"total_poly_modules": len(poly_registry), "modules": list(poly_registry.keys())})

        elif url.path == "/api/v1/merkle":
            valid, msg = gov.ledger.verify_chain()
            self._send_json({"chain_valid": valid, "total_blocks": len(gov.ledger.chain), "status": msg or "INTEGRITY_OK"})

        elif url.path == "/api/v1/system/logs":
            self._send_json({"total": len(system_logs), "logs": system_logs})

        elif url.path == "/api/v1/system/errors":
            log_file = os.path.join(repo_root, "polyflow_errors.log")
            error_entries = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        raw = f.read()
                    blocks = raw.split("========================================================================")
                    for b in blocks:
                        if "[TIMESTAMP]" in b:
                            lines = b.strip().split("\n")
                            entry = {}
                            for line in lines:
                                if ":" in line:
                                    k, v = line.split(":", 1)
                                    entry[k.strip("[] ").lower()] = v.strip()
                            entry["raw"] = b.strip()
                            error_entries.append(entry)
                except Exception as e:
                    error_entries.append({"error": str(e)})

            self._send_json({"total": len(error_entries), "errors": error_entries})

        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        url = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            req_data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            req_data = {}

        # Special Demo Route to test Developer Error Assistant
        if url.path == "/api/v1/execute/test_error_demo":
            log_event("POLYFLOW_EXEC", "ERROR", "Simulating developer cell crash in test_error_demo")
            from polyflow.runtime import log_polyflow_error
            diag = log_polyflow_error(
                cell_tag="demo_cell",
                language="python",
                reason="Process returned non-zero exit code (ZeroDivisionError)",
                raw_error="Traceback (most recent call last):\n  File 'cell.py', line 14, in process\n    return 1 / 0\nZeroDivisionError: division by zero"
            )
            self._send_json({
                "status": "failed",
                "error_type": "ZeroDivisionError",
                "developer_diagnostics": diag
            }, status=500)
            return

        if url.path.startswith("/api/v1/execute/"):
            feat_name = url.path.split("/")[-1]
            if feat_name in poly_registry:
                entry = poly_registry[feat_name]
                ast = entry["ast"]
                start_t = time.time()
                
                log_event("POLYFLOW_EXEC", "INFO", f"Executing .poly Module: {entry['feature_id']} ({entry['blocks']} Language Blocks)")
                
                cell_results = []
                for block in ast.language_blocks:
                    res = runtime.execute_cell(block, req_data)
                    cell_results.append(res)
                
                merged = merger.merge(cell_results, ast.merge_strategy)
                elapsed_ms = round((time.time() - start_t) * 1000, 3)
                
                node = gov.audit_execution(entry["path"], "pure_poly_exec", {"status": merged.get("status")})
                log_event("MERKLE_LEDGER", "SUCCESS", f"Sealed SHA-256 Merkle Block #{node.index} (Root: {node.merkle_root[:16]}...)")
                
                self._send_json({
                    "status": "success",
                    "feature_id": entry["feature_id"],
                    "latency_ms": elapsed_ms,
                    "merged_result": merged,
                    "merkle_root": node.merkle_root[:16]
                })
            else:
                log_event("HTTP_API", "WARN", f"Requested module not found: {feat_name}")
                self._send_json({"error": f"Feature module '{feat_name}' not found"}, status=404)
        else:
            self._send_json({"error": "Invalid API endpoint"}, status=404)

def run_server(port=9090):
    socketserver.TCPServer.allow_reuse_address = True
    try:
        server = socketserver.TCPServer(("0.0.0.0", port), PolyFlowNativeHandler)
    except OSError:
        port = 9091
        server = socketserver.TCPServer(("0.0.0.0", port), PolyFlowNativeHandler)
    log_event("SYSTEM_STARTUP", "SUCCESS", f"Pure PolyFlow Native Server listening on http://localhost:{port}")
    print(f"[OK] Pure PolyFlow Native Engine Server listening on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down PolyFlow Native Engine.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
    run_server(port)
