import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, CheckCircle2, ShieldCheck, Terminal, ArrowRight, RefreshCw, FileCode, Cpu } from 'lucide-react';

export function Tab02Interpreter() {
  const [data, setData] = useState(null);
  const [mode, setMode] = useState('normal'); // 'normal' | 'failure'
  const [isRunning, setIsRunning] = useState(false);
  const [activeStageIndex, setActiveStageIndex] = useState(-1);
  const [errorSubtab, setErrorSubtab] = useState('readable'); // 'readable' | 'raw'

  useEffect(() => {
    fetch('/data/interpreter_demo.json')
      .then(r => r.json())
      .then(d => setData(d))
      .catch(err => console.warn('Could not load interpreter_demo.json', err));
  }, []);

  const handleRunWorkflow = () => {
    if (isRunning || !data) return;
    setIsRunning(true);
    setActiveStageIndex(0);

    const stagesCount = data.pipeline_stages.length;
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      if (current >= stagesCount) {
        clearInterval(interval);
        setActiveStageIndex(stagesCount - 1);
        setIsRunning(false);
      } else {
        setActiveStageIndex(current);
      }
    }, 350);
  };

  if (!data) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
        Loading Interpreter Demo Data...
      </div>
    );
  }

  const { pipeline_stages, normal_run, cell_failure_run, capability_cards, error_log } = data;
  const currentResult = mode === 'normal' ? normal_run : cell_failure_run;

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header Card */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', fontFamily: 'var(--font-mono)' }}>
                TAB 02 / RUNTIME
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                PolyFlow Portable Execution Engine
              </span>
            </div>
            <h1 style={{ fontSize: 20, fontWeight: 800, color: '#ffffff', margin: 0 }}>
              PolyFlow Interpreter & Multi-Cell Execution Engine
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, maxWidth: 880 }}>
              Question: What happens when a .poly file executes? The interpreter validates contracts, schedules language runtimes in isolated sandboxes, manages partial failures via deterministic fallback policies, and produces cryptographically signed execution receipts.
            </p>
          </div>

          {/* Execution Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Mode Selector */}
            <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: 3, borderRadius: 6, border: '1px solid var(--border-default)' }}>
              <button
                onClick={() => { setMode('normal'); setActiveStageIndex(-1); }}
                style={{
                  padding: '5px 12px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: mode === 'normal' ? '#272f48' : 'transparent',
                  color: mode === 'normal' ? '#ffffff' : '#94a3b8'
                }}
              >
                Normal Run
              </button>
              <button
                onClick={() => { setMode('failure'); setActiveStageIndex(-1); }}
                style={{
                  padding: '5px 12px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: mode === 'failure' ? '#3b1c24' : 'transparent',
                  color: mode === 'failure' ? '#f87171' : '#94a3b8'
                }}
              >
                Inject One Cell Failure
              </button>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunWorkflow}
              disabled={isRunning}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 16px',
                borderRadius: 6,
                background: isRunning ? 'var(--bg-surface)' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#ffffff',
                border: '1px solid var(--border-accent)',
                fontSize: 12.5,
                fontWeight: 700,
                cursor: isRunning ? 'not-allowed' : 'pointer'
              }}
            >
              <Play size={14} />
              <span>{isRunning ? 'Executing Workflow...' : 'Run Workflow'}</span>
            </button>
          </div>
        </div>

        {/* Horizontal Pipeline Stepper */}
        <div style={{ marginTop: 22 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
            Execution Pipeline Sequence
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${pipeline_stages.length}, 1fr)`, gap: 8 }}>
            {pipeline_stages.map((stage, idx) => {
              const isActive = activeStageIndex === idx;
              const isPast = activeStageIndex > idx;
              const isFinal = activeStageIndex === pipeline_stages.length - 1;
              const isFailureStage = mode === 'failure' && stage.id === 'runtimes';

              let borderColor = 'var(--border-subtle)';
              let bg = 'var(--bg-surface)';
              let textColor = 'var(--text-muted)';

              if (isActive) {
                borderColor = isFailureStage ? '#ef4444' : '#6366f1';
                bg = isFailureStage ? 'rgba(239, 68, 68, 0.15)' : 'rgba(99, 102, 241, 0.15)';
                textColor = '#ffffff';
              } else if (isPast || isFinal) {
                if (isFailureStage) {
                  borderColor = '#f87171';
                  textColor = '#f87171';
                } else {
                  borderColor = '#10b981';
                  textColor = '#34d399';
                }
              }

              return (
                <div
                  key={stage.id}
                  style={{
                    background: bg,
                    border: `1px solid ${borderColor}`,
                    borderRadius: 6,
                    padding: '10px 10px',
                    transition: 'all 0.25s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      0{idx + 1}
                    </span>
                    {isPast || isFinal ? (
                      isFailureStage ? (
                        <AlertCircle size={12} color="#f87171" />
                      ) : (
                        <CheckCircle2 size={12} color="#10b981" />
                      )
                    ) : null}
                  </div>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: textColor, marginTop: 4 }}>
                    {stage.name}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2, lineHeight: 1.3 }}>
                    {stage.description}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Execution Receipt & Runtimes Status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 16 }}>
        {/* Left: Runtime Output & Cells */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Cpu size={16} color="#818cf8" />
              <span style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>Runtime Execution Output</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                Latency: {currentResult.latency_ms} ms
              </span>
              <span style={{
                fontSize: 11,
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 4,
                fontFamily: 'var(--font-mono)',
                background: currentResult.execution_status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: currentResult.execution_status === 'SUCCESS' ? '#34d399' : '#fbbf24',
                border: `1px solid ${currentResult.execution_status === 'SUCCESS' ? '#10b981' : '#f59e0b'}`
              }}>
                {currentResult.execution_status}
              </span>
            </div>
          </div>

          {/* Cells Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {currentResult.cells.map(cell => (
              <div
                key={cell.cell_id}
                style={{
                  background: 'var(--bg-surface)',
                  padding: 12,
                  borderRadius: 6,
                  border: `1px solid ${cell.status === 'SUCCESS' ? 'var(--border-subtle)' : 'rgba(239, 68, 68, 0.4)'}`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                      cell[{cell.cell_id}]
                    </span>
                    <span style={{ fontSize: 10, padding: '1px 5px', borderRadius: 3, background: 'rgba(255,255,255,0.06)', color: '#94a3b8' }}>
                      {cell.language}
                    </span>
                  </div>
                  <span style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: cell.status === 'SUCCESS' ? '#34d399' : '#f87171'
                  }}>
                    {cell.status} ({cell.latency_ms} ms)
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Toolchain: {cell.toolchain}
                </div>
                {cell.error ? (
                  <div style={{ marginTop: 6, padding: '6px 8px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 4, color: '#f87171', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                    Error: {cell.error}
                  </div>
                ) : (
                  <div style={{ marginTop: 6, background: '#0a0c12', padding: '6px 8px', borderRadius: 4, fontSize: 10.5, fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
                    {JSON.stringify(cell.output)}
                  </div>
                )}
              </div>
            ))}
          </div>

          {mode === 'failure' && currentResult.failure_isolation && (
            <div style={{ marginTop: 12, padding: 12, background: 'rgba(245, 158, 11, 0.08)', borderRadius: 6, border: '1px solid rgba(245, 158, 11, 0.3)', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#fbbf24' }}>
                Failure Isolation & Fallback Policy Analysis
              </div>
              <div style={{ fontSize: 11, color: '#f87171' }}>
                &bull; <strong>Failed Component:</strong> {currentResult.failure_isolation.failed_component}
              </div>
              <div style={{ fontSize: 11, color: '#34d399' }}>
                &bull; <strong>Components Remaining Valid:</strong> {currentResult.failure_isolation.valid_components.join(', ')}
              </div>
              <div style={{ fontSize: 11, color: '#a78bfa' }}>
                &bull; <strong>Fallback Rule:</strong> <code>{currentResult.failure_isolation.fallback_rule}</code> ({currentResult.failure_isolation.fallback_action})
              </div>
              <div style={{ fontSize: 11, color: '#38bdf8' }}>
                &bull; <strong>Final Feature State:</strong> <span style={{ padding: '1px 6px', borderRadius: 3, background: 'rgba(245, 158, 11, 0.2)', fontWeight: 700 }}>{currentResult.failure_isolation.final_state}</span>
              </div>
              <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: 2 }}>
                {currentResult.failure_isolation.derived_rationale}
              </div>
            </div>
          )}
        </div>

        {/* Right: Cryptographic Execution Receipt */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <ShieldCheck size={16} color="#10b981" />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0' }}>Cryptographic Execution Receipt</span>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)', flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Receipt ID</div>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
              {currentResult.receipt.receipt_id}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Feature Unit</div>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#f8fafc' }}>
              {currentResult.receipt.feature_id}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Provenance Hash</div>
            <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: '#a78bfa', wordBreak: 'break-all' }}>
              {currentResult.receipt.provenance_hash}
            </div>
            <div style={{ marginTop: 'auto', paddingTop: 10, borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 6, color: '#34d399', fontSize: 11.5, fontWeight: 600 }}>
              <CheckCircle2 size={14} />
              <span>Cryptographic Lineage Verified</span>
            </div>
          </div>
        </div>
      </div>

      {/* Three Capability Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
        {capability_cards.map(card => (
          <div key={card.id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: '#ffffff', marginBottom: 4 }}>
              {card.title}
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginBottom: 10 }}>
              {card.summary}
            </div>
            <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)', fontSize: 11, fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
              {card.id === 'error_translation' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <div style={{ color: '#f87171' }}>Exception: {card.details.raw_exception}</div>
                  <div style={{ color: '#818cf8' }}>Code: {card.details.translated_code}</div>
                  <div style={{ color: '#94a3b8' }}>Fix: {card.details.remediation}</div>
                </div>
              )}
              {card.id === 'contract_guard' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <div>Contract: {card.details.contract}</div>
                  <div style={{ color: '#34d399' }}>Bound Checks: {card.details.bound_checks}</div>
                  <div style={{ color: '#94a3b8' }}>Enforcement: {card.details.enforcement}</div>
                </div>
              )}
              {card.id === 'source_traceability' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <div>Source: {card.details.source_target}</div>
                  <div style={{ color: '#38bdf8' }}>Hash: {card.details.pinned_sha256}</div>
                  <div style={{ color: '#94a3b8' }}>Lines: {card.details.span}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Error Diagnostics Panel (.polyflow/logs/errors.jsonl) */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Terminal size={16} color="#cbd5e1" />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>Diagnostic Error Log (.polyflow/logs/errors.jsonl)</span>
          </div>
          <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: 2, borderRadius: 4, border: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => setErrorSubtab('readable')}
              style={{
                padding: '3px 10px',
                borderRadius: 3,
                fontSize: 11,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: errorSubtab === 'readable' ? '#272f48' : 'transparent',
                color: errorSubtab === 'readable' ? '#ffffff' : '#94a3b8'
              }}
            >
              Readable
            </button>
            <button
              onClick={() => setErrorSubtab('raw')}
              style={{
                padding: '3px 10px',
                borderRadius: 3,
                fontSize: 11,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: errorSubtab === 'raw' ? '#272f48' : 'transparent',
                color: errorSubtab === 'raw' ? '#ffffff' : '#94a3b8'
              }}
            >
              Raw JSON
            </button>
          </div>
        </div>

        {errorSubtab === 'readable' ? (
          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11.5 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 700, color: '#f87171', fontFamily: 'var(--font-mono)' }}>[{error_log.code}] {error_log.category}</span>
              <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Timestamp: {error_log.timestamp}</span>
            </div>
            <div style={{ color: '#e2e8f0' }}>Message: {error_log.message}</div>
            <div style={{ color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>Location: {error_log.file}:{error_log.line}:{error_log.column}</div>
            <div style={{ color: '#38bdf8', marginTop: 4 }}>Recommended Action: {error_log.suggested_action}</div>
          </div>
        ) : (
          <pre style={{ margin: 0, padding: 12, background: '#0a0c12', borderRadius: 6, border: '1px solid #23293d', fontSize: 11, fontFamily: 'var(--font-mono)', color: '#cbd5e1', overflowX: 'auto' }}>
            {JSON.stringify(error_log, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
