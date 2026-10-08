import React, { useState, useEffect } from 'react';
import { Network, Database, Layers, ArrowRight, CheckCircle2, AlertCircle, FileCode, Cpu, BarChart2, DollarSign } from 'lucide-react';
import { GraphCanvas } from './GraphCanvas';
import { Graph3DCanvas } from './Graph3DCanvas';

export function Tab03RCIR({
  graphData,
  layout,
  layoutMode,
  setLayoutMode,
  selectedNode,
  setSelectedNode,
  hoveredNode,
  setHoveredNode,
  connectedNeighbors,
  highlightedNodes,
  searchQuery,
  matchingNodePaths,
  camera,
  setCamera,
  handleWheel,
  handleMouseDown,
  handleMouseMove,
  handleMouseUp,
  zoomIn,
  zoomOut,
  resetCamera
}) {
  const [subtab, setSubtab] = useState('structure'); // 'structure' | 'tokens'
  const [pipelineData, setPipelineData] = useState(null);
  const [tokenData, setTokenData] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState('BLIND-TASK-01');
  const [showInteractiveGraph, setShowInteractiveGraph] = useState(false);

  useEffect(() => {
    fetch('/data/rcir_pipeline.json')
      .then(r => r.json())
      .then(d => {
        setPipelineData(d);
        if (d?.ranked_candidates?.length > 0) {
          setSelectedCandidate(d.ranked_candidates[0]);
        }
      })
      .catch(err => console.warn('Could not load rcir_pipeline.json', err));

    fetch('/data/token_ab.json')
      .then(r => r.json())
      .then(d => setTokenData(d))
      .catch(err => console.warn('Could not load token_ab.json', err));
  }, []);

  if (!pipelineData || !tokenData) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
        Loading RCIR Pipeline & Token Data...
      </div>
    );
  }

  const { pipeline_stages, graph_summary, ranked_candidates } = pipelineData;
  const currentPair = tokenData.pairs.find(p => p.task_id === selectedTaskId) || tokenData.pairs[0];

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header Card with Subtab Navigation */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', fontFamily: 'var(--font-mono)' }}>
                TAB 03 / RCIR ENGINE
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Repository-Scale Code Intelligence & Context Compiler
              </span>
            </div>
            <h1 style={{ fontSize: 20, fontWeight: 800, color: '#ffffff', margin: 0 }}>
              RCIR: Architecture & Token Telemetry
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, maxWidth: 880 }}>
              Question: How does RCIR reduce repository context for an AI agent? RCIR constructs a canonical multi-relational code graph, evaluates change intent across candidate evidence channels, and compresses context via bounded knapsack packing.
            </p>
          </div>

          {/* Subtab Toggle Buttons */}
          <div style={{ display: 'flex', background: 'var(--bg-surface)', padding: 3, borderRadius: 6, border: '1px solid var(--border-default)' }}>
            <button
              onClick={() => setSubtab('structure')}
              style={{
                padding: '6px 14px',
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: subtab === 'structure' ? '#272f48' : 'transparent',
                color: subtab === 'structure' ? '#ffffff' : '#94a3b8'
              }}
            >
              Structure & Graph
            </button>
            <button
              onClick={() => setSubtab('tokens')}
              style={{
                padding: '6px 14px',
                borderRadius: 4,
                fontSize: 12,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: subtab === 'tokens' ? '#272f48' : 'transparent',
                color: subtab === 'tokens' ? '#ffffff' : '#94a3b8'
              }}
            >
              Token Usage Telemetry
            </button>
          </div>
        </div>
      </div>

      {/* Subtab A: Structure & Graph Pipeline */}
      {subtab === 'structure' && (
        <>
          {/* Horizontal Pipeline Sequence */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                RCIR Retrieval & Context Compilation Flow
              </div>
              <button
                onClick={() => setShowInteractiveGraph(!showInteractiveGraph)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 600,
                  background: showInteractiveGraph ? 'rgba(99, 102, 241, 0.2)' : 'var(--bg-surface)',
                  color: showInteractiveGraph ? '#818cf8' : 'var(--text-muted)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer'
                }}
              >
                {showInteractiveGraph ? 'Hide Interactive Graph' : 'Show Nextcloud AST Graph View'}
              </button>
            </div>

            {/* Stages Row */}
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${pipeline_stages.length}, 1fr)`, gap: 8 }}>
              {pipeline_stages.map((stage, idx) => (
                <div
                  key={stage.id}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '10px 8px'
                  }}
                >
                  <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                    0{idx + 1}
                  </div>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: '#ffffff', marginTop: 3 }}>
                    {stage.name}
                  </div>
                  <div style={{ fontSize: 10.5, fontWeight: 600, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {stage.metric}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.3 }}>
                    {stage.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Graph Embed if toggled */}
          {showInteractiveGraph && graphData && (
            <div style={{ height: 440, borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border-default)', position: 'relative' }}>
              {layoutMode === '3d' ? (
                <Graph3DCanvas
                  data={graphData}
                  selectedNode={selectedNode}
                  onSelectNode={setSelectedNode}
                  searchQuery={searchQuery}
                  onResetCamera={resetCamera}
                />
              ) : (
                <GraphCanvas
                  layout={layout}
                  selectedNode={selectedNode}
                  onSelectNode={setSelectedNode}
                  hoveredNode={hoveredNode}
                  onHoverNode={setHoveredNode}
                  connectedNeighbors={connectedNeighbors}
                  highlightedNodes={highlightedNodes}
                  searchQuery={searchQuery}
                  matchingNodePaths={matchingNodePaths}
                  camera={camera}
                  setCamera={setCamera}
                  handleWheel={handleWheel}
                  handleMouseDown={handleMouseDown}
                  handleMouseMove={handleMouseMove}
                  handleMouseUp={handleMouseUp}
                  zoomIn={zoomIn}
                  zoomOut={zoomOut}
                  resetCamera={resetCamera}
                  layoutMode={layoutMode}
                  onToggleLayout={setLayoutMode}
                />
              )}
            </div>
          )}

          {/* Ranked Candidates Inspection */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Candidate List */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 10 }}>
                Ranked Candidates for Target ChangeSpec
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {ranked_candidates.map(rc => {
                  const isSelected = selectedCandidate?.path === rc.path;
                  return (
                    <div
                      key={rc.path}
                      onClick={() => setSelectedCandidate(rc)}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 6,
                        background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'var(--bg-surface)',
                        border: isSelected ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                          {rc.path}
                        </span>
                        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                          score: {rc.rank_score}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 11, color: 'var(--text-muted)' }}>
                        <span>Channel: {rc.channel}</span>
                        <span>Confidence: {rc.confidence}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Candidate Evidence Inspector */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 10 }}>
                Candidate Selection Provenance
              </div>
              {selectedCandidate ? (
                <div style={{ background: 'var(--bg-surface)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>File Path</div>
                    <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#ffffff', fontWeight: 600 }}>
                      {selectedCandidate.path}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Selection Rationale</div>
                    <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 2 }}>
                      {selectedCandidate.reason}
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 4 }}>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Evidence Channel</div>
                      <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                        {selectedCandidate.channel}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Confidence</div>
                      <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#10b981' }}>
                        {selectedCandidate.confidence}%
                      </div>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>AST Symbol Span</div>
                    <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e2e8f0' }}>
                      Lines {selectedCandidate.span.start} - {selectedCandidate.span.end}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>Select a candidate to view evidence</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Subtab B: Token Usage Telemetry */}
      {subtab === 'tokens' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Top Task Selector & Benchmark Metadata */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Active Evaluation Task:</span>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#ffffff', marginTop: 2 }}>
                  {currentPair.task_id}: {currentPair.title}
                </div>
              </div>

              {/* Task Selector Dropdown */}
              <select
                value={selectedTaskId}
                onChange={e => setSelectedTaskId(e.target.value)}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-default)',
                  color: '#ffffff',
                  padding: '6px 12px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer'
                }}
              >
                {tokenData.pairs.map(p => (
                  <option key={p.task_id} value={p.task_id}>
                    {p.task_id} — {p.title}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: 16, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-subtle)', fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              <span>Provider: <strong style={{ color: '#ffffff' }}>{tokenData.provider}</strong></span>
              <span>Model: <strong style={{ color: '#ffffff' }}>{tokenData.model}</strong></span>
              <span>Turn Budget: <strong style={{ color: '#ffffff' }}>{tokenData.turn_budget} turns</strong></span>
              <span>Source: <strong style={{ color: '#38bdf8' }}>{tokenData.measurement_source}</strong></span>
              <span>Individual Trials: <strong style={{ color: '#ffffff' }}>{tokenData.individual_trials}</strong></span>
            </div>
          </div>

          {/* Synchronized Side-by-Side Comparison Lanes */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 140px 1fr', gap: 12, alignItems: 'stretch' }}>
            {/* Left Lane: Baseline (WITHOUT RCIR) */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
              <div style={{ paddingBottom: 10, borderBottom: '1px solid var(--border-subtle)', marginBottom: 12 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Condition A: WITHOUT RCIR
                </span>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#cbd5e1', marginTop: 2 }}>
                  Standard Lexical File & Ast Search
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Prompt Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.baseline.prompt_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Completion Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.baseline.completion_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.baseline.total_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Turns Used</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.baseline.turns_used} / 5
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 12, padding: 10, background: 'var(--bg-surface)', borderRadius: 6, border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>Wall Duration:</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#ffffff' }}>
                  {currentPair.baseline.duration_seconds}s
                </span>
              </div>
              <div style={{ marginTop: 6, padding: 10, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 6, border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11.5, color: '#f87171' }}>Gatekeeper Release:</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#f87171' }}>
                  {currentPair.baseline.gatekeeper}
                </span>
              </div>
            </div>

            {/* Center: Empirical Measured Delta */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-surface)', borderRadius: 10, border: '1px solid var(--border-default)', padding: 12, textAlign: 'center' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Input Token Delta
              </div>
              <div style={{
                fontSize: 22,
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                color: currentPair.input_token_delta_pct > 0 ? '#10b981' : '#f87171',
                marginTop: 6
              }}>
                {currentPair.input_token_delta_pct > 0 ? `+${currentPair.input_token_delta_pct}%` : `${currentPair.input_token_delta_pct}%`}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                {currentPair.input_token_delta_pct > 0 ? 'RCIR Reduced Tokens' : 'RCIR Used More Tokens'}
              </div>
              <div style={{ marginTop: 12, fontSize: 10, fontFamily: 'var(--font-mono)', color: '#818cf8', padding: '2px 6px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.15)' }}>
                {currentPair.status}
              </div>
            </div>

            {/* Right Lane: RCIR (WITH RCIR) */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
              <div style={{ paddingBottom: 10, borderBottom: '1px solid var(--border-subtle)', marginBottom: 12 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Condition B: WITH RCIR
                </span>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginTop: 2 }}>
                  Canonical Graph Knapsack Context
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Prompt Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.rcir.prompt_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Completion Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.rcir.completion_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total Tokens</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.rcir.total_tokens.toLocaleString()}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-surface)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Turns Used</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                    {currentPair.rcir.turns_used} / 5
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 12, padding: 10, background: 'var(--bg-surface)', borderRadius: 6, border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>Wall Duration:</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#ffffff' }}>
                  {currentPair.rcir.duration_seconds}s
                </span>
              </div>
              <div style={{ marginTop: 6, padding: 10, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 6, border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11.5, color: '#f87171' }}>Gatekeeper Release:</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#f87171' }}>
                  {currentPair.rcir.gatekeeper}
                </span>
              </div>
            </div>
          </div>

          {/* IDE Credits & Reference API Scenario Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 14 }}>
            {/* IDE Credits Card */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <DollarSign size={16} color="#fbbf24" />
                <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>IDE Credits Telemetry</span>
              </div>
              <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Measurement State:</span>
                  <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 8px', borderRadius: 4 }}>
                    {tokenData.ide_credits.status}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.4 }}>
                  {tokenData.ide_credits.rationale}
                </div>
              </div>
            </div>

            {/* Reference API Cost Scenario Card */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <BarChart2 size={16} color="#38bdf8" />
                <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>Reference API Cost Scenario (Hypothetical)</span>
              </div>
              <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)', fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.4 }}>
                <div>{tokenData.reference_cost_scenario.note}</div>
                <div style={{ marginTop: 6, fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
                  Model: {tokenData.reference_cost_scenario.reference_model} · Input: ${tokenData.reference_cost_scenario.reference_pricing.input_per_million_usd}/1M · Output: ${tokenData.reference_cost_scenario.reference_pricing.output_per_million_usd}/1M
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
