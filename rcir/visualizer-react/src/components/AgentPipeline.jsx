import React, { useState } from 'react';
import { Bot, Play, RotateCcw, Terminal, Eye } from 'lucide-react';
import { AgentStageCard } from './AgentStageCard';

export function AgentPipeline({
  agentState,
  onRunPipeline,
  onCancelPipeline,
  currentRepoName,
  onHighlightTouchedNodes
}) {
  const [taskPrompt, setTaskPrompt] = useState('Add LRU caching to ListRecommendations endpoint in recommendation service');

  const {
    stages,
    isRunning,
    selectedStageId,
    setSelectedStageId,
    touchedNodes
  } = agentState;

  const currentSelectedStage = stages.find(s => s.id === selectedStageId) || stages[0];

  const presets = [
    'Add LRU caching to ListRecommendations endpoint in recommendation service',
    'Inject OpenTelemetry span tracing into gRPC recommendation handler',
    'Add input validation guard on product_ids list before model inference',
    'Refactor logger configuration into structured JSON format'
  ];

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-app)',
      padding: '16px 20px',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: 6, background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={16} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>PolyFlow AEF Autonomous Multi-Agent Pipeline</h2>
              <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                Maker → Reviewer → Implementer → Gatekeeper → Historian (§8 Invariant Synthesis)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            {isRunning ? (
              <button
                onClick={onCancelPipeline}
                className="btn btn-secondary"
                style={{ fontSize: 11.5, color: '#fb7185' }}
              >
                <RotateCcw size={13} />
                <span>Cancel</span>
              </button>
            ) : (
              <button
                onClick={() => onRunPipeline(taskPrompt)}
                className="btn btn-primary"
                style={{ fontSize: 12 }}
              >
                <Play size={13} fill="#fff" />
                <span>Execute AEF Pipeline</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Task Prompt Input */}
      <div className="glass-panel" style={{ padding: 14, marginBottom: 14 }}>
        <label style={{ fontSize: 11.5, fontWeight: 700, color: '#e2e8f0', marginBottom: 4, display: 'block' }}>
          Autonomous Engineering Objective / Task Prompt
        </label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <input
            type="text"
            className="input-text"
            value={taskPrompt}
            onChange={(e) => setTaskPrompt(e.target.value)}
            disabled={isRunning}
            style={{ flex: 1, fontSize: 12.5 }}
            placeholder="Describe the feature or refactoring task..."
          />
        </div>

        {/* Presets */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => setTaskPrompt(p)}
              disabled={isRunning}
              style={{
                background: taskPrompt === p ? '#283049' : '#141724',
                border: `1px solid ${taskPrompt === p ? '#ec4899' : '#2d354e'}`,
                color: taskPrompt === p ? '#ffffff' : '#cbd5e1',
                borderRadius: 4,
                padding: '3px 8px',
                fontSize: 11,
                cursor: 'pointer',
                fontWeight: taskPrompt === p ? 600 : 400
              }}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Responsive Stage Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
        gap: 10,
        marginBottom: 14
      }}>
        {stages.map((stage) => (
          <AgentStageCard
            key={stage.id}
            stage={stage}
            isSelected={selectedStageId === stage.id}
            onSelect={() => setSelectedStageId(stage.id)}
          />
        ))}
      </div>

      {/* Stage Output Inspector / Terminal */}
      <div className="glass-panel" style={{ flex: 1, padding: 14, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Terminal size={15} color={currentSelectedStage.color} />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>
              {currentSelectedStage.role} Output &amp; Artifacts
            </span>
          </div>

          {touchedNodes.length > 0 && (
            <button
              onClick={() => onHighlightTouchedNodes(touchedNodes)}
              className="btn btn-secondary"
              style={{ fontSize: 11, padding: '3px 8px' }}
            >
              <Eye size={13} color="#ec4899" />
              <span>Illuminate Touched Nodes on Graph</span>
            </button>
          )}
        </div>

        {/* Output Code Block */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {currentSelectedStage.output ? (
            <div className="code-block" style={{ whiteSpace: 'pre-wrap', color: '#f1f5f9', fontSize: 12 }}>
              {currentSelectedStage.output}
            </div>
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: 140,
              color: '#94a3b8',
              fontSize: 12.5,
              gap: 6
            }}>
              <Bot size={24} style={{ opacity: 0.4 }} />
              <div>Click <strong>"Execute AEF Pipeline"</strong> above to run real multi-agent generation.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
