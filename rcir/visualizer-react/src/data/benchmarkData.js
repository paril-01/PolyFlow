// benchmarkData.js — PolyFlow Empirical Showcase Data Loaders & Historical Reference Fixtures
// Strictly Rule 0 Compliant: Zero hardcoded benchmark claims. All live data loaded from /data/*.json.

const cache = new Map();

async function fetchJson(path) {
  if (cache.has(path)) {
    return cache.get(path);
  }
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`HTTP ${res.status} fetching ${path}`);
    const data = await res.json();
    cache.set(path, data);
    return data;
  } catch (err) {
    console.warn(`Failed to fetch ${path}:`, err);
    return null;
  }
}

export async function loadRunManifest() {
  return fetchJson('/data/run_manifest.json');
}

export async function loadSystemStatus() {
  return fetchJson('/data/system_status.json');
}

export async function loadPolyflowMapping() {
  return fetchJson('/data/polyflow_mapping.json');
}

export async function loadInterpreterDemo() {
  return fetchJson('/data/interpreter_demo.json');
}

export async function loadRcirPipeline() {
  return fetchJson('/data/rcir_pipeline.json');
}

export async function loadTokenAb() {
  return fetchJson('/data/token_ab.json');
}

export async function loadAgentTrials() {
  return fetchJson('/data/agent_trials.json');
}

export async function loadErpnextScale() {
  return fetchJson('/data/erpnext_scale.json');
}

export async function loadClaimRegistry() {
  return fetchJson('/data/claim_registry.json');
}

// Stage Architecture Descriptors (Structural metadata only, no empirical claims)
export const AEF_AGENT_STAGES = [
  {
    stage: 1,
    name: "Maker Agent",
    role: "Architecture Discovery & Design",
    focus: "Analyzes system requirements, performs trade-off analysis, produces Architecture Decision Records (ADRs) and structural specs.",
    outputArtifact: "01_maker_design.md",
    badge: "Discovery"
  },
  {
    stage: 2,
    name: "Reviewer Agent 1",
    role: "12-Dimensional Design Audit",
    focus: "Audits architectural plan against 12 core engineering dimensions before any code is generated.",
    outputArtifact: "02_reviewer_design_review.md",
    badge: "Design Audit"
  },
  {
    stage: 3,
    name: "Implementer Agent",
    role: "Autonomous Code & Tool Loop",
    focus: "Executes concrete repo tools (inspect, edit, run tests) to implement modifications within a bounded context budget.",
    outputArtifact: "03_implementer_code.md",
    badge: "Tool Loop"
  },
  {
    stage: 4,
    name: "Reviewer Agent 2",
    role: "Unified Git Diff Review",
    focus: "Audits git diff output against previous AST state, checking for regression risks, boundary leaks, or security flaws.",
    outputArtifact: "04_reviewer_code_review.md",
    badge: "Diff Audit"
  },
  {
    stage: 5,
    name: "Gatekeeper Agent",
    role: "Adversarial Release Authority",
    focus: "Validates host compiler exit codes and unit test results; strictly vetoes unverified changes.",
    outputArtifact: "05_gatekeeper_release_decision.md",
    badge: "Release Authority"
  },
  {
    stage: 6,
    name: "Historian Agent",
    role: "Telemetry & Permanent Memory",
    focus: "Logs immutable memory records, token accounting, invalidation cache signatures, and technical debt items.",
    outputArtifact: "06_historian_memory_log.md",
    badge: "Engineering Memory"
  }
];

// Historical fixtures structure explicitly isolated
export const HISTORICAL_FIXTURES = {
  description: "Archived reference schema from preliminary prototypes",
  archived_run: "proto_preliminary"
};
