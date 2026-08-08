"""
PolyEnterprise Interactive Local Web Server.

Serves a live, full-stack Web UI on http://localhost:5000 connected to the PolyFlow runtime.
Extracts and renders React components and routes API calls directly into .poly feature modules.
"""

import sys
import json
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from polyflow.parser import PolyParser
from polyflow.runtime import PolyCellRuntime
from polyflow.merge import PolyMergeEngine
from polyflow.governance import PolyGovernanceEngine

app_dir = Path(__file__).parent
parser = PolyParser()
runtime = PolyCellRuntime()
merger = PolyMergeEngine()
gov = PolyGovernanceEngine()

def find_block(ast, lang: str, tag: str = None):
    for b in ast.language_blocks:
        if b.language.lower() == lang.lower():
            if tag and b.tag.lower() == tag.lower():
                return b
    for b in ast.language_blocks:
        if b.language.lower() == lang.lower() and not b.tag.startswith("test"):
            return b
    return ast.language_blocks[0]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PolyEnterprise Platform — Live PolyFlow System</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; }
    code, pre, .font-mono { font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

  <!-- Top Navigation Header -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center font-black text-xl text-white shadow-lg shadow-indigo-500/20">
        P
      </div>
      <div>
        <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          PolyEnterprise Platform
          <span class="bg-indigo-950 text-indigo-400 text-xs px-2.5 py-0.5 rounded-full border border-indigo-700/50 font-mono font-normal">.poly 10k lines architecture</span>
        </h1>
        <p class="text-xs text-slate-400">Live Multi-Language Runtime (React/TS • Python • Java • Go • Node)</p>
      </div>
    </div>

    <div class="flex items-center space-x-6">
      <div class="flex items-center space-x-2 text-xs text-slate-400">
        <span class="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-mono">PolyFlow Engine: ACTIVE (localhost:5000)</span>
      </div>
      <a href="#ledger" onclick="loadLedger()" class="bg-slate-800 hover:bg-slate-700 text-white text-xs px-3.5 py-2 rounded-lg font-semibold border border-slate-700 transition flex items-center gap-1.5">
        <i class="fa-solid fa-link text-emerald-400"></i> View Merkle Ledger
      </a>
    </div>
  </header>

  <!-- Main Portal Layout -->
  <div class="flex-1 flex overflow-hidden">
    
    <!-- Sidebar Controls -->
    <aside class="w-72 border-r border-slate-800 bg-slate-900/50 p-4 space-y-2 overflow-y-auto">
      <div class="text-xs font-semibold uppercase tracking-wider text-slate-400 px-3 py-2">
        Feature Modules (.poly)
      </div>
      
      <button onclick="switchTab('auth')" id="nav-auth" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-indigo-600 text-white shadow-lg">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-shield-halved"></i> 01. Enterprise Auth</span>
        <span class="font-mono text-[10px] opacity-75">React + Py</span>
      </button>

      <button onclick="switchTab('rbac')" id="nav-rbac" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-user-lock"></i> 02. RBAC Directory</span>
        <span class="font-mono text-[10px] text-slate-400">Py + Java</span>
      </button>

      <button onclick="switchTab('catalog')" id="nav-catalog" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-boxes-stacked"></i> 03. Inventory Catalog</span>
        <span class="font-mono text-[10px] text-slate-400">React + Go</span>
      </button>

      <button onclick="switchTab('pricing')" id="nav-pricing" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-calculator"></i> 04. AI Pricing Engine</span>
        <span class="font-mono text-[10px] text-slate-400">Python AI</span>
      </button>

      <button onclick="switchTab('checkout')" id="nav-checkout" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-cart-shopping"></i> 05. Cart & Checkout</span>
        <span class="font-mono text-[10px] text-slate-400">React + Py</span>
      </button>

      <button onclick="switchTab('payment')" id="nav-payment" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-credit-card"></i> 06. Payment Circuit Breaker</span>
        <span class="font-mono text-[10px] text-emerald-400 font-bold">Resilient</span>
      </button>

      <button onclick="switchTab('fulfillment')" id="nav-fulfillment" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-truck-fast"></i> 07. SAP ERP Fulfillment</span>
        <span class="font-mono text-[10px] text-slate-400">Java + Go</span>
      </button>

      <button onclick="switchTab('notifications')" id="nav-notifications" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-bell"></i> 08. Notifications</span>
        <span class="font-mono text-[10px] text-slate-400">Node Webhook</span>
      </button>

      <button onclick="switchTab('risk')" id="nav-risk" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-chart-line"></i> 09. AI Fraud Analytics</span>
        <span class="font-mono text-[10px] text-slate-400">Py ML</span>
      </button>

      <button onclick="switchTab('soc2')" id="nav-soc2" class="nav-btn w-full text-left px-3.5 py-3 rounded-xl text-xs font-semibold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-2.5"><i class="fa-solid fa-file-contract"></i> 10. SOC2 Merkle Ledger</span>
        <span class="font-mono text-[10px] text-slate-400">SHA-256</span>
      </button>
    </aside>

    <!-- Main Dynamic Workspace -->
    <main class="flex-1 p-8 overflow-y-auto">
      
      <!-- Module 1: Enterprise Auth UI -->
      <div id="tab-auth" class="tab-content max-w-xl mx-auto space-y-6">
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl">
          <div class="flex items-center gap-3 border-b border-slate-800 pb-4">
            <i class="fa-solid fa-shield-halved text-2xl text-indigo-500"></i>
            <div>
              <h2 class="text-xl font-bold text-white">OAuth 2.0 PKCE & SAML Login</h2>
              <p class="text-xs text-slate-400 font-mono">01_enterprise_auth.poly</p>
            </div>
          </div>

          <form onsubmit="handleAuthSubmit(event)" class="mt-6 space-y-4">
            <div>
              <label class="block text-xs font-semibold uppercase text-slate-400">Corporate Email</label>
              <input id="auth-email" type="email" value="admin.executive@enterprise.com" required className="w-full bg-slate-950 border border-slate-800 text-white text-xs px-3.5 py-2.5 rounded-xl font-mono mt-1 w-full" style="width: 100%; background: #020617; border: 1px solid #1e293b; padding: 10px; color: white; border-radius: 8px;" />
            </div>
            <div>
              <label class="block text-xs font-semibold uppercase text-slate-400">Password</label>
              <input id="auth-pass" type="password" value="Password123!" required style="width: 100%; background: #020617; border: 1px solid #1e293b; padding: 10px; color: white; border-radius: 8px;" />
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Authenticate via PolyFlow Engine
            </button>
          </form>

          <div id="auth-response" class="mt-6 hidden bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto"></div>
        </div>
      </div>

      <!-- Module 6: Payment Circuit Breaker UI -->
      <div id="tab-payment" class="tab-content hidden max-w-2xl mx-auto space-y-6">
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
              <i class="fa-solid fa-credit-card text-2xl text-emerald-400"></i>
              <div>
                <h2 class="text-xl font-bold text-white">Multi-Language Circuit Breaker</h2>
                <p class="text-xs text-slate-400 font-mono">06_multi_gateway_payment.poly</p>
              </div>
            </div>
            <span class="bg-emerald-950 border border-emerald-700 text-emerald-300 text-xs px-3 py-1 rounded-full font-mono">Fail-Partial Resilient</span>
          </div>

          <div class="mt-6 bg-slate-950 p-4 rounded-xl border border-slate-800">
            <label class="flex items-center justify-between cursor-pointer">
              <span class="text-xs font-semibold text-slate-300">Simulate Primary Python Stripe Outage</span>
              <input id="toggle-failover" type="checkbox" checked class="h-4 w-4 rounded border-slate-700 bg-slate-800 text-emerald-600" />
            </label>
          </div>

          <button onclick="handlePaymentSubmit()" class="mt-4 w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl text-xs shadow-lg transition">
            Execute Payment Routing ($27,201.68)
          </button>

          <div id="payment-response" class="mt-6 hidden bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs overflow-x-auto"></div>
        </div>
      </div>

      <!-- Module 10: Merkle Ledger Graph Viewer -->
      <div id="tab-soc2" class="tab-content hidden max-w-4xl mx-auto space-y-6">
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-xl font-bold text-white">Cryptographic Merkle Audit Ledger</h2>
              <p class="text-xs text-slate-400 font-mono">10_soc2_compliance_merkle.poly & PolyGovernanceEngine</p>
            </div>
            <button onclick="loadLedger()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-xl font-bold">
              Refresh Merkle Chain
            </button>
          </div>

          <div id="ledger-nodes" class="mt-6 space-y-3 font-mono text-xs">
            <p class="text-slate-400">Loading ledger nodes...</p>
          </div>
        </div>
      </div>

      <!-- Generic Fallback Panel -->
      <div id="tab-generic" class="tab-content hidden max-w-3xl mx-auto space-y-6">
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl">
          <h2 id="generic-title" class="text-xl font-bold text-white">Module View</h2>
          <p id="generic-desc" class="text-xs text-slate-400 font-mono mt-1"></p>
          <button onclick="executeGenericModule()" class="mt-6 bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2.5 rounded-xl font-bold">
            Execute .poly Feature Cell Live
          </button>
          <div id="generic-response" class="mt-6 hidden bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400"></div>
        </div>
      </div>

    </main>
  </div>

  <script>
    let currentTab = 'auth';

    function switchTab(tabId) {
      currentTab = tabId;
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.nav-btn').forEach(el => {
        el.classList.remove('bg-indigo-600', 'text-white', 'shadow-lg');
        el.classList.add('text-slate-300');
      });

      const navBtn = document.getElementById('nav-' + tabId);
      if (navBtn) {
        navBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-lg');
        navBtn.classList.remove('text-slate-300');
      }

      if (tabId === 'auth') {
        document.getElementById('tab-auth').classList.remove('hidden');
      } else if (tabId === 'payment') {
        document.getElementById('tab-payment').classList.remove('hidden');
      } else if (tabId === 'soc2') {
        document.getElementById('tab-soc2').classList.remove('hidden');
        loadLedger();
      } else {
        document.getElementById('tab-generic').classList.remove('hidden');
        document.getElementById('generic-title').innerText = 'Module: ' + tabId.toUpperCase();
        document.getElementById('generic-desc').innerText = tabId + '.poly feature cell executor';
        document.getElementById('generic-response').classList.add('hidden');
      }
    }

    async function handleAuthSubmit(e) {
      e.preventDefault();
      const email = document.getElementById('auth-email').value;
      const pass = document.getElementById('auth-pass').value;

      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: email, password: pass })
      });
      const data = await res.json();
      const outBox = document.getElementById('auth-response');
      outBox.classList.remove('hidden');
      outBox.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }

    async function handlePaymentSubmit() {
      const failover = document.getElementById('toggle-failover').checked;
      const res = await fetch('/api/v1/payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_id: 'cart_ent_9911', grand_total: 27201.68, simulate_fail: failover })
      });
      const data = await res.json();
      const outBox = document.getElementById('payment-response');
      outBox.classList.remove('hidden');
      outBox.innerHTML = '<pre class="text-emerald-400">' + JSON.stringify(data, null, 2) + '</pre>';
    }

    async function executeGenericModule() {
      const res = await fetch('/api/v1/' + currentTab, { method: 'POST' });
      const data = await res.json();
      const outBox = document.getElementById('generic-response');
      outBox.classList.remove('hidden');
      outBox.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }

    async function loadLedger() {
      const res = await fetch('/api/v1/ledger');
      const data = await res.json();
      const container = document.getElementById('ledger-nodes');
      container.innerHTML = '';
      data.chain.forEach(node => {
        const item = document.createElement('div');
        item.className = 'bg-slate-950 p-4 rounded-xl border border-slate-800 border-l-4 border-l-emerald-500';
        item.innerHTML = `
          <div class="flex justify-between font-bold text-slate-200">
            <span>Node #${node.index} (${node.feature_id})</span>
            <span class="text-slate-400">${new Date(node.timestamp * 1000).toLocaleTimeString()}</span>
          </div>
          <p class="mt-1 text-slate-300">Merkle Root: <span class="text-emerald-400 font-bold">${node.merkle_root}</span></p>
          <p class="text-slate-500 text-[11px]">Data Hash:   ${node.data_hash}</p>
        `;
        container.appendChild(item);
      });
    }

    window.onload = function() {
      loadLedger();
    };
  </script>
</body>
</html>
"""

class PolyEnterpriseRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content, status=200):
        body = html_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self._send_html(HTML_TEMPLATE)
        elif url.path == "/api/v1/ledger":
            chain_nodes = []
            for node in gov.ledger.chain:
                chain_nodes.append({
                    "index": node.index,
                    "timestamp": node.timestamp,
                    "feature_id": node.feature_id,
                    "merkle_root": node.merkle_root,
                    "data_hash": node.data_hash
                })
            self._send_json({"chain": chain_nodes, "valid": gov.ledger.verify_chain()[0]})
        elif url.path == "/api/v1/catalog":
            ast = parser.parse_file(str(app_dir / "03_product_inventory.poly"))
            block = find_block(ast, "python")
            res = runtime.execute_cell(block, {"query": "", "category": "all"})
            gov.audit_execution("03_product_inventory.poly", "catalog_api_view", {})
            self._send_json(res.output)
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        try:
            req_json = json.loads(post_data)
        except Exception:
            req_json = {}

        if url.path == "/api/v1/auth/login":
            ast = parser.parse_file(str(app_dir / "01_enterprise_auth.poly"))
            res = runtime.execute_cell(find_block(ast, "python", "service"), req_json)
            gov.audit_execution("01_enterprise_auth.poly", "auth_login_web", {"username": req_json.get("username")})
            self._send_json({"cell_result": res.output, "status": res.status})

        elif url.path == "/api/v1/payment":
            ast = parser.parse_file(str(app_dir / "06_multi_gateway_payment.poly"))
            res_py = runtime.execute_cell(find_block(ast, "python"), req_json)
            res_java = runtime.execute_cell(find_block(ast, "java"), req_json)
            res_go = runtime.execute_cell(find_block(ast, "go"), req_json)
            merged = merger.merge([res_py, res_java, res_go], ast.merge_strategy)
            gov.audit_execution("06_multi_gateway_payment.poly", "payment_processed_web", {"winner": merged.get("winner")})
            self._send_json({"merged_result": merged, "circuit_breaker_winner": merged.get("winner")})

        elif url.path in ("/api/v1/rbac", "/api/v1/user"):
            ast = parser.parse_file(str(app_dir / "02_user_management_rbac.poly"))
            res = runtime.execute_cell(find_block(ast, "python"), req_json)
            gov.audit_execution("02_user_management_rbac.poly", "rbac_web", {})
            self._send_json(res.output)

        elif url.path in ("/api/v1/pricing", "/api/v1/checkout", "/api/v1/fulfillment", "/api/v1/notifications", "/api/v1/risk", "/api/v1/soc2"):
            module_name = url.path.split("/")[-1]
            file_map = {
                "pricing": "04_pricing_discount_engine.poly",
                "checkout": "05_cart_checkout.poly",
                "fulfillment": "07_order_fulfillment_pipeline.poly",
                "notifications": "08_notification_omnichannel.poly",
                "risk": "09_risk_fraud_analytics.poly",
                "soc2": "10_soc2_compliance_merkle.poly"
            }
            fname = file_map.get(module_name, "04_pricing_discount_engine.poly")
            ast = parser.parse_file(str(app_dir / fname))
            res = runtime.execute_cell(find_block(ast, "python"), req_json)
            gov.audit_execution(fname, f"{module_name}_executed_web", {})
            self._send_json(res.output)
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, PolyEnterpriseRequestHandler)
    safe_print("=========================================================================")
    safe_print(f"POLYENTERPRISE LIVE INTERACTIVE WEB SERVER RUNNING")
    safe_print(f"URL: http://localhost:{port}")
    safe_print(f"Connected to PolyFlow Multi-Language Engine (.poly 10k lines architecture)")
    safe_print("=========================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        safe_print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
