import React from 'react';
import { 
  Layers, 
  Cpu, 
  ShieldCheck, 
  GitBranch, 
  Terminal, 
  Zap, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react';
import { NEXTCLOUD_BENCHMARK } from '../data/benchmarkData';

export function ExecutiveHero({ onNavigate }) {
  const { scale, primaryMetrics } = NEXTCLOUD_BENCHMARK;

  return (
    <div className="executive-hero">
      {/* Top Banner / Badge */}
      <div className="hero-badge-container">
        <span className="hero-pill">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Rule 0.1 Compliant — 100% Real Repository Evidence</span>
        </span>
        <span className="hero-pill-secondary">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>Zero Cloud Telemetry — 100% Offline Air-Gapped</span>
        </span>
      </div>

      {/* Main Title & Value Proposition */}
      <div className="hero-header">
        <h1 className="hero-title">
          Deterministic Dependency Intelligence <br />
          <span className="hero-gradient-text">& Multi-Agent Release Authority</span>
        </h1>
        <p className="hero-subtitle">
          Validated against <strong>Nextcloud Server Core</strong> (11,793 files, 926k LOC). 
          Eliminates context blindness, prevents silent multi-file regressions, and enforces 
          compiler-verified gatekeeping for enterprise AI coding agents.
        </p>
      </div>

      {/* Key Metric Snapshot Grid */}
      <div className="hero-metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Candidate Recall (2-Hop)</span>
            <Zap className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="metric-value text-cyan-400">{primaryMetrics.candidateFileRecallRcir}</div>
          <div className="metric-desc">
            vs <strong>{primaryMetrics.candidateFileRecallBaseline}</strong> Baseline ({primaryMetrics.candidatePrecisionRcir} precision trade-off)
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">References Rescued</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="metric-value text-emerald-400">+{primaryMetrics.referencesRescued}</div>
          <div className="metric-desc">
            Ground-truth dependencies identified by RCIR missed by naive search
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Token Footprint Cut</span>
            <Layers className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="metric-value text-indigo-400">-{primaryMetrics.tokenReduction}</div>
          <div className="metric-desc">
            Contract-bounded contexts eliminate context window blowup
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-label">Blast Radius Query</span>
            <Terminal className="w-5 h-5 text-amber-400" />
          </div>
          <div className="metric-value text-amber-400">{scale.impactQueryLatencyMs} ms</div>
          <div className="metric-desc">
            Sub-second traversal across {scale.graphEdges.toLocaleString()} real dependency edges
          </div>
        </div>
      </div>

      {/* The Core Problem vs Solution Visual Comparison */}
      <div className="problem-solution-section">
        <div className="comparison-box problem-box">
          <div className="comparison-header">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
            <h3>The Legacy Problem: Fragile AI Coding Agents</h3>
          </div>
          <ul className="comparison-list">
            <li>
              <strong>Context Blindness:</strong> Naive grep misses cross-service DI lookups (e.g. 98.7% of <code>IConfig</code> consumers).
            </li>
            <li>
              <strong>Context Explosion:</strong> Pulling whole directories consumes 54,000+ tokens on a single service change.
            </li>
            <li>
              <strong>False Positives:</strong> Querying generic methods (<code>getId()</code>) pulls 399 irrelevant files across 33 apps.
            </li>
            <li>
              <strong>Unverified Hallucinations:</strong> Single-pass LLMs write code without running actual compilers or integration test suites.
            </li>
          </ul>
        </div>

        <div className="comparison-box solution-box">
          <div className="comparison-header">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3>The PolyFlow + RCIR Solution</h3>
          </div>
          <ul className="comparison-list">
            <li>
              <strong>RCIR Graph Engine:</strong> Sub-second extraction of 50k nodes & 143k edges with calibrated resolution fractions.
            </li>
            <li>
              <strong>Contract-Bounded Budgets:</strong> 4,000-token caps guarantee dense, high-signal prompt packages.
            </li>
            <li>
              <strong>Concrete Repo Tools:</strong> Implementer agent edits real files, runs <code>javac 21</code>, and executes test suites.
            </li>
            <li>
              <strong>Adversarial Gatekeeping:</strong> Gatekeeper checks real test exit codes and unified diffs, refusing unverified release.
            </li>
          </ul>
        </div>
      </div>

      {/* Interactive Navigation Pathways */}
      <div className="presentation-pathways">
        <h3 className="pathway-title">Explore the Validation Proofs</h3>
        <div className="pathway-grid">
          <button className="pathway-btn" onClick={() => onNavigate('graph')}>
            <div className="pathway-icon-wrapper text-cyan-400">
              <GitBranch className="w-6 h-6" />
            </div>
            <div className="pathway-text">
              <div className="pathway-heading">Nextcloud 50k Graph</div>
              <div className="pathway-sub">Explore {scale.graphEdges.toLocaleString()} edges & sub-second blast radius</div>
            </div>
            <ArrowRight className="w-5 h-5 ml-auto text-slate-500" />
          </button>

          <button className="pathway-btn" onClick={() => onNavigate('agents')}>
            <div className="pathway-icon-wrapper text-indigo-400">
              <Layers className="w-6 h-6" />
            </div>
            <div className="pathway-text">
              <div className="pathway-heading">6-Stage Agent Pool</div>
              <div className="pathway-sub">Maker → Reviewer → Implementer → Gatekeeper</div>
            </div>
            <ArrowRight className="w-5 h-5 ml-auto text-slate-500" />
          </button>

          <button className="pathway-btn" onClick={() => onNavigate('benchmark')}>
            <div className="pathway-icon-wrapper text-emerald-400">
              <Zap className="w-6 h-6" />
            </div>
            <div className="pathway-text">
              <div className="pathway-heading">Empirical Benchmark Arena</div>
              <div className="pathway-sub">Head-to-head recall, silent misses & token savings</div>
            </div>
            <ArrowRight className="w-5 h-5 ml-auto text-slate-500" />
          </button>

          <button className="pathway-btn" onClick={() => onNavigate('studio')}>
            <div className="pathway-icon-wrapper text-amber-400">
              <Terminal className="w-6 h-6" />
            </div>
            <div className="pathway-text">
              <div className="pathway-heading">Polyglot Studio</div>
              <div className="pathway-sub">Unified Feature Capsule (.poly · Java 21 · Python · TS)</div>
            </div>
            <ArrowRight className="w-5 h-5 ml-auto text-slate-500" />
          </button>

          <button className="pathway-btn" onClick={() => onNavigate('proof')}>
            <div className="pathway-icon-wrapper text-rose-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="pathway-text">
              <div className="pathway-heading">Proof & Audit Center</div>
              <div className="pathway-sub">Nextcloud Git Commit SHA · Hashes · Reproducibility</div>
            </div>
            <ArrowRight className="w-5 h-5 ml-auto text-slate-500" />
          </button>
        </div>
      </div>
    </div>
  );
}
