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
  Check,
  XCircle,
  ShieldAlert,
  Scale
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
            Strict Rule 0.1 Compliance: Candidate Recall vs Precision Trade-offs · Real Multi-Service Repos · Fail-Closed Release Safety
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
                OpenTelemetry Demo (611 Nodes Polyglot Services)
              </button>
            </div>
          </div>

          {/* Top Aggregate Summary Stat Cards */}
          {activeProject === 'nextcloud' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Candidate File Recall (2-Hop)
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  {primaryMetrics.candidateFileRecallRcir}
                </div>
                <div style={{ fontSize: 11.5, color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>{primaryMetrics.observedRecallUplift} vs Baseline (32.8%)</span>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(244, 63, 94, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#fb7185', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Candidate Precision & Noise
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#fb7185', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  {primaryMetrics.candidatePrecisionRcir}
                </div>
                <div style={{ fontSize: 11.5, color: '#cbd5e1' }}>
                  7,276 FP candidates (94.4% noise rate)
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Rescued Ground Truth
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  +{primaryMetrics.referencesRescued}
                </div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                  Silent misses: {primaryMetrics.silentMissesBaseline} ➔ {primaryMetrics.silentMissesRcir}
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Direct AST Mode vs 2-Hop
                </div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
                  55.3% Recall · 22.4% Prec.
                </div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                  Direct 1-Hop AST Edge Extraction
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Mutation Recall (§6.1.B)
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  {primaryMetrics.mutationRecall}
                </div>
                <div style={{ fontSize: 11.5, color: '#10b981' }}>
                  {primaryMetrics.detectedCallSites} / {primaryMetrics.expectedCallSites} expected call sites resolved
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Mutation Precision
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  {primaryMetrics.mutationPrecision}
                </div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                  0 false-positive edge classifications
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(129, 140, 248, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Dynamic Task Success (§6.2)
                </div>
                <div style={{ fontSize: 32, fontWeight: 800, color: '#818cf8', fontFamily: 'var(--font-mono)', margin: '4px 0' }}>
                  {primaryMetrics.taskSuccessRate}
                </div>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                  {primaryMetrics.tasksPassed} PASS, {primaryMetrics.tasksFailed} FAIL across 5 tasks
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Polyglot Architecture Scale
                </div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
                  611 Nodes · 1,176 Edges
                </div>
                <div style={{ fontSize: 11.5, color: '#10b981' }}>
                  160 files scanned in 11.78s (Exit 0)
                </div>
              </div>
            </div>
          )}

          {/* Graphical Task Comparison Section */}
          <div className="glass-panel" style={{ padding: 22, borderRadius: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#f8fafc', margin: '0 0 4px 0' }}>
                  {activeProject === 'nextcloud' 
                    ? "Nextcloud Server Core: Candidate Recall & Precision Head-to-Head" 
                    : "OpenTelemetry Demo: Synthetic Mutation Evaluation & Dynamic Task Verification"}
                </h3>
                <p style={{ fontSize: 12, color: '#94a3b8', margin: 0 }}>
                  {activeProject === 'nextcloud'
                    ? "Evaluates 2-hop candidate expansion trade-offs: high candidate recall paired with candidate false-positive noise."
                    : "Committed empirical results from rcir/artifacts/opentelemetry_demo_eval.md (160 files, 14 polyglot services)."}
                </p>
              </div>
              <span className="hero-pill text-emerald-400" style={{ fontSize: 11 }}>
                N={tasks.length} Real Evaluated Tasks
              </span>
            </div>

            {/* Task Comparison Cards List */}
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
                  {activeProject === 'nextcloud' ? (
                    <>
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
                          <span className="hero-pill text-cyan-400" style={{ fontSize: 10.5 }}>{task.gtFiles} Ground Truth Files</span>
                          <span className="hero-pill text-emerald-400" style={{ fontSize: 10.5, fontWeight: 700 }}>
                            +{Math.round(task.rcirRecall - task.baseRecall)}% Recall Delta
                          </span>
                        </div>
                      </div>

                      {/* Dual-Bar: Recall AND Precision */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
                        {/* Recall Comparison */}
                        <div style={{ background: '#0a0f1d', borderRadius: 8, padding: 12, border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', marginBottom: 6, textTransform: 'uppercase' }}>
                            Candidate File Recall
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                <span style={{ color: '#f43f5e' }}>Baseline Search</span>
                                <span style={{ color: '#f43f5e', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                  {task.baseRecall}% ({task.baseMisses} misses)
                                </span>
                              </div>
                              <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden', marginTop: 2 }}>
                                <div style={{ width: `${Math.max(2, task.baseRecall)}%`, height: '100%', background: '#f43f5e', borderRadius: 3 }} />
                              </div>
                            </div>
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                <span style={{ color: '#10b981' }}>RCIR (2-Hop Expansion)</span>
                                <span style={{ color: '#10b981', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                  {task.rcirRecall}% ({task.rcirMisses} misses)
                                </span>
                              </div>
                              <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden', marginTop: 2 }}>
                                <div style={{ width: `${Math.max(2, task.rcirRecall)}%`, height: '100%', background: '#10b981', borderRadius: 3 }} />
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Precision Comparison */}
                        <div style={{ background: '#0a0f1d', borderRadius: 8, padding: 12, border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', marginBottom: 6, textTransform: 'uppercase' }}>
                            Candidate Precision (Candidate Noise Trade-off)
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                <span style={{ color: '#cbd5e1' }}>Baseline Candidates</span>
                                <span style={{ color: '#cbd5e1', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                  {task.basePrecision}% ({task.baseCandidates} total, {task.baseFps} FP)
                                </span>
                              </div>
                              <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden', marginTop: 2 }}>
                                <div style={{ width: `${Math.max(2, task.basePrecision)}%`, height: '100%', background: '#94a3b8', borderRadius: 3 }} />
                              </div>
                            </div>
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                <span style={{ color: '#fb7185' }}>RCIR Candidates</span>
                                <span style={{ color: '#fb7185', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                  {task.rcirPrecision}% ({task.rcirCandidates} total, {task.rcirFps} FP)
                                </span>
                              </div>
                              <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden', marginTop: 2 }}>
                                <div style={{ width: `${Math.max(2, task.rcirPrecision)}%`, height: '100%', background: '#fb7185', borderRadius: 3 }} />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Notes / Findings */}
                      <div style={{ marginTop: 10, fontSize: 11.5, color: '#cbd5e1', lineHeight: 1.4 }}>
                        <strong>Finding: </strong> {task.notes}
                      </div>
                    </>
                  ) : (
                    <>
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
                          <span className={`hero-pill ${task.taskOutcome === 'PASS' ? 'text-emerald-400' : 'text-rose-400'}`} style={{ fontSize: 10.5, fontWeight: 700 }}>
                            Dynamic Task: {task.taskOutcome}
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginBottom: 8 }}>
                        <div style={{ background: '#0a0f1d', borderRadius: 8, padding: 10, border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: 10.5, color: '#94a3b8' }}>Expected vs Detected Call Sites</div>
                          <div style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', marginTop: 2 }}>
                            {task.detectedSites} / {task.expectedSites} Detected ({task.recall}%)
                          </div>
                        </div>
                        <div style={{ background: '#0a0f1d', borderRadius: 8, padding: 10, border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: 10.5, color: '#94a3b8' }}>Mutation Precision</div>
                          <div style={{ fontSize: 14, fontWeight: 700, color: '#10b981', marginTop: 2 }}>
                            {task.precision}% (0 False Positive Edges)
                          </div>
                        </div>
                        <div style={{ background: '#0a0f1d', borderRadius: 8, padding: 10, border: '1px solid var(--border-subtle)' }}>
                          <div style={{ fontSize: 10.5, color: '#94a3b8' }}>Dynamic Verification Scenario</div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#38bdf8', marginTop: 2 }}>
                            <code>{task.dynamicTask}</code>
                          </div>
                        </div>
                      </div>

                      <div style={{ fontSize: 11.5, color: '#cbd5e1', lineHeight: 1.4 }}>
                        <strong>Analysis: </strong> {task.notes}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: REAL E2E CODING LOOPS (WITH HONEST FAIL-CLOSED GATEKEEPER FINDING) */}
      {activeTab === 'e2e' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="glass-panel" style={{ padding: 18, borderRadius: 10, border: '1px solid rgba(244, 63, 94, 0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <ShieldAlert className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                  End-to-End Autonomous Coding Agent Benchmark: Fail-Closed Gatekeeper Enforcement
                </h3>
                <p style={{ fontSize: 12.5, color: '#cbd5e1', margin: '4px 0 0 0', lineHeight: 1.5 }}>
                  {E2E_CODING_BENCHMARK.finding}
                </p>
                <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 11.5, color: '#94a3b8', flexWrap: 'wrap' }}>
                  <span>Tested Toolchains: Adoptium Java 21 JDK, Node.js v25, Python 3.12, SQLite</span>
                  <span>·</span>
                  <span style={{ color: '#38bdf8' }}>Evaluated Model: qwen2.5:0.5b (Local Ollama, 0 cloud sockets)</span>
                </div>
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
                  <span className="hero-pill text-rose-400" style={{ fontSize: 11, border: '1px solid #f43f5e', background: 'rgba(244,63,94,0.1)' }}>
                    <ShieldAlert className="w-3.5 h-3.5 mr-1" />
                    GATEKEEPER {t.gatekeeperVerdict} (RELEASE REFUSED)
                  </span>
                </div>

                <p style={{ fontSize: 12, color: '#cbd5e1', marginBottom: 10 }}>{t.requirement}</p>

                <div style={{ background: '#070a12', borderRadius: 6, border: '1px solid var(--border-subtle)', padding: 10, marginBottom: 12 }}>
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Gatekeeper Audit Status & Git Diff:</div>
                  <pre style={{ margin: 0, fontSize: 11.5, fontFamily: 'var(--font-mono)', color: '#fb7185' }}>
                    <code>{t.gitDiffSummary}</code>
                  </pre>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                    <strong>Verdict Rationale: </strong>{t.gatekeeperReason}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 11.5 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#10b981' }}>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Java 21 Unit Tests: PASSED (Pre-existing on baseline)
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#10b981' }}>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Polyglot Vertical Slice: PASSED (Pre-existing on baseline)
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#fb7185' }}>
                    <XCircle className="w-3.5 h-3.5" />
                    Release Status: BLOCKED (0 files modified)
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
