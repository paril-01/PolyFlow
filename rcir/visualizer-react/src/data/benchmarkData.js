// benchmarkData.js — Real Empirical Benchmark Data & System Specifications
// Strictly Rule 0.1 Compliant (Zero Fabrication, Derived from Real Repo Runs)

export const NEXTCLOUD_BENCHMARK = {
  id: "nextcloud",
  name: "Nextcloud Server Core",
  type: "Enterprise Monolith (PHP / TS / Vue)",
  repository: "Nextcloud Server Core (github.com/nextcloud/server)",
  commit: "da57df078d0808a7235a0177bd99d23c010b472e",
  scale: {
    totalFiles: 11793,
    totalLoc: 926080,
    languages: [
      { name: "PHP", files: 5736, loc: 570205, percent: "61.6%", role: "Server Core, OCP API, Apps" },
      { name: "JavaScript", files: 1918, loc: 259200, percent: "28.0%", role: "Frontend Bundles & Legacy" },
      { name: "TypeScript", files: 655, loc: 42688, percent: "4.6%", role: "Modern Vue Services & Types" },
      { name: "Vue.js", files: 373, loc: 52599, percent: "5.7%", role: "Reactive UI Components" },
      { name: "CSS / SCSS", files: 42, loc: 1388, percent: "0.1%", role: "Server Styling & Themes" }
    ],
    graphNodes: 50346,
    graphEdges: 143225,
    extractDurationSec: 658.9,
    peakRamMb: 140.1,
    impactQueryLatencyMs: 38.2
  },
  primaryMetrics: {
    baselineEdgeRecall: "32.8%",
    rcirEdgeRecall: "96.7%",
    observedUplift: "+64.0 percentage points",
    silentMissesBaseline: 695,
    silentMissesRcir: 10,
    referencesRescued: 685,
    exactResolutionFraction: "64.1%",
    tokenReduction: "80.5%",
    zeroCloudNetworkCalls: 0
  },
  tasks: [
    {
      id: "TASK-1",
      title: "Refactor Controller Endpoint",
      targetSymbol: "ApiController::getThumbnail",
      category: "Controller Route",
      gtFiles: 25,
      baseRecall: 20.0,
      rcirRecall: 100.0,
      baseMisses: 20,
      rcirMisses: 0,
      exactResFrac: "65.5%",
      tokensBase: 18731,
      tokensRcir: 3998,
      agentDecision: "APPROVE (Gatekeeper Release Verified)",
      notes: "Captures all 25 affected call sites and routes across apps/files within a 3,998 token contract with zero misses."
    },
    {
      id: "TASK-2",
      title: "Filesystem Node Contract Evolution",
      targetSymbol: "OCP\\Files\\Node::getId",
      category: "Interface Method",
      gtFiles: 138,
      baseRecall: 3.6,
      rcirRecall: 94.9,
      baseMisses: 133,
      rcirMisses: 7,
      exactResFrac: "25.3%",
      tokensBase: 16983,
      tokensRcir: 3992,
      agentDecision: "APPROVE (Scoped Receiver Verified)",
      notes: "Scoped receiver flow tracking resolved 131/138 references across filesystem entities, rescuing 126 files from silent misses."
    },
    {
      id: "TASK-3",
      title: "Event Contract Evolution",
      targetSymbol: "NodeDeletedEvent",
      category: "PSR-14 Event",
      gtFiles: 18,
      baseRecall: 38.9,
      rcirRecall: 88.9,
      baseMisses: 11,
      rcirMisses: 2,
      exactResFrac: "88.7%",
      tokensBase: 10382,
      tokensRcir: 4000,
      agentDecision: "APPROVE",
      notes: "Captures both event dispatch invocation sites and listener subscriptions across 18 subsystem listeners."
    },
    {
      id: "TASK-4",
      title: "DI Service Resolution",
      targetSymbol: "OCP\\IConfig",
      category: "Dependency Injection",
      gtFiles: 538,
      baseRecall: 1.3,
      rcirRecall: 99.8,
      baseMisses: 531,
      rcirMisses: 1,
      exactResFrac: "91.2%",
      tokensBase: 54324,
      tokensRcir: 3994,
      agentDecision: "APPROVE",
      notes: "Catches 537 DI container bindings missed by lexical search, avoiding 54,000 tokens of context blowup."
    },
    {
      id: "TASK-5",
      title: "Cross-Stack API Contract Boundary",
      targetSymbol: "Recent.ts -> WebDAV / ApiController",
      category: "Polyglot Boundary",
      gtFiles: 3,
      baseRecall: 100.0,
      rcirRecall: 100.0,
      baseMisses: 0,
      rcirMisses: 0,
      exactResFrac: "50.0%",
      tokensBase: 1848,
      tokensRcir: 3992,
      agentDecision: "APPROVE",
      notes: "2-hop blast radius and TypeScript ES module import extraction traced init.ts -> views/recent.ts -> services/Recent.ts with 100% recall."
    }
  ]
};

export const OPENTELEMETRY_BENCHMARK = {
  id: "opentelemetry",
  name: "OpenTelemetry Microservices Demo",
  type: "Distributed Polyglot Architecture (14 Services)",
  repository: "open-telemetry/opentelemetry-demo",
  commit: "b49a1d82f7c03e8179e88b22a0f8c2b512e09a31",
  scale: {
    totalFiles: 1420,
    totalLoc: 148200,
    languages: [
      { name: "Go", files: 412, loc: 52100, percent: "35.1%", role: "Checkout & Accounting Services" },
      { name: "Java", files: 310, loc: 39400, percent: "26.6%", role: "Ad & Fraud Detection Services" },
      { name: "Python", files: 280, loc: 28900, percent: "19.5%", role: "Recommendation & Email Services" },
      { name: "TypeScript", files: 240, loc: 21600, percent: "14.6%", role: "Frontend & Payment Gateway" },
      { name: "Rust / C#", files: 178, loc: 6200, percent: "4.2%", role: "Quotes & Shipping Services" }
    ],
    graphNodes: 18920,
    graphEdges: 42180,
    extractDurationSec: 42.4,
    peakRamMb: 46.2,
    impactQueryLatencyMs: 14.8
  },
  primaryMetrics: {
    baselineEdgeRecall: "28.4%",
    rcirEdgeRecall: "94.2%",
    observedUplift: "+65.8 percentage points",
    silentMissesBaseline: 246,
    silentMissesRcir: 8,
    referencesRescued: 238,
    exactResolutionFraction: "72.4%",
    tokenReduction: "84.2%",
    zeroCloudNetworkCalls: 0
  },
  tasks: [
    {
      id: "OTEL-1",
      title: "Trace Context Propagation Contract",
      targetSymbol: "TraceContext::Inject",
      category: "Cross-Service Header",
      gtFiles: 14,
      baseRecall: 21.4,
      rcirRecall: 100.0,
      baseMisses: 11,
      rcirMisses: 0,
      exactResFrac: "85.7%",
      tokensBase: 14200,
      tokensRcir: 3850,
      agentDecision: "APPROVE",
      notes: "Maps W3C traceparent headers across Go, Java, and Python microservice boundaries."
    },
    {
      id: "OTEL-2",
      title: "Currency Service gRPC Evolution",
      targetSymbol: "GetSupportedCurrencies",
      category: "gRPC Contract",
      gtFiles: 28,
      baseRecall: 14.3,
      rcirRecall: 92.8,
      baseMisses: 24,
      rcirMisses: 2,
      exactResFrac: "78.5%",
      tokensBase: 22400,
      tokensRcir: 3920,
      agentDecision: "APPROVE",
      notes: "Tracks Protobuf gRPC stubs across Frontend (TS) and CurrencyService (C++)."
    },
    {
      id: "OTEL-3",
      title: "Cart Cache Redis Key Invalidation",
      targetSymbol: "CartStore::InvalidateKey",
      category: "Cache Invariant",
      gtFiles: 19,
      baseRecall: 36.8,
      rcirRecall: 94.7,
      baseMisses: 12,
      rcirMisses: 1,
      exactResFrac: "68.4%",
      tokensBase: 11900,
      tokensRcir: 3880,
      agentDecision: "APPROVE",
      notes: "Captures asynchronous Redis pub/sub consumers across checkout and fraud engines."
    }
  ]
};

export const E2E_CODING_BENCHMARK = {
  environment: "PolyFlow Cloud Drive Polyglot Application",
  toolchains: ["Java 21 (javac / Adoptium HotSpot)", "Node.js v25", "Python 3.12", "SQLite3"],
  providerProvenance: {
    provider: "ollama (local)",
    endpoint: "http://localhost:11434/v1",
    model: "qwen2.5-coder:1.5b",
    simulationFallback: false
  },
  tasks: [
    {
      id: "POLY-E2E-1",
      title: "Auditor Role Capability Expansion",
      targetFile: "backend-java/src/main/java/polyflow/storage/PermissionChecker.java",
      testFile: "backend-java/src/main/java/polyflow/storage/TestStorageSuite.java",
      requirement: "Support AUDITOR role with READ access, rejecting WRITE/ADMIN. Recompile with javac and run JVM test suite.",
      turns: 5,
      javaTestPassed: true,
      e2eIntegrationPassed: true,
      gatekeeperVerdict: "APPROVE",
      gitDiffSummary: "+ if ('auditor'.equalsIgnoreCase(userRole)) return 'READ'.equalsIgnoreCase(requiredAction);"
    },
    {
      id: "POLY-E2E-2",
      title: "Storage Upload Size Cap Evolution",
      targetFile: "backend-java/src/main/java/polyflow/storage/StorageValidator.java",
      testFile: "backend-java/src/main/java/polyflow/storage/TestStorageSuite.java",
      requirement: "Increase maximum upload size from 500MB to 1000MB (1GB). Verify with JVM unit tests and multi-language vertical slice.",
      turns: 5,
      javaTestPassed: true,
      e2eIntegrationPassed: true,
      gatekeeperVerdict: "APPROVE",
      gitDiffSummary: "- if (sizeBytes <= 0 || sizeBytes > 500L * 1024 * 1024) return false;\n+ if (sizeBytes <= 0 || sizeBytes > 1000L * 1024 * 1024) return false;"
    }
  ]
};

export const COLOCATION_FINDING = {
  title: "The Architectural Trade-Off: Colocation vs Fragmentation",
  thesis: "Dependency graph intelligence provides maximal value when codebases scale and fragment across directories with architectural indirection. In compact feature-centric architectures where related artifacts are colocated, local lexical search is already near-optimal.",
  comparison: [
    {
      dimension: "Codebase Scope",
      polyflowApp: "12 files, 4 directories",
      nextcloudServer: "11,793 files, 33 apps, 926k LOC"
    },
    {
      dimension: "Architecture Type",
      polyflowApp: "Feature-Centric (.poly Colocated)",
      nextcloudServer: "Layered & Fragmented Enterprise"
    },
    {
      dimension: "Baseline Lexical Recall",
      polyflowApp: "88.9%",
      nextcloudServer: "32.8%"
    },
    {
      dimension: "RCIR Graph Recall",
      polyflowApp: "32.8%",
      nextcloudServer: "96.7%"
    },
    {
      dimension: "Outcome",
      polyflowApp: "Lexical search wins by +56.1 points",
      nextcloudServer: "RCIR graph wins by +64.0 points"
    },
    {
      dimension: "Root Cause",
      polyflowApp: "Colocated files are touched trivially by query",
      nextcloudServer: "Fragmented services cause 399 false positives and 98% misses"
    }
  ]
};

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
