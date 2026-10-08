// showcase_app/frontend/js/interpreter.js — Tab 02: Real-time Animated Workflow

const InterpreterModule = {
  currentEventSource: null,
  latestReceipt: null,

  init() {
    const btnNormal = document.getElementById("btn-run-normal");
    const btnFailure = document.getElementById("btn-run-failure");
    const btnCopy = document.getElementById("btn-copy-receipt");

    if (btnNormal) btnNormal.onclick = () => this.runWorkflow("normal");
    if (btnFailure) btnFailure.onclick = () => this.runWorkflow("failure");
    if (btnCopy) {
      btnCopy.onclick = () => {
        if (this.latestReceipt) {
          navigator.clipboard.writeText(JSON.stringify(this.latestReceipt, null, 2));
          alert("Receipt copied to clipboard.");
        }
      };
    }
  },

  resetUI() {
    const nodes = document.querySelectorAll("#workflow-diagram .workflow-node");
    nodes.forEach(n => {
      n.className = "workflow-node";
    });

    document.getElementById("interp-status-val").textContent = "RUNNING";
    document.getElementById("interp-status-val").style.color = "var(--text-primary)";
    document.getElementById("interp-status-sub").textContent = "Live execution in progress";
    document.getElementById("interp-latency-val").textContent = "-- ms";
    document.getElementById("interp-cells-val").textContent = "0 / 5";
    document.getElementById("interp-fallback-sub").textContent = "0 fallbacks triggered";
    document.getElementById("interp-timeline").innerHTML = "";
    document.getElementById("interp-receipt-view").textContent = "Executing cells in sandboxed runtime...";
  },

  async runWorkflow(mode) {
    if (this.currentEventSource) {
      this.currentEventSource.close();
    }

    this.resetUI();
    const runId = "interp_" + Date.now();
    const timelineEl = document.getElementById("interp-timeline");

    // Connect to backend SSE endpoint
    const url = `/api/interpreter/runs/${runId}/events?mode=${mode}`;
    const eventSource = new EventSource(url);
    this.currentEventSource = eventSource;

    let cellsCount = 0;
    let fallbackCount = 0;

    eventSource.onmessage = (e) => {
      if (e.data === "[DONE]") {
        eventSource.close();
        return;
      }

      try {
        const evt = JSON.parse(e.data);
        this.handleEvent(evt, mode, timelineEl, cellsCount, fallbackCount);
        if (evt.type === "cell") cellsCount++;
        if (evt.type === "stage" && evt.stage === "merge" && evt.status === "DEGRADED") fallbackCount++;
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn("SSE connection closed or error:", err);
      eventSource.close();
    };
  },

  handleEvent(evt, mode, timelineEl, cellsCount, fallbackCount) {
    // 1. Stage node highlight
    if (evt.type === "stage") {
      const nodeEl = document.getElementById(`node-${evt.stage}`);
      if (nodeEl) {
        if (evt.status === "IN_PROGRESS") {
          nodeEl.className = "workflow-node active";
        } else if (evt.status === "COMPLETED") {
          nodeEl.className = "workflow-node success";
        } else if (evt.status === "DEGRADED") {
          nodeEl.className = "workflow-node degraded";
        }
      }

      const logItem = document.createElement("div");
      logItem.style.color = evt.status === "DEGRADED" ? "var(--accent-amber)" : "var(--text-secondary)";
      logItem.textContent = `[${evt.timestamp.split("T")[1].replace("Z", "")}] STAGE ${evt.stage.toUpperCase()}: ${evt.name} (${evt.status})`;
      timelineEl.appendChild(logItem);
      timelineEl.scrollTop = timelineEl.scrollHeight;
    }

    // 2. Cell execution highlight
    if (evt.type === "cell") {
      const runtimesNode = document.getElementById("node-runtimes");
      if (runtimesNode) {
        if (evt.status === "SUCCESS") {
          runtimesNode.className = "workflow-node success";
        } else {
          runtimesNode.className = "workflow-node failed";
        }
      }

      document.getElementById("interp-cells-val").textContent = `${cellsCount + 1} / 5`;

      const logItem = document.createElement("div");
      logItem.style.color = evt.status === "SUCCESS" ? "var(--accent-green)" : "var(--accent-red)";
      logItem.textContent = `[${evt.timestamp.split("T")[1].replace("Z", "")}] CELL ${evt.cell_id} (${evt.language}): ${evt.status} (${evt.duration_ms} ms)`;
      timelineEl.appendChild(logItem);
      timelineEl.scrollTop = timelineEl.scrollHeight;
    }

    // 3. Receipt emission
    if (evt.type === "receipt") {
      const receiptNode = document.getElementById("node-receipt");
      if (receiptNode) {
        receiptNode.className = evt.execution_status === "SUCCESS" ? "workflow-node success" : "workflow-node degraded";
      }

      this.latestReceipt = evt.receipt;
      document.getElementById("interp-status-val").textContent = evt.execution_status;
      document.getElementById("interp-status-val").style.color = evt.execution_status === "SUCCESS" ? "var(--accent-green)" : "var(--accent-amber)";
      document.getElementById("interp-status-sub").textContent = evt.execution_status === "SUCCESS" ? "All cells executed cleanly" : "Controlled fallback policy applied";
      document.getElementById("interp-latency-val").textContent = `${evt.latency_ms} ms`;
      document.getElementById("interp-fallback-sub").textContent = `${evt.cells_fallback} fallbacks triggered`;

      document.getElementById("interp-receipt-view").textContent = JSON.stringify(evt.receipt, null, 2);
    }
  }
};
