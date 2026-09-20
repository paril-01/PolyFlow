import React from 'react';
import { X, Copy, Check, ArrowUpRight, ArrowDownLeft, Shield } from 'lucide-react';
import { getNodeColor } from '../lib/colors';

export function NodeInspector({ node, graphData, onClose, onSelectNodeByPath }) {
  const [copied, setCopied] = React.useState(false);

  if (!node) return null;

  const nodeColor = getNodeColor(node);

  // Find incoming and outgoing edges for this node
  const outgoing = (graphData?.graph?.edges || []).filter(e => e.source === node.path);
  const incoming = (graphData?.graph?.edges || []).filter(e => e.target === node.path);

  const handleCopy = () => {
    navigator.clipboard.writeText(node.path);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lineCount = (node.end_line && node.line) ? (node.end_line - node.line + 1) : null;
  const hubScore = typeof node.hub_score === 'number' ? node.hub_score : 0.05;

  return (
    <div className="inspector-drawer">
      {/* Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-header)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor, boxShadow: `0 0 6px ${nodeColor}` }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Node Inspector
          </span>
        </div>
        <button className="btn-icon" onClick={onClose} title="Close Inspector">
          <X size={15} />
        </button>
      </div>

      {/* Content scroll area */}
      <div style={{ padding: 16, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 14 }}>
        {/* Node Identifier Card */}
        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{
              fontSize: 10.5,
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 4,
              background: '#20263c',
              color: nodeColor,
              border: `1px solid ${nodeColor}60`
            }}>
              {node.level || node.kind}
            </span>
            <button
              onClick={handleCopy}
              style={{
                background: '#1d2336',
                border: '1px solid #333d5c',
                borderRadius: 4,
                padding: '2px 8px',
                color: copied ? '#34d399' : '#cbd5e1',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 11
              }}
              title="Copy Qualified Identifier"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          <div style={{
            fontSize: 12.5,
            fontWeight: 600,
            color: '#38bdf8',
            fontFamily: 'var(--font-mono)',
            wordBreak: 'break-all',
            lineHeight: 1.4
          }}>
            {node.path}
          </div>
        </div>

        {/* Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {/* Hub Score Gauge */}
          <div className="glass-card" style={{ padding: 12 }}>
            <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4, fontWeight: 600 }}>Hub Centrality</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>
              {(hubScore * 100).toFixed(1)}%
            </div>
            <div style={{ height: 4, width: '100%', background: '#252c42', borderRadius: 2, marginTop: 8, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${Math.min(100, hubScore * 100)}%`, background: '#fbbf24' }} />
            </div>
          </div>

          {/* Code Span */}
          <div className="glass-card" style={{ padding: 12 }}>
            <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4, fontWeight: 600 }}>Source Lines</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
              {node.line ? `L${node.line}` : 'N/A'}
              {node.end_line && <span style={{ fontSize: 13, color: '#94a3b8' }}>-{node.end_line}</span>}
            </div>
            <div style={{ fontSize: 10.5, color: '#94a3b8', marginTop: 4 }}>
              {lineCount ? `${lineCount} lines` : 'Container node'}
            </div>
          </div>
        </div>

        {/* Outgoing Calls / Dependencies */}
        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#818cf8', marginBottom: 8 }}>
            <ArrowUpRight size={14} />
            <span>Dependencies / Calls ({outgoing.length})</span>
          </div>
          {outgoing.length === 0 ? (
            <div style={{ fontSize: 11.5, color: '#94a3b8', fontStyle: 'italic' }}>No outgoing dependencies</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxHeight: 150, overflowY: 'auto' }}>
              {outgoing.slice(0, 15).map((e, idx) => (
                <div
                  key={idx}
                  onClick={() => onSelectNodeByPath(e.target)}
                  style={{
                    padding: '5px 8px',
                    borderRadius: 4,
                    background: '#1a1f30',
                    border: '1px solid #2d3652',
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    color: '#93c5fd',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '82%' }}>
                    {e.target.split('::').pop()}
                  </span>
                  <span style={{ fontSize: 9.5, color: '#94a3b8', textTransform: 'uppercase' }}>{e.edge_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Incoming Callers */}
        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#34d399', marginBottom: 8 }}>
            <ArrowDownLeft size={14} />
            <span>Incoming Callers ({incoming.length})</span>
          </div>
          {incoming.length === 0 ? (
            <div style={{ fontSize: 11.5, color: '#94a3b8', fontStyle: 'italic' }}>Root or standalone entrypoint</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, maxHeight: 150, overflowY: 'auto' }}>
              {incoming.slice(0, 15).map((e, idx) => (
                <div
                  key={idx}
                  onClick={() => onSelectNodeByPath(e.source)}
                  style={{
                    padding: '5px 8px',
                    borderRadius: 4,
                    background: '#1a1f30',
                    border: '1px solid #2d3652',
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    color: '#6ee7b7',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '82%' }}>
                    {e.source.split('::').pop()}
                  </span>
                  <span style={{ fontSize: 9.5, color: '#94a3b8', textTransform: 'uppercase' }}>{e.edge_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* State-Split Invariant Status */}
        <div className="glass-card" style={{ padding: 12, border: '1px solid rgba(245, 158, 11, 0.4)', background: 'rgba(245, 158, 11, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#fbbf24', marginBottom: 6 }}>
            <Shield size={14} />
            <span>State-Split Invariant Status</span>
          </div>
          <div style={{ fontSize: 11.5, color: '#e2e8f0', lineHeight: 1.4 }}>
            Declaration signature (<code style={{ color: '#38bdf8' }}>interface_hash</code>) separated from body (<code style={{ color: '#34d399' }}>body_hash</code>). Modifications to body preserve caller cache retention!
          </div>
        </div>
      </div>
    </div>
  );
}
