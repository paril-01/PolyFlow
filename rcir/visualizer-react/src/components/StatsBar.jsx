import React from 'react';
import { Activity, Database, GitFork, ZoomIn, ShieldCheck, Sparkles } from 'lucide-react';

export function StatsBar({
  datasetId,
  nodeCount = 0,
  edgeCount = 0,
  layoutMode,
  zoomScale = 1.0,
  selectedNode
}) {
  return (
    <footer className="stats-bar">
      {/* Left: Dataset & Node stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Database size={13} color="#818cf8" />
          <span>REPO: <strong style={{ color: '#fff' }}>{datasetId}</strong></span>
        </div>
        <span>•</span>
        <div>NODES: <strong style={{ color: '#38bdf8' }}>{nodeCount}</strong></div>
        <span>•</span>
        <div>EDGES: <strong style={{ color: '#34d399' }}>{edgeCount}</strong></div>
      </div>

      {/* Center: Selected Node status if any */}
      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '40%', color: '#94a3b8' }}>
        {selectedNode ? (
          <span>SELECTED: <strong style={{ color: '#fbbf24' }}>{selectedNode.path}</strong></span>
        ) : (
          <span>CLICK ANY NODE TO FOCUS ILLUMINATE</span>
        )}
      </div>

      {/* Right: Layout & Engine status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <ZoomIn size={12} />
          <span>ZOOM: {(zoomScale * 100).toFixed(0)}%</span>
        </div>
        <span>•</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <ShieldCheck size={13} color="#34d399" />
          <span>STATE-SPLIT: <strong>ENFORCED</strong></span>
        </div>
        <span>•</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Activity size={12} color="#10b981" />
          <span style={{ color: '#34d399' }}>60 FPS D3-CANVAS</span>
        </div>
      </div>
    </footer>
  );
}
