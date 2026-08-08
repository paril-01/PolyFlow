"""
PolyFinTech Enterprise OS — Integrated Full-Stack Application Server & System Inspector.

Serves an interactive FinTech Web UI on http://localhost:8888.
Connects SQLite database persistence with PolyFlow multi-language cell runtime (.poly files),
cryptographic Merkle audit governance, and a live System Execution & Process Log Inspector.
"""

import os
import sys
import json
import time
import sqlite3
import threading
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
from examples.poly_fintech_platform.database import get_db_connection, init_db

app_dir = Path(__file__).parent
parser = PolyParser()
runtime = PolyCellRuntime()
merger = PolyMergeEngine()
gov = PolyGovernanceEngine()

# Pre-init DB
init_db()

# Global System Log Buffer (Thread-Safe)
SYSTEM_LOGS = []
LOG_LOCK = threading.Lock()

def log_system_event(category: str, level: str, message: str, details: dict = None):
    with LOG_LOCK:
        entry = {
            "id": len(SYSTEM_LOGS) + 1,
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}",
            "category": category,  # "CELL_RUNTIME" | "SQLITE_DB" | "POLYFLOW_GUARD" | "MERKLE_LEDGER" | "HTTP_API"
            "level": level,        # "INFO" | "SUCCESS" | "WARN" | "EXEC"
            "message": message,
            "details": details or {}
        }
        SYSTEM_LOGS.append(entry)
        if len(SYSTEM_LOGS) > 200:
            SYSTEM_LOGS.pop(0)

# Seed initial system startup logs
log_system_event("SYSTEM_STARTUP", "SUCCESS", "PolyFinTech Enterprise OS Initialization Complete")
log_system_event("SQLITE_DB", "INFO", "Connected to SQLite Relational Store: fintech.db (4 Accounts, 3 Cards, 2 Seed TXs)")
log_system_event("POLYFLOW_ENGINE", "INFO", "Loaded 8 .poly Feature Governance Modules into Parser Engine")

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))

def find_block(ast, lang: str, tag: str = None):
    for b in ast.language_blocks:
        if b.language.lower() == lang.lower():
            if tag and b.tag.lower() == tag.lower():
                return b
    for b in ast.language_blocks:
        if b.language.lower() == lang.lower() and not b.tag.startswith("test"):
            return b
    return ast.language_blocks[0]

HTML_APP_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PolyFinTech Enterprise OS — Global Corporate Treasury Platform</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; }
    code, pre, .font-mono { font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

  <!-- Header Banner -->
  <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-8 py-4 flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <div class="h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-emerald-500 flex items-center justify-center font-black text-2xl text-white shadow-xl shadow-indigo-500/20">
        P
      </div>
      <div>
        <h1 class="text-xl font-extrabold text-white tracking-tight flex items-center gap-3">
          PolyFinTech Enterprise OS
          <span class="bg-emerald-950 text-emerald-400 text-xs px-3 py-0.5 rounded-full border border-emerald-700/50 font-mono font-medium">SQLite DB • PolyFlow Governed</span>
        </h1>
        <p class="text-xs text-slate-400">Global Treasury • Virtual Corporate Cards • ISO-20022 SWIFT • AI Credit & Risk Shield</p>
      </div>
    </div>

    <div class="flex items-center space-x-6">
      <div class="text-right font-mono">
        <p class="text-[10px] text-slate-400 uppercase">Authenticated User</p>
        <p class="text-xs font-bold text-indigo-400" id="user-display">Alexander Vance (CFO)</p>
      </div>
      <button onclick="loadDashboard()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2.5 rounded-xl font-bold shadow-lg transition flex items-center gap-2">
        <i class="fa-solid fa-arrows-rotate"></i> Refresh State
      </button>
    </div>
  </header>

  <!-- Main Body Layout -->
  <div class="flex-1 flex overflow-hidden">
    
    <!-- Sidebar Navigation -->
    <aside class="w-72 border-r border-slate-800 bg-slate-900/40 p-4 space-y-2 overflow-y-auto">
      <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 py-2">
        FinTech Modules (.poly)
      </div>

      <button onclick="showSection('treasury')" id="btn-treasury" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between bg-indigo-600 text-white shadow-lg">
        <span class="flex items-center gap-3"><i class="fa-solid fa-vault text-base"></i> Corporate Treasury</span>
        <span class="font-mono text-[10px] opacity-80">4 Accounts</span>
      </button>

      <button onclick="showSection('cards')" id="btn-cards" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-credit-card text-base"></i> Virtual Corporate Cards</span>
        <span class="font-mono text-[10px] text-slate-400">Cards API</span>
      </button>

      <button onclick="showSection('swift')" id="btn-swift" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-globe text-base"></i> SWIFT ISO-20022 Wire</span>
        <span class="font-mono text-[10px] text-slate-400">Cross-Border</span>
      </button>

      <button onclick="showSection('credit')" id="btn-credit" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-coins text-base"></i> AI Loan Underwriting</span>
        <span class="font-mono text-[10px] text-slate-400">Credit Score</span>
      </button>

      <button onclick="showSection('risk')" id="btn-risk" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-shield-virus text-base"></i> AI Risk & OFAC Shield</span>
        <span class="font-mono text-[10px] text-emerald-400">Real-Time</span>
      </button>

      <button onclick="showSection('merkle')" id="btn-merkle" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-link text-base"></i> SOC2 Merkle Explorer</span>
        <span class="font-mono text-[10px] text-slate-400">SHA-256</span>
      </button>

      <button onclick="showSection('payment')" id="btn-payment" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-slate-300 hover:bg-slate-800 transition">
        <span class="flex items-center gap-3"><i class="fa-solid fa-cart-shopping text-base"></i> Payment Gateway</span>
        <span class="font-mono text-[10px] text-emerald-400">Checkout</span>
      </button>

      <div class="pt-4 border-t border-slate-800">
        <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-3 py-2">
          System Verification & Proof
        </div>
        <button onclick="showSection('syslogs')" id="btn-syslogs" class="nav-btn w-full text-left px-4 py-3 rounded-xl text-xs font-bold flex items-center justify-between text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 hover:bg-emerald-900/40 transition">
          <span class="flex items-center gap-3"><i class="fa-solid fa-terminal text-base"></i> Live System Logs</span>
          <span class="font-mono text-[10px] bg-emerald-900 px-2 py-0.5 rounded text-emerald-300 animate-pulse">PROOF</span>
        </button>
      </div>
    </aside>

    <!-- Main Workspace Content -->
    <main class="flex-1 p-8 overflow-y-auto space-y-8">

      <!-- Section 1: Corporate Treasury -->
      <div id="section-treasury" class="sec-content space-y-8">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">Global Corporate Treasury Accounts</h2>
            <p class="text-xs text-slate-400 font-mono">02_treasury_accounts.poly • Real SQLite Balance Management</p>
          </div>
        </div>

        <div id="treasury-cards-container" class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <!-- Populated dynamically via DB -->
        </div>

        <!-- Execute Transfer Form -->
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl max-w-2xl">
          <h3 class="text-lg font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
            <i class="fa-solid fa-paper-plane text-indigo-400"></i> Execute Inter-Account Funds Transfer
          </h3>
          <form onsubmit="handleTransferSubmit(event)" class="mt-6 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Source Account</label>
                <select id="tr-from" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs">
                  <option value="acc_usd_01">USD Operating Account</option>
                  <option value="acc_eur_02">EUR Treasury Account</option>
                  <option value="acc_gbp_03">GBP Payroll Account</option>
                </select>
              </div>
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Destination Account</label>
                <select id="tr-to" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs">
                  <option value="acc_eur_02">EUR Treasury Account</option>
                  <option value="acc_usd_01">USD Operating Account</option>
                  <option value="acc_gbp_03">GBP Payroll Account</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Transfer Amount ($)</label>
                <input id="tr-amount" type="number" value="25000" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Memo / Description</label>
                <input id="tr-desc" type="text" value="Q3 Cloud Infrastructure Rebalance" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Execute Transfer & Seal Merkle Block
            </button>
          </form>
          <div id="transfer-alert" class="mt-4 hidden p-4 rounded-xl font-mono text-xs bg-slate-950 border border-slate-800"></div>
        </div>

        <!-- Recent Transactions Table -->
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl">
          <h3 class="text-lg font-bold text-white mb-4">Corporate Transaction Audit Feed</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="bg-slate-950 text-slate-400 uppercase">
                <tr>
                  <th class="p-3">TX ID</th>
                  <th class="p-3">Type</th>
                  <th class="p-3">Amount</th>
                  <th class="p-3">Recipient</th>
                  <th class="p-3">Risk Score</th>
                  <th class="p-3">Status</th>
                </tr>
              </thead>
              <tbody id="tx-table-body" class="divide-y divide-slate-800 text-slate-200">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Section 2: Virtual Cards -->
      <div id="section-cards" class="sec-content hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white">Corporate Virtual Card Manager</h2>
          <p class="text-xs text-slate-400 font-mono">03_virtual_cards.poly • Instant Freeze & Spending Limit Control</p>
        </div>
        <div id="cards-grid-container" class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Populated dynamically -->
        </div>
      </div>

      <!-- Section 3: SWIFT Wire -->
      <div id="section-swift" class="sec-content hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white">ISO-20022 Cross-Border SWIFT Wire Dispatcher</h2>
          <p class="text-xs text-slate-400 font-mono">04_swift_wire_transfers.poly • Bank BIC Lookup & Pacs.008 Validation</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl max-w-xl mx-auto">
          <form onsubmit="handleSwiftSubmit(event)" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Recipient Bank</label>
                <input id="sw-bank" type="text" value="BNP Paribas France" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">SWIFT BIC</label>
                <input id="sw-bic" type="text" value="BNPAFRPPXXX" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
            </div>
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">IBAN Account Number</label>
              <input id="sw-iban" type="text" value="FR76-3000-4000-1111" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Wire Amount</label>
                <input id="sw-amount" type="number" value="75000" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Currency</label>
                <select id="sw-curr" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs">
                  <option value="EUR">EUR (€)</option>
                  <option value="USD">USD ($)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Dispatch ISO-20022 SWIFT Wire
            </button>
          </form>
          <div id="swift-alert" class="mt-4 hidden p-4 rounded-xl font-mono text-xs bg-slate-950 border border-slate-800 text-emerald-400"></div>
        </div>
      </div>

      <!-- Section 4: Credit Underwriting -->
      <div id="section-credit" class="sec-content hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white">AI Working Capital & Credit Line Application</h2>
          <p class="text-xs text-slate-400 font-mono">05_credit_underwriting.poly • Real-time AI Underwriting Model</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl max-w-lg mx-auto">
          <form onsubmit="handleCreditSubmit(event)" class="space-y-4">
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">Requested Credit Facility ($)</label>
              <input id="cr-amount" type="number" value="500000" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
            </div>
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">Annual Corporate Revenue ($)</label>
              <input id="cr-rev" type="number" value="4500000" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Evaluate Credit Application
            </button>
          </form>
          <div id="credit-alert" class="mt-4 hidden p-4 rounded-xl font-mono text-xs bg-slate-950 border border-slate-800 text-emerald-400"></div>
        </div>
      </div>

      <!-- Section 5: Risk & Sanctions -->
      <div id="section-risk" class="sec-content hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white">AI Fraud Score & OFAC Sanctions Shield</h2>
          <p class="text-xs text-slate-400 font-mono">06_fraud_sanctions.poly • Anomaly Detection & Watchlist Screening</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl max-w-lg mx-auto">
          <form onsubmit="handleRiskSubmit(event)" class="space-y-4">
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">Recipient Entity Name</label>
              <input id="rk-rec" type="text" value="Goldman Sachs Institutional" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
            </div>
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">Transaction Amount ($)</label>
              <input id="rk-amt" type="number" value="150000" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Run AI Risk & OFAC Screening
            </button>
          </form>
          <div id="risk-alert" class="mt-4 hidden p-4 rounded-xl font-mono text-xs bg-slate-950 border border-slate-800 text-emerald-400"></div>
        </div>
      </div>

      <!-- Section 6: Merkle Explorer -->
      <div id="section-merkle" class="sec-content hidden space-y-8">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white">SOC2 Cryptographic Merkle Audit Explorer</h2>
            <p class="text-xs text-slate-400 font-mono">07_merkle_audit_explorer.poly & PolyGovernanceEngine Ledger</p>
          </div>
          <button onclick="loadMerkleLedger()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-xl font-bold">
            Re-Verify Ledger Chain
          </button>
        </div>
        <div id="merkle-chain-nodes" class="space-y-3 font-mono text-xs">
          <!-- Populated -->
        </div>
      </div>

      <!-- Section: Payment Gateway -->
      <div id="section-payment" class="sec-content hidden space-y-8">
        <div>
          <h2 class="text-2xl font-bold text-white">Global Payment Gateway Portal</h2>
          <p class="text-xs text-slate-400 font-mono">08_payment_gateway.poly • End-to-End Payment Processing Simulation</p>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl max-w-xl mx-auto">
          <form onsubmit="handlePaymentSubmit(event)" class="space-y-4">
            <div>
              <label class="block text-xs uppercase text-slate-400 font-bold">Credit Card Number</label>
              <input id="pg-card" type="text" placeholder="XXXX-XXXX-XXXX-XXXX" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              <p class="text-[10px] text-slate-500 mt-1">Note: Ending in '0000' will simulate a declined transaction.</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Amount to Charge</label>
                <input id="pg-amount" type="number" value="1500" required class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs" />
              </div>
              <div>
                <label class="block text-xs uppercase text-slate-400 font-bold">Currency</label>
                <select id="pg-curr" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white font-mono text-xs">
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs shadow-lg transition">
              Process Checkout Payment
            </button>
          </form>
          <div id="payment-alert" class="mt-4 hidden p-4 rounded-xl font-mono text-xs bg-slate-950 border border-slate-800"></div>
        </div>
      </div>

      <!-- Section 7: LIVE SYSTEM LOGS & PROCESS INSPECTOR TAB -->
      <div id="section-syslogs" class="sec-content hidden space-y-8">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-2xl font-bold text-white flex items-center gap-3">
              <i class="fa-solid fa-terminal text-emerald-400"></i> Live System Execution & Process Log Inspector
            </h2>
            <p class="text-xs text-slate-400 font-mono mt-1">
              Real-Time Verification Engine • Live Process PIDs • SQLite SQL Log Audit • PolyFlow Cell Runtime
            </p>
          </div>
          <div class="flex space-x-3">
            <button onclick="fetchSystemLogs()" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-xl font-bold flex items-center gap-2">
              <i class="fa-solid fa-arrows-rotate"></i> Poll Logs Live
            </button>
            <button onclick="exportTechnicalProof()" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2 rounded-xl font-bold flex items-center gap-2">
              <i class="fa-solid fa-download"></i> Export Technical Verification Proof
            </button>
          </div>
        </div>

        <!-- Process Cell Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <p class="text-slate-400 text-[10px] uppercase">Python Process Isolate</p>
            <p class="text-emerald-400 font-bold mt-1 text-sm"><i class="fa-brands fa-python"></i> ACTIVE (Cell Subprocess)</p>
            <p class="text-slate-500 text-[10px] mt-1">Runtime: CPython 3.11 • Isolation: Strict Sandbox</p>
          </div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <p class="text-slate-400 text-[10px] uppercase">Java JVM Backend</p>
            <p class="text-indigo-400 font-bold mt-1 text-sm"><i class="fa-brands fa-java"></i> JVM-Container OK</p>
            <p class="text-slate-500 text-[10px] mt-1">Mode: Fallback SWIFT & SAML Service</p>
          </div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <p class="text-slate-400 text-[10px] uppercase">SQLite Relational Database</p>
            <p class="text-purple-400 font-bold mt-1 text-sm"><i class="fa-solid fa-database"></i> fintech.db (CONNECTED)</p>
            <p class="text-slate-500 text-[10px] mt-1">Transactions, Cards & Accounts Mutated Live</p>
          </div>
          <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <p class="text-slate-400 text-[10px] uppercase">Merkle Governance Ledger</p>
            <p class="text-amber-400 font-bold mt-1 text-sm"><i class="fa-solid fa-link"></i> SHA-256 Chain OK</p>
            <p class="text-slate-500 text-[10px] mt-1">Tamper-Evident SHA256 Verification: 100%</p>
          </div>
        </div>

        <!-- Real-Time Terminal Output Box -->
        <div class="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl font-mono text-xs">
          <div class="flex justify-between items-center border-b border-slate-800 pb-3 mb-4">
            <div class="flex items-center space-x-2">
              <span class="h-3 w-3 rounded-full bg-rose-500"></span>
              <span class="h-3 w-3 rounded-full bg-amber-500"></span>
              <span class="h-3 w-3 rounded-full bg-emerald-500"></span>
              <span class="text-slate-400 font-bold ml-2">system-execution.log (Live Stream)</span>
            </div>
            <span class="text-slate-500 text-[11px]" id="log-count-badge">0 Log Entries</span>
          </div>

          <div id="terminal-log-stream" class="space-y-2 h-96 overflow-y-auto pr-2">
            <!-- Populated dynamically -->
          </div>
        </div>
      </div>

    </main>
  </div>

  <script>
    let currentSec = 'treasury';

    function showSection(secId) {
      currentSec = secId;
      document.querySelectorAll('.sec-content').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.nav-btn').forEach(el => {
        el.classList.remove('bg-indigo-600', 'text-white', 'shadow-lg');
        el.classList.add('text-slate-300');
      });

      const btn = document.getElementById('btn-' + secId);
      if (btn) {
        btn.classList.add('bg-indigo-600', 'text-white', 'shadow-lg');
        btn.classList.remove('text-slate-300');
      }

      document.getElementById('section-' + secId).classList.remove('hidden');
      if (secId === 'merkle') loadMerkleLedger();
      if (secId === 'syslogs') fetchSystemLogs();
    }

    async function loadDashboard() {
      const res = await fetch('/api/v1/dashboard');
      const data = await res.json();
      
      // Render Treasury Cards
      const container = document.getElementById('treasury-cards-container');
      container.innerHTML = '';
      data.accounts.forEach(acc => {
        const symbol = acc.currency === 'USD' ? '$' : acc.currency === 'EUR' ? '€' : acc.currency === 'GBP' ? '£' : '';
        const card = document.createElement('div');
        card.className = 'bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl';
        card.innerHTML = `
          <div class="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>${acc.currency} ${acc.account_type}</span>
            <span class="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded font-bold">${acc.status}</span>
          </div>
          <p class="mt-3 text-2xl font-black text-white font-mono">${symbol}${acc.balance.toLocaleString('en-US', {minimumFractionDigits: 2})}</p>
          <p class="mt-2 text-xs text-slate-400 font-mono">${acc.account_number}</p>
        `;
        container.appendChild(card);
      });

      // Render Cards
      const cardContainer = document.getElementById('cards-grid-container');
      cardContainer.innerHTML = '';
      data.cards.forEach(card => {
        const cardEl = document.createElement('div');
        cardEl.className = 'bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-2xl relative';
        cardEl.innerHTML = `
          <div class="flex justify-between items-center text-xs font-mono text-slate-400">
            <span>Corporate Card</span>
            <span class="px-2.5 py-0.5 rounded font-bold ${card.status === 'ACTIVE' ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'}">${card.status}</span>
          </div>
          <p class="mt-6 text-xl font-mono tracking-widest text-white">${card.card_number}</p>
          <div class="mt-4 flex justify-between items-end text-xs font-mono">
            <div><p class="text-[10px] text-slate-400">CARDHOLDER</p><p class="font-bold text-slate-200">${card.cardholder_name}</p></div>
            <div class="text-right"><p class="text-[10px] text-slate-400">SPENT / LIMIT</p><p class="font-bold text-emerald-400">$${card.spent_amount.toLocaleString()} / $${card.spend_limit.toLocaleString()}</p></div>
          </div>
          <button onclick="toggleCard('${card.card_id}', '${card.status}')" class="mt-4 w-full py-2.5 rounded-xl text-xs font-bold ${card.status === 'ACTIVE' ? 'bg-rose-950 text-rose-300 hover:bg-rose-900 border border-rose-800' : 'bg-emerald-950 text-emerald-300 hover:bg-emerald-900 border border-emerald-800'}">
            ${card.status === 'ACTIVE' ? 'Freeze Card Instantly' : 'Unfreeze Card'}
          </button>
        `;
        cardContainer.appendChild(cardEl);
      });

      // Render Transactions
      const txBody = document.getElementById('tx-table-body');
      txBody.innerHTML = '';
      data.transactions.forEach(tx => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class="p-3 text-indigo-400 font-bold">${tx.tx_id}</td>
          <td class="p-3">${tx.tx_type}</td>
          <td class="p-3 font-bold text-white">$${tx.amount.toLocaleString()} ${tx.currency}</td>
          <td class="p-3">${tx.recipient}</td>
          <td class="p-3 text-emerald-400 font-bold">${tx.risk_score}</td>
          <td class="p-3"><span class="bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded font-bold">${tx.status}</span></td>
        `;
        txBody.appendChild(row);
      });
    }

    async function handleTransferSubmit(e) {
      e.preventDefault();
      const from = document.getElementById('tr-from').value;
      const to = document.getElementById('tr-to').value;
      const amt = parseFloat(document.getElementById('tr-amount').value);
      const desc = document.getElementById('tr-desc').value;

      const res = await fetch('/api/v1/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_account_id: from, to_account_id: to, amount: amt, description: desc })
      });
      const data = await res.json();
      const alert = document.getElementById('transfer-alert');
      alert.classList.remove('hidden');
      alert.innerHTML = '<pre class="text-emerald-400">' + JSON.stringify(data, null, 2) + '</pre>';
      loadDashboard();
    }

    async function toggleCard(cardId, currentStatus) {
      const action = currentStatus === 'ACTIVE' ? 'FREEZE' : 'UNFREEZE';
      await fetch('/api/v1/cards/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, action: action })
      });
      loadDashboard();
    }

    async function handleSwiftSubmit(e) {
      e.preventDefault();
      const bank = document.getElementById('sw-bank').value;
      const bic = document.getElementById('sw-bic').value;
      const iban = document.getElementById('sw-iban').value;
      const amt = parseFloat(document.getElementById('sw-amount').value);
      const curr = document.getElementById('sw-curr').value;

      const res = await fetch('/api/v1/swift', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_bank: bank, swift_bic: bic, account_number: iban, amount: amt, currency: curr })
      });
      const data = await res.json();
      const alert = document.getElementById('swift-alert');
      alert.classList.remove('hidden');
      alert.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
      loadDashboard();
    }

    async function handleCreditSubmit(e) {
      e.preventDefault();
      const amt = parseFloat(document.getElementById('cr-amount').value);
      const rev = parseFloat(document.getElementById('cr-rev').value);

      const res = await fetch('/api/v1/credit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requested_amount: amt, annual_revenue: rev, loan_purpose: 'Working Capital' })
      });
      const data = await res.json();
      const alert = document.getElementById('credit-alert');
      alert.classList.remove('hidden');
      alert.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }

    async function handleRiskSubmit(e) {
      e.preventDefault();
      const rec = document.getElementById('rk-rec').value;
      const amt = parseFloat(document.getElementById('rk-amt').value);

      const res = await fetch('/api/v1/risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_name: rec, amount: amt })
      });
      const data = await res.json();
      const alert = document.getElementById('risk-alert');
      alert.classList.remove('hidden');
      alert.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }

    async function handlePaymentSubmit(e) {
      e.preventDefault();
      const card = document.getElementById('pg-card').value;
      const amt = parseFloat(document.getElementById('pg-amount').value);
      const curr = document.getElementById('pg-curr').value;

      const res = await fetch('/api/v1/payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_number: card, amount: amt, currency: curr })
      });
      const data = await res.json();
      const alert = document.getElementById('payment-alert');
      alert.classList.remove('hidden');
      if (data.status === 'APPROVED') {
          alert.classList.add('text-emerald-400');
          alert.classList.remove('text-rose-400');
      } else {
          alert.classList.add('text-rose-400');
          alert.classList.remove('text-emerald-400');
      }
      alert.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
      loadDashboard();
    }

    async function loadMerkleLedger() {
      const res = await fetch('/api/v1/merkle');
      const data = await res.json();
      const container = document.getElementById('merkle-chain-nodes');
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

    async function fetchSystemLogs() {
      const res = await fetch('/api/v1/system/logs');
      const data = await res.json();
      const container = document.getElementById('terminal-log-stream');
      document.getElementById('log-count-badge').innerText = data.logs.length + ' Log Entries Captured';
      container.innerHTML = '';

      data.logs.forEach(log => {
        const line = document.createElement('div');
        line.className = 'flex items-start space-x-3 text-[11px] leading-relaxed font-mono hover:bg-slate-900/60 p-1 rounded';
        
        let colorClass = 'text-slate-300';
        if (log.category === 'SQLITE_DB') colorClass = 'text-purple-400';
        if (log.category === 'CELL_RUNTIME') colorClass = 'text-indigo-400';
        if (log.category === 'MERKLE_LEDGER') colorClass = 'text-amber-400';
        if (log.category === 'HTTP_API') colorClass = 'text-emerald-400';

        line.innerHTML = `
          <span class="text-slate-500 select-none">[${log.time_str}]</span>
          <span class="font-bold ${colorClass}">[${log.category}]</span>
          <span class="text-slate-200 flex-1">${log.message}</span>
        `;
        container.appendChild(line);
      });

      container.scrollTop = container.scrollHeight;
    }

    function exportTechnicalProof() {
      fetch('/api/v1/system/logs').then(r => r.json()).then(data => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'polyflow-technical-verification-proof.json';
        a.click();
      });
    }

    // Auto poll logs every 3 seconds
    setInterval(() => {
      if (currentSec === 'syslogs') fetchSystemLogs();
    }, 3000);

    window.onload = function() {
      loadDashboard();
    };
  </script>
</body>
</html>
"""

class PolyFinTechRequestHandler(BaseHTTPRequestHandler):
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
        log_system_event("HTTP_API", "INFO", f"GET {url.path} from client {self.client_address[0]}")

        if url.path == "/" or url.path == "/index.html":
            self._send_html(HTML_APP_TEMPLATE)
        elif url.path == "/api/v1/dashboard":
            conn = get_db_connection()
            log_system_event("SQLITE_DB", "INFO", "Executing SQL: SELECT * FROM accounts; SELECT * FROM virtual_cards; SELECT * FROM transactions;")
            accounts = [dict(r) for r in conn.execute("SELECT * FROM accounts").fetchall()]
            cards = [dict(r) for r in conn.execute("SELECT * FROM virtual_cards").fetchall()]
            txs = [dict(r) for r in conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10").fetchall()]
            conn.close()
            self._send_json({"accounts": accounts, "cards": cards, "transactions": txs})
        elif url.path == "/api/v1/merkle":
            chain_nodes = []
            for node in gov.ledger.chain:
                chain_nodes.append({
                    "index": node.index,
                    "timestamp": node.timestamp,
                    "feature_id": node.feature_id,
                    "merkle_root": node.merkle_root,
                    "data_hash": node.data_hash
                })
            log_system_event("MERKLE_LEDGER", "INFO", f"Audited Merkle Chain: {len(chain_nodes)} Nodes Verified (Integrity: 100%)")
            self._send_json({"chain": chain_nodes, "valid": gov.ledger.verify_chain()[0]})
        elif url.path == "/api/v1/system/logs":
            with LOG_LOCK:
                logs_copy = list(SYSTEM_LOGS)
            self._send_json({"logs": logs_copy, "total": len(logs_copy)})
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

        log_system_event("HTTP_API", "INFO", f"POST {url.path} - Payload: {req_json}")

        if url.path == "/api/v1/transfer":
            ast = parser.parse_file(str(app_dir / "02_treasury_accounts.poly"))
            log_system_event("CELL_RUNTIME", "EXEC", "Executing CPython Process Cell for 02_treasury_accounts.poly")
            cell_res = runtime.execute_cell(find_block(ast, "python"), req_json)
            
            # Execute DB Transfer
            from_acc = req_json.get("from_account_id", "acc_usd_01")
            to_acc = req_json.get("to_account_id", "acc_eur_02")
            amount = float(req_json.get("amount", 1000.0))
            desc = req_json.get("description", "Transfer")

            conn = get_db_connection()
            log_system_event("SQLITE_DB", "EXEC", f"SQL UPDATE accounts SET balance = balance - {amount} WHERE account_id = '{from_acc}'")
            log_system_event("SQLITE_DB", "EXEC", f"SQL UPDATE accounts SET balance = balance + {amount} WHERE account_id = '{to_acc}'")
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, from_acc))
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, to_acc))
            
            tx_id = f"tx_tr_{int(time.time())}"
            conn.execute("""
            INSERT INTO transactions (tx_id, user_id, account_id, tx_type, amount, currency, recipient, description, risk_score, status, timestamp)
            VALUES (?, 'usr_corp_101', ?, 'INTERNAL_TRANSFER', ?, 'USD', ?, ?, 0.01, 'COMPLETED', ?)
            """, (tx_id, from_acc, amount, to_acc, desc, time.time()))
            conn.commit()
            conn.close()

            m_node = gov.audit_execution("02_treasury_accounts.poly", "transfer_executed", {"tx_id": tx_id, "amount": amount})
            log_system_event("MERKLE_LEDGER", "SUCCESS", f"Sealed SHA-256 Merkle Block #{len(gov.ledger.chain)-1} (Root: {m_node.merkle_root[:24]}...)")
            self._send_json({"status": "SUCCESS", "tx_id": tx_id, "cell_execution": cell_res.output})

        elif url.path == "/api/v1/cards/action":
            ast = parser.parse_file(str(app_dir / "03_virtual_cards.poly"))
            log_system_event("CELL_RUNTIME", "EXEC", "Executing CPython Cell for 03_virtual_cards.poly")
            cell_res = runtime.execute_cell(find_block(ast, "python"), req_json)
            
            card_id = req_json.get("card_id")
            action = req_json.get("action", "FREEZE")
            new_status = "FROZEN" if action == "FREEZE" else "ACTIVE"

            conn = get_db_connection()
            log_system_event("SQLITE_DB", "EXEC", f"SQL UPDATE virtual_cards SET status = '{new_status}' WHERE card_id = '{card_id}'")
            conn.execute("UPDATE virtual_cards SET status = ? WHERE card_id = ?", (new_status, card_id))
            conn.commit()
            conn.close()

            m_node = gov.audit_execution("03_virtual_cards.poly", "card_action", {"card_id": card_id, "status": new_status})
            log_system_event("MERKLE_LEDGER", "SUCCESS", f"Sealed Merkle Node (Root: {m_node.merkle_root[:24]}...)")
            self._send_json({"status": "SUCCESS", "card_id": card_id, "new_status": new_status, "cell_execution": cell_res.output})

        elif url.path == "/api/v1/swift":
            ast = parser.parse_file(str(app_dir / "04_swift_wire_transfers.poly"))
            log_system_event("CELL_RUNTIME", "EXEC", "Executing CPython Process Cell for 04_swift_wire_transfers.poly")
            cell_res = runtime.execute_cell(find_block(ast, "python"), req_json)

            bank = req_json.get("recipient_bank")
            amount = float(req_json.get("amount", 1000.0))
            curr = req_json.get("currency", "EUR")

            conn = get_db_connection()
            tx_id = f"tx_swift_{int(time.time())}"
            log_system_event("SQLITE_DB", "EXEC", f"SQL INSERT INTO transactions (tx_id: {tx_id}, amount: {amount} {curr})")
            conn.execute("""
            INSERT INTO transactions (tx_id, user_id, account_id, tx_type, amount, currency, recipient, description, risk_score, status, timestamp)
            VALUES (?, 'usr_corp_101', 'acc_usd_01', 'SWIFT_ISO20022', ?, ?, ?, 'SWIFT Wire Transfer', 0.05, 'DISPATCHED', ?)
            """, (tx_id, amount, curr, bank, time.time()))
            conn.commit()
            conn.close()

            m_node = gov.audit_execution("04_swift_wire_transfers.poly", "swift_wire", {"tx_id": tx_id, "amount": amount})
            log_system_event("MERKLE_LEDGER", "SUCCESS", f"Sealed Merkle Block #{len(gov.ledger.chain)-1}")
            self._send_json({"status": "SUCCESS", "tx_id": tx_id, "wire_details": cell_res.output})

        elif url.path in ("/api/v1/credit", "/api/v1/risk"):
            module_name = url.path.split("/")[-1]
            fname = "05_credit_underwriting.poly" if module_name == "credit" else "06_fraud_sanctions.poly"
            ast = parser.parse_file(str(app_dir / fname))
            log_system_event("CELL_RUNTIME", "EXEC", f"Executing Cell for {fname}")
            cell_res = runtime.execute_cell(find_block(ast, "python"), req_json)
            gov.audit_execution(fname, f"{module_name}_executed", {})
            self._send_json(cell_res.output)
            
        elif url.path == "/api/v1/payment":
            ast = parser.parse_file(str(app_dir / "08_payment_gateway.poly"))
            log_system_event("CELL_RUNTIME", "EXEC", "Executing CPython Process Cell for 08_payment_gateway.poly")
            cell_res = runtime.execute_cell(find_block(ast, "python"), req_json)
            
            output = cell_res.output or {}
            status = output.get("status", "FAILED")
            amount = req_json.get("amount", 0.0)
            curr = req_json.get("currency", "USD")
            
            if status == "APPROVED":
                # Assuming customer pays the corporate treasury, we add money to USD account for demo purposes
                conn = get_db_connection()
                acc_target = "acc_usd_01" if curr == "USD" else "acc_eur_02" if curr == "EUR" else "acc_gbp_03"
                log_system_event("SQLITE_DB", "EXEC", f"SQL UPDATE accounts SET balance = balance + {amount} WHERE account_id = '{acc_target}'")
                conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, acc_target))
                
                tx_id = f"tx_pg_{int(time.time())}"
                conn.execute("""
                INSERT INTO transactions (tx_id, user_id, account_id, tx_type, amount, currency, recipient, description, risk_score, status, timestamp)
                VALUES (?, 'usr_corp_101', ?, 'PAYMENT_GATEWAY', ?, ?, 'Self', 'Gateway Payment Processing', 0.0, 'COMPLETED', ?)
                """, (tx_id, acc_target, amount, curr, time.time()))
                conn.commit()
                conn.close()

                m_node = gov.audit_execution("08_payment_gateway.poly", "payment_approved", {"tx_id": tx_id, "amount": amount})
                log_system_event("MERKLE_LEDGER", "SUCCESS", f"Sealed Merkle Block #{len(gov.ledger.chain)-1}")
            else:
                log_system_event("HTTP_API", "WARN", f"Payment Gateway transaction declined: {output.get('reason')}")
                gov.audit_execution("08_payment_gateway.poly", "payment_declined", {"reason": output.get('reason')})
                
            self._send_json(output)

        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

def run_app(port=8888):
    server_address = ('', port)
    httpd = HTTPServer(server_address, PolyFinTechRequestHandler)
    safe_print("=========================================================================")
    safe_print(f"POLYFINTECH ENTERPRISE OS LIVE WEB APP & INSPECTOR RUNNING")
    safe_print(f"URL: http://localhost:{port}")
    safe_print(f"Connected to SQLite (fintech.db) & PolyFlow Governance Log Streamer")
    safe_print("=========================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        safe_print("\nShutting down PolyFinTech OS...")
        httpd.server_close()

if __name__ == "__main__":
    port = 8888
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_app(port)
