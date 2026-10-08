// showcase_app/frontend/js/proofs.js — Tab 04: Proofs & Evidence Registry

const ProofsModule = {
  csvList: [
    { name: "run_summary.csv", desc: "Benchmark execution & gatekeeper accounting" },
    { name: "paired_token_usage.csv", desc: "Paired baseline vs RCIR input and total tokens" },
    { name: "agent_trials.csv", desc: "All 10 individual agent trial traces and results" },
    { name: "retrieved_files.csv", desc: "RCIR top-ranked context candidate files" },
    { name: "feature_closure.csv", desc: "5 representative ERPNext feature closures" },
    { name: "source_mappings.csv", desc: "78 native artifact to .poly symbol mappings" },
    { name: "interpreter_events.csv", desc: "PolyCell execution and fallback event log" },
    { name: "runtime_receipts.csv", desc: "Cryptographic SHA-256 execution receipts" },
    { name: "coverage_ledger.csv", desc: "ERPNext multi-tier architecture coverage ledger" }
  ],

  init() {
    const btnRefresh = document.getElementById("btn-refresh-proofs");
    const btnCloseModal = document.getElementById("btn-close-modal");

    if (btnRefresh) btnRefresh.onclick = () => this.loadProofs();
    if (btnCloseModal) btnCloseModal.onclick = () => this.closeModal();

    this.renderCSVHub();
    this.loadProofs();
  },

  renderCSVHub() {
    const grid = document.getElementById("csv-links-grid");
    if (!grid) return;
    grid.innerHTML = "";

    this.csvList.forEach(item => {
      const card = document.createElement("div");
      card.className = "metric-card";
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.justifyContent = "space-between";
      card.innerHTML = `
        <div>
          <div style="font-weight: 600; font-family: var(--font-mono); font-size: 13px; color: var(--accent-blue);">${item.name}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">${item.desc}</div>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 12px;">
          <button class="btn btn-outline btn-sm" onclick="ProofsModule.viewCSV('${item.name}')">Preview</button>
          <a href="/data/csv/${item.name}" download class="btn btn-outline btn-sm">Download</a>
        </div>
      `;
      grid.appendChild(card);
    });
  },

  async loadProofs() {
    try {
      const res = await fetch("/api/proofs");
      if (!res.ok) throw new Error("Failed to load proofs");
      const data = await res.json();
      this.renderProofsTable(data.proofs || []);
      const countEl = document.getElementById("proofs-count-val");
      if (countEl) countEl.textContent = (data.proofs || []).length;
    } catch (err) {
      console.error("Proofs load error:", err);
    }
  },

  renderProofsTable(proofs) {
    const tbody = document.getElementById("tbody-proofs-registry");
    if (!tbody) return;
    tbody.innerHTML = "";

    proofs.forEach(p => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family: var(--font-mono); font-size: 11px;">${p.proof_id}</td>
        <td style="font-weight: 500;">${p.title}</td>
        <td><span class="brand-badge" style="font-size: 10px;">${p.mime_type.split("/")[1] || "file"}</span></td>
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${p.sha256 ? p.sha256.substring(0, 16) + '...' : 'DYNAMIC'}</td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-outline btn-sm" onclick="ProofsModule.openProof('${p.proof_id}')">Open</button>
            <a href="${p.safe_url}/download" class="btn btn-outline btn-sm">Download</a>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  async openProof(proofId) {
    try {
      const res = await fetch(`/api/proofs/${proofId}`);
      if (!res.ok) throw new Error("Proof not found or integrity check failed");
      const text = await res.text();
      this.openModal(text, `Proof: ${proofId}`);
    } catch (err) {
      alert("Error loading proof: " + err.message);
    }
  },

  async viewCSV(filename) {
    try {
      const res = await fetch(`/data/csv/${filename}`);
      if (!res.ok) throw new Error("CSV not found");
      const text = await res.text();
      this.openModal(text, `Dataset: ${filename}`);
    } catch (err) {
      alert("Error loading CSV: " + err.message);
    }
  },

  openModal(content, title) {
    const modal = document.getElementById("proof-modal");
    const titleEl = document.getElementById("modal-proof-title");
    const contentEl = document.getElementById("modal-proof-content");

    if (titleEl) titleEl.textContent = title || "Proof Viewer";
    if (contentEl) contentEl.textContent = content || "No content available.";
    if (modal) modal.classList.add("open");
  },

  closeModal() {
    const modal = document.getElementById("proof-modal");
    if (modal) modal.classList.remove("open");
  }
};
