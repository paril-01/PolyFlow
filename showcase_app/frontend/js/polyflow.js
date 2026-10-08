// showcase_app/frontend/js/polyflow.js — Tab 01: Native vs Feature View

const PolyFlowModule = {
  async init() {
    try {
      const res = await fetch("/api/features/ERPNEXT-ACCOUNTS-SALES_INVOICE/native-vs-poly");
      if (!res.ok) throw new Error("Failed to load feature mapping");
      const data = await res.json();
      this.render(data);
    } catch (err) {
      console.error("PolyFlow module error:", err);
      // Fallback to local static json if backend offline
      try {
        const fallbackRes = await fetch("/data/polyflow_mapping.json");
        const fallbackData = await fallbackRes.json();
        const feat = fallbackData.features["ERPNEXT-ACCOUNTS-SALES_INVOICE"];
        if (feat) this.render(feat);
      } catch (e) {
        console.error("Fallback load failed:", e);
      }
    }
  },

  render(data) {
    const container = document.getElementById("native-layers-container");
    if (!container) return;
    container.innerHTML = "";

    const layers = data.layers || {};
    const layerNames = {
      frontend: "Frontend / Client JS",
      backend: "Backend / Python Controller",
      data_model: "Data Model / DocType Schema",
      framework: "Hooks / Configuration",
      tests: "Tests / Verification",
      dependencies: "Linked Dependencies"
    };

    let totalFiles = 0;

    Object.keys(layers).forEach(layerKey => {
      const layer = layers[layerKey];
      const files = layer.files || [];
      totalFiles += files.length;

      const layerDiv = document.createElement("div");
      layerDiv.style.marginBottom = "10px";

      const header = document.createElement("div");
      header.style.display = "flex";
      header.style.justifyContent = "space-between";
      header.style.fontSize = "11px";
      header.style.fontWeight = "600";
      header.style.color = "var(--text-muted)";
      header.style.marginBottom = "4px";
      header.style.textTransform = "uppercase";
      header.innerHTML = `<span>${layerNames[layerKey] || layerKey}</span><span>${files.length} files</span>`;
      layerDiv.appendChild(header);

      files.forEach(f => {
        const item = document.createElement("div");
        item.className = "file-list-item";
        item.dataset.path = f.path;
        item.dataset.polySymbol = f.symbol || "";

        const nameSpan = document.createElement("span");
        nameSpan.className = "file-name-truncate";
        nameSpan.textContent = f.path;
        nameSpan.title = f.path;

        const actionBtn = document.createElement("button");
        actionBtn.className = "btn btn-outline btn-sm";
        actionBtn.textContent = "View";
        actionBtn.onclick = (e) => {
          e.stopPropagation();
          ProofsModule.openModal(f.path, `Source: ${f.path}`);
        };

        item.appendChild(nameSpan);
        item.appendChild(actionBtn);

        item.onmouseenter = () => this.highlightPolyCode(f.symbol);
        item.onmouseleave = () => this.clearPolyHighlight();

        layerDiv.appendChild(item);
      });

      container.appendChild(layerDiv);
    });

    // Render .poly code
    this.renderPolyCode(data.poly_content || "");

    const btnProof = document.getElementById("btn-open-polyflow-proof");
    if (btnProof) {
      btnProof.onclick = () => {
        ProofsModule.openModal(data.poly_content, "Unified Feature: sales_invoice.poly");
      };
    }
  },

  renderPolyCode(codeText) {
    const codeView = document.getElementById("poly-code-view");
    if (!codeView) return;
    codeView.innerHTML = "";

    const lines = codeText.split("\n");
    lines.forEach((line, idx) => {
      const lineDiv = document.createElement("div");
      lineDiv.className = "code-line";
      lineDiv.dataset.lineNum = idx + 1;

      const numSpan = document.createElement("span");
      numSpan.className = "code-num";
      numSpan.textContent = idx + 1;

      const textSpan = document.createElement("span");
      textSpan.className = "code-text";
      textSpan.textContent = line;

      lineDiv.appendChild(numSpan);
      lineDiv.appendChild(textSpan);
      codeView.appendChild(lineDiv);
    });
  },

  highlightPolyCode(symbol) {
    if (!symbol) return;
    const lines = document.querySelectorAll("#poly-code-view .code-line");
    lines.forEach(l => {
      if (l.textContent.includes(symbol)) {
        l.style.backgroundColor = "rgba(59, 130, 246, 0.25)";
        l.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else {
        l.style.backgroundColor = "transparent";
      }
    });
  },

  clearPolyHighlight() {
    const lines = document.querySelectorAll("#poly-code-view .code-line");
    lines.forEach(l => {
      l.style.backgroundColor = "transparent";
    });
  }
};
