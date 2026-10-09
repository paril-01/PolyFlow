// showcase_app/frontend/js/app.js — Showcase Application Coordinator

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Tab navigation
  const tabButtons = document.querySelectorAll(".nav-tabs .tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.dataset.tab;

      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(targetTabId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // 2. Check Backend Health
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const health = await res.json();
      const statusEl = document.getElementById("backend-status-text");
      if (statusEl) {
        statusEl.innerHTML = `Run: run_20261009_blind_verified &bull; Target: da57df07 &bull; Evidence: ${health.evidence_status || 'VALIDATED'}`;
      }
    }
  } catch (err) {
    const statusEl = document.getElementById("backend-status-text");
    if (statusEl) {
      statusEl.innerHTML = "Offline &bull; Target: da57df07 &bull; Evidence: STATIC_FIXTURES";
      statusEl.style.color = "var(--text-muted)";
    }
  }

  // 3. Initialize feature modules
  PolyFlowModule.init();
  InterpreterModule.init();
  RCIRModule.init();
  ProofsModule.init();
  ERPNextModule.init();
});
