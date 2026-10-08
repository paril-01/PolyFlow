import React, { useState, useEffect } from 'react';
import { Bot, ShieldCheck, CheckCircle2, AlertCircle, Terminal, FileCode, Check, X, ArrowRight, GitCommit } from 'lucide-react';

export function Tab04AgentValidation() {
  const [trialsData, setTrialsData] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [selectedTrialId, setSelectedTrialId] = useState('BLIND-TASK-01_rcir_turn5');

  useEffect(() => {
    fetch('/data/agent_trials.json')
      .then(r => r.json())
      .then(d => setTrialsData(d))
      .catch(err => console.warn('Could not load agent_trials.json', err));

    fetch('/data/system_status.json')
      .then(r => r.json())
      .then(d => setStatusData(d))
      .catch(err => console.warn('Could not load system_status.json', err));
  }, []);

  if (!trialsData || !statusData) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
        Loading Agent Validation & Blind Trials Data...
      </div>
    );
  }

  const { trials } = trialsData;
  const { gates } = statusData;
  const currentTrial = trials.find(t => t.trial_id === selectedTrialId) || trials[0];

  const timelineSteps = [
    { id: 'task', label: 'Task Specification' },
    { id: 'inspect', label: 'Inspect Repo' },
    { id: 'rcir', label: 'RCIR Context' },
    { id: 'patch', label: 'Generate Patch' },
    { id: 'l1', label: 'L1: Syntax' },
    { id: 'l2', label: 'L2: Targeted Tests' },
    { id: 'l3', label: 'L3: Regression' },
    { id: 'gate', label: 'Gatekeeper Release' }
  ];

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header & Blind Test Protocol Card */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', fontFamily: 'var(--font-mono)' }}>
                TAB 04 / VERIFICATION
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Autonomous Coding Loop & Multi-Level Verification
              </span>
            </div>
            <h1 style={{ fontSize: 20, fontWeight: 800, color: '#ffffff', margin: 0 }}>
              Agent Benchmark & Blind Verification Telemetry
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, maxWidth: 880 }}>
              Question: Does the system actually make and verify code changes? Trials are executed under a strict blind validation protocol with hidden evaluators, multi-level verification (L1 Syntax, L2 Targeted Behavioral Tests, L3 Regression), and adversarial gatekeeping.
            </p>
          </div>

          {/* Blind Test Header Badge Protocol Box */}
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Benchmark Mode:</span>
              <strong style={{ color: '#38bdf8' }}>BLIND</strong>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Prior report access:</span>
              <strong style={{ color: '#f87171' }}>BLOCKED</strong>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Hidden evaluator:</span>
              <strong style={{ color: '#10b981' }}>ENABLED</strong>
            </div>
          </div>
        </div>

        {/* 7 Formal Verification Gates */}
        <div style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
            Master Contract Gates (Execution Exit 0 vs Semantic Gate Verification)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(135px, 1fr))', gap: 8 }}>
            {gates.map(gate => {
              const isPassed = gate.passed;
              return (
                <div
                  key={gate.name}
                  style={{
                    background: 'var(--bg-surface)',
                    padding: '8px 10px',
                    borderRadius: 6,
                    border: `1px solid ${isPassed ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                  }}
                >
                  <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {gate.name.replace('_', ' ')}
                  </div>
                  <div style={{
                    fontSize: 11,
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: isPassed ? '#34d399' : '#f87171',
                    marginTop: 3,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4
                  }}>
                    {isPassed ? <Check size={12} /> : <X size={12} />}
                    <span>{gate.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Verification Timeline Flow */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
          Standard Verification Timeline
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${timelineSteps.length}, 1fr)`, gap: 8 }}>
          {timelineSteps.map((step, idx) => (
            <div
              key={step.id}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6,
                padding: '8px 8px'
              }}
            >
              <div style={{ fontSize: 9.5, fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                Stage {idx + 1}
              </div>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#ffffff', marginTop: 2 }}>
                {step.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Trial Explorer & Evidence Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16 }}>
        {/* Left: Trial Selector */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16, display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 10 }}>
            Blind Trials ({trials.length} Executed)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflowY: 'auto', maxHeight: 520 }}>
            {trials.map(trial => {
              const isSelected = selectedTrialId === trial.trial_id;
              const isRcir = trial.condition === 'rcir';
              return (
                <div
                  key={trial.trial_id}
                  onClick={() => setSelectedTrialId(trial.trial_id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'var(--bg-surface)',
                    border: isSelected ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: isRcir ? '#818cf8' : '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                      {trial.task_id} ({trial.condition})
                    </span>
                    <span style={{ fontSize: 10, padding: '1px 5px', borderRadius: 3, background: 'rgba(239,68,68,0.15)', color: '#f87171', fontWeight: 700 }}>
                      {trial.gatekeeper_verdict}
                    </span>
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: 4, display: 'flex', justifyContent: 'space-between' }}>
                    <span>Turns: {trial.turns_used}/5</span>
                    <span>Tokens: {trial.usage.total_tokens.toLocaleString()}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Trial Detail */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Trial Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 10, borderBottom: '1px solid var(--border-subtle)' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>
                Trial: {currentTrial.trial_id}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                Condition: {currentTrial.condition} · Turns: {currentTrial.turns_used} · Duration: {currentTrial.duration_seconds}s
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Gatekeeper Verdict</div>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#f87171', fontFamily: 'var(--font-mono)' }}>
                {currentTrial.gatekeeper_verdict}
              </div>
            </div>
          </div>

          {/* Verification Levels L1 / L2 / L3 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {/* L1 Syntax */}
            <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>L1: Syntax Check</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: currentTrial.verification.l1_syntax_passed ? '#34d399' : '#f87171', marginTop: 2 }}>
                {currentTrial.verification.l1_syntax_passed ? 'PASS' : 'FAIL'}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                PHP -l lint clean across modified files
              </div>
            </div>

            {/* L2 Targeted Test */}
            <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>L2: Targeted Behavioral Test</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: currentTrial.verification.l2_targeted_passed ? '#34d399' : '#f87171', marginTop: 2 }}>
                {currentTrial.verification.l2_targeted_passed ? 'PASS' : 'FAIL'}
              </div>
              <div style={{ fontSize: 10, color: '#f87171', marginTop: 4, fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>
                {currentTrial.verification.l2_log}
              </div>
            </div>

            {/* L3 Regression */}
            <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>L3: Regression Test Suite</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: currentTrial.verification.l3_regression_passed ? '#34d399' : '#f87171', marginTop: 2 }}>
                {currentTrial.verification.l3_regression_passed ? 'PASS' : 'FAIL'}
              </div>
              <div style={{ fontSize: 10, color: '#34d399', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
                {currentTrial.verification.l3_log}
              </div>
            </div>
          </div>

          {/* Unified Diff & Files Modified */}
          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#cbd5e1', marginBottom: 6 }}>
              Modified Files & Unified Git Diff
            </div>
            {currentTrial.files_modified.length > 0 ? (
              <pre style={{ margin: 0, fontSize: 11, fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                {currentTrial.git_diff}
              </pre>
            ) : (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No files modified before 5-turn budget limit. Model executed {currentTrial.tool_calls_executed} tool inspections and exhausted turns.
              </div>
            )}
          </div>

          {/* Raw Artifact Lineage */}
          <div style={{ fontSize: 10.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Raw Artifact Source: {currentTrial.source_artifact}
          </div>
        </div>
      </div>
    </div>
  );
}
