import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  CheckCircle2, 
  Layers, 
  Zap, 
  AlertTriangle, 
  Terminal, 
  Lock, 
  GitBranch, 
  FileCode2,
  FolderGit2,
  Cpu,
  Boxes,
  ArrowRight,
  Flame,
  Check
} from 'lucide-react';
import { 
  NEXTCLOUD_BENCHMARK, 
  OPENTELEMETRY_BENCHMARK,
  E2E_CODING_BENCHMARK, 
  COLOCATION_FINDING 
} from '../data/benchmarkData';

export function BenchmarkArena() {
  const [activeProject, setActiveProject] = useState('nextcloud'); // 'nextcloud' | 'opentelemetry'
  const [activeTab, setActiveTab] = useState('retrieval'); // 'retrieval' | 'e2e' | 'colocation'
  const [selectedTaskIdx, setSelectedTaskIdx] = useState(0);

  const projectData = activeProject === 'nextcloud' ? NEXTCLOUD_BENCHMARK : OPENTELEMETRY_BENCHMARK;
  const { scale, primaryMetrics, tasks } = projectData;
  const currentTask = tasks[selectedTaskIdx] || tasks[0];

  return (
    <div className="benchmark-arena" style={{ display: 'flex', flexDirection: 'column', gap: 22, paddingBottom: 40 }}>
      {/* Header and Project Selector */}
      <div className="arena-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#f8fafc', margin: 0 }}>
              Generalized Empirical Benchmark Arena
            </h2>
          </div>
          <p style={{ fontSize: 12.5, color: '#94a3b8', margin: 0 }}>
            Universal Evaluation Framework: Dependency Completeness · Bounded Context Budgets · Gatekeeper Release Authority
          </p>
        </div>

        {/* Global View Selector Tabs */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button 
            className={`view-pill ${activeTab === 'retrieval' ? 'active' : ''}`}
            onClick={() => setActiveTab('retrieval')}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: activeTab === 'retrieval' ? '1px solid #38bdf8' : '1px solid var(--border-subtle)',
              background: activeTab === 'retrieval' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(15, 23, 42, 0.6)',
              color: activeTab === 'retrieval' ? '#38bdf8' : '#94a3b8',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Dependency Intelligence
          </button>
          <button 
            className={`view-pill ${activeTab === 'e2e' ? 'active' : ''}`}
            onClick={() => setActiveTab('e2e')}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: activeTab === 'e2e' ? '1px solid #38bdf8' : '1px solid var(--border-subtle)',
              background: activeTab === 'e2e' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(15, 23, 42, 0.6)',
              color: activeTab === 'e2e' ? '#38bdf8' : '#94a3b8',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Real E2E Coding Loops
          </button>
          <button 
            className={`view-pill ${activeTab === 'colocation' ? 'active' : ''}`}
            onClick={() => setActiveTab('colocation')}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: activeTab === 'colocation' ? '1px solid #38bdf8' : '1px solid var(--border-subtle)',
              background: activeTab === 'colocation' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(15, 23, 42, 0.6)',
              color: activeTab === 'colocation' ? '#38bdf8' : '#94a3b8',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Colocation vs Fragmentation
          </button>
        </div>
      </div>

      {/* TAB 1: GENERALIZED DEPENDENCY BENCHMARK WITH RICH GRAPHICAL COMPARISON BARS */}
      {activeTab === 'retrieval' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Multi-Project Architecture Switcher */}
          <div className="glass-panel" style={{ padding: '14px 18px', borderRadius: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FolderGit2 className="w-4 h-4 text-cyan-400" />
              <span style={{ fontSize: 12.5, fontWeight: 700, color: '#f8fafc' }}>Select Target Repository:</span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => { setActiveProject('nextcloud'); setSelectedTaskIdx(0); }}
                style={{
                  padding: '7px 14px',
                  borderRadius: 6,
                  border: activeProject === 'nextcloud' ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                  background: activeProject === 'nextcloud' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(15, 23, 42, 0.5)',
                  color: activeProject === 'nextcloud' ? '#10b981' : '#94a3b8',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                Nextcloud Server Core (50k Nodes Monolith)
              </button>
              <button
                onClick={() => { setActiveProject('opentelemetry'); setSelectedTaskIdx(0); }}
                style={{
                  padding: '7px 14px',
                  borderRadius: 6,
                  border: activeProject === 'opentelemetry' ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                  background: activeProject === 'opentelemetry' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(15, 23, 42, 0.5)',
                  color: activeProject === 'opentelemetry' ? '#10b981' : '#94a3b8',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                OpenTelemetry Demo (14 Polyglot Microservices)
              </button>
            </div>
          </div>

          {/* Top Aggregate Summary Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
            <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(56, 189, 248, 0.3)' }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Average Edge Recall
              </div>
              <div style={{ fontSize: 32, fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                {primaryMetrics.rcirEdgeRecall}
              </div>
              <div style={{ fontSize: 11.5, color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrendingUp className="w-3.5 h-3.5" />
                <span>{primaryMetrics.observedUplift} vs Baseline</span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Rescued Dependencies
              </div>
              <div style={{ fontSize: 32, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                +{primaryMetrics.referencesRescued}
              </div>
              <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                Silent misses: {primaryMetrics.silentMissesBaseline} ➔ {primaryMetrics.silentMissesRcir}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(129, 140, 248, 0.3)' }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Context Token Savings
              </div>
              <div style={{ fontSize: 32, fontWeight: 800, color: '#818cf8', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                -{primaryMetrics.tokenReduction}
              </div>
              <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                Strict 4,000-token contract cap
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Model & Provenance
              </div>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
                qwen2.5-coder:1.5b
              </div>
              <div style={{ fontSize: 11.5, color: '#10b981' }}>
                Air-Gapped Local Inference (Exit 0)
              </div>
            </div>
          </div>

          {/* Graphical Task Comparison Bars */}
          <div className="glass-panel" style={{ padding: 22, borderRadius: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#f8fafc', margin: '0 0 4px 0' }}>
                  Graphical Head-to-Head Comparison: Baseline Search vs RCIR Graph
                </h3>
                <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>
                  Evaluated across genuine AST call graphs, interface bindings, and dependency injection services.
                </p>
              </div>
              <span className="hero-pill text-emerald-400" style={{ fontSize: 11 }}>
                N={tasks.length} Real Tasks
              </span>
            </div>

            {/* Task Comparison Bars List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {tasks.map((task, idx) => (
                <div 
                  key={task.id} 
                  style={{ 
                    background: 'rgba(15, 23, 42, 0.6)', 
                    border: selectedTaskIdx === idx ? '1px solid #38bdf8' : '1px solid var(--border-subtle)', 
                    borderRadius: 10, 
                    padding: 16,
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onClick={() => setSelectedTaskIdx(idx)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 800, color: '#f8fafc' }}>
                        {task.id}: {task.title}
                      </span>
                      <span style={{ fontSize: 11.5, color: '#94a3b8', marginLeft: 8 }}>
                        Target: <code style={{ color: '#38bdf8' }}>{task.targetSymbol}</code>
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span className="hero-pill" style={{ fontSize: 10.5 }}>{task.category}</span>
                      <span className="hero-pill text-cyan-400" style={{ fontSize: 10.5 }}>{task.gtFiles} GT Files</span>
                      <span className="hero-pill text-emerald-400" style={{ fontSize: 10.5, fontWeight: 700 }}>
                        +{Math.round(task.rcirRecall - task.baseRecall)}% Uplift
                      </span>
                    </div>
                  </div>

                  {/* Graphical Comparison Bar Visualizer */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {/* Baseline Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                        <span style={{ color: '#f43f5e', fontWeight: 600 }}>Condition A: Baseline (Naive Localized Search)</span>
                        <span style={{ color: '#f43f5e', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                          {task.baseRecall}% Recall ({task.baseMisses} silent misses) · {task.tokensBase.toLocaleString()} tokens
                        </span>
                      </div>
                      <div style={{ width: '100%', height: 10, background: 'rgba(255, 255, 255, 0.05)', borderRadius: 5, overflow: 'hidden' }}>
                        <div style={{ 
                          width: `${Math.max(2, task.baseRecall)}%`, 
                          height: '100%', 
                          background: 'linear-gradient(90deg, #f43f5e, #fb7185)', 
                          borderRadius: 5,
                          transition: 'width 0.6s ease'
                        }} />
                      </div>
                    </div>

                    {/* RCIR Bar */}
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                        <span style={{ color: '#10b981', fontWeight: 600 }}>Condition B: PolyFlow RCIR (AST Dependency Graph)</span>
                        <span style={{ color: '#10b981', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                          {task.rcirRecall}% Recall ({task.rcirMisses} misses) · {task.tokensRcir.toLocaleString()} tokens
                        </span>
                      </div>
                      <div style={{ width: '100%', height: 10, background: 'rgba(255, 255, 255, 0.05)', borderRadius: 5, overflow: 'hidden' }}>
                        <div style={{ 
                          width: `${Math.max(2, task.rcirRecall)}%`, 
                          height: '100%', 
                          background: 'linear-gradient(90deg, #06b6d4, #10b981)', 
                          borderRadius: 5,
                          transition: 'width 0.6s ease'
                        }} />
                      </div>
                    </div>
                  </div>

                  {/* Notes / Findings */}
                  <div style={{ marginTop: 10, fontSize: 11.5, color: '#cbd5e1', lineHeight: 1.4 }}>
                    <strong>Finding: </strong> {task.notes}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REAL E2E CODING LOOPS */}
      {activeTab === 'e2e' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="glass-panel" style={{ padding: 18, borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Terminal className="w-5 h-5 text-cyan-400" />
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                  End-to-End Autonomous Coding Agent Benchmark
                </h3>
                <p style={{ fontSize: 12, color: '#94a3b8', margin: '2px 0 0 0' }}>
                  Evaluates real agents executing concrete repo tools (<code>inspect_file</code>, <code>edit_file</code>, <code>run_command</code>) 
                  against Adoptium Java 21, Python 3.12, Node.js v25, and SQLite runtimes with local model reasoning.
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {E2E_CODING_BENCHMARK.tasks.map(t => (
              <div key={t.id} className="glass-panel" style={{ padding: 18, borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <h4 style={{ fontSize: 15, fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                      {t.id}: {t.title}
                    </h4>
                    <span style={{ fontSize: 11.5, color: '#94a3b8' }}>Target: <code>{t.targetFile}</code></span>
                  </div>
                  <span className="hero-pill text-emerald-400" style={{ fontSize: 11 }}>
                    <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                    GATEKEEPER {t.gatekeeperVerdict}
                  </span>
                </div>

                <p style={{ fontSize: 12, color: '#cbd5e1', marginBottom: 12 }}>{t.requirement}</p>

                <div style={{ background: '#070a12', borderRadius: 6, border: '1px solid var(--border-subtle)', padding: 10, marginBottom: 12 }}>
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Verified Unified Git Diff:</div>
                  <pre style={{ margin: 0, fontSize: 11.5, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                    <code>{t.gitDiffSummary}</code>
                  </pre>
                </div>

                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: 11.5, color: '#10b981' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Java 21 Unit Tests PASSED
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Multi-Language Vertical Slice PASSED
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#38bdf8' }}>
                    <Cpu className="w-3.5 h-3.5" />
                    Local Ollama (qwen2.5-coder:1.5b)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: COLOCATION VS FRAGMENTATION FINDING */}
      {activeTab === 'colocation' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="glass-panel" style={{ padding: 20, borderRadius: 10 }}>
            <h3 style={{ fontSize: 17, fontWeight: 800, color: '#f8fafc', marginBottom: 6 }}>
              {COLOCATION_FINDING.title}
            </h3>
            <p style={{ fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
              {COLOCATION_FINDING.thesis}
            </p>
          </div>

          <div className="glass-panel" style={{ padding: 20, borderRadius: 10 }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: '#94a3b8' }}>
                    <th style={{ padding: '10px 14px' }}>Architectural Dimension</th>
                    <th style={{ padding: '10px 14px' }}>PolyFlow Cloud Drive Prototype</th>
                    <th style={{ padding: '10px 14px' }}>Nextcloud Server Core</th>
                  </tr>
                </thead>
                <tbody>
                  {COLOCATION_FINDING.comparison.map((r, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '10px 14px', fontWeight: 600, color: '#cbd5e1' }}>{r.dimension}</td>
                      <td style={{ padding: '10px 14px', color: '#38bdf8' }}>{r.polyflowApp}</td>
                      <td style={{ padding: '10px 14px', color: '#10b981', fontWeight: 600 }}>{r.nextcloudServer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
