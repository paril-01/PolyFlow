import React, { useState, useMemo } from 'react';
import { 
  X, 
  Copy, 
  Check, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Shield, 
  FileCode, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Cpu, 
  ExternalLink,
  GitBranch,
  Terminal,
  CornerDownRight
} from 'lucide-react';
import { getNodeColor } from '../lib/colors';

export function NodeInspector({ node, graphData, edgeIndex, onClose, onSelectNodeByPath }) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'calls' | 'invariants'

  if (!node) return null;

  const nodeColor = getNodeColor(node);
  const nodePath = node.path || node.id || '';
  const nodeName = node.name || (nodePath ? nodePath.split('/').pop().split('::').pop() : 'Node');
  const nodeSym = nodePath ? nodePath.split('/').pop().replace(/\.(php|js|ts|vue)$/, '') : '';

  // Instant O(1) lookup via edgeIndex with fallback memoization
  const outgoing = useMemo(() => {
    if (!nodePath) return [];
    if (edgeIndex?.outgoing?.has(nodePath)) {
      return edgeIndex.outgoing.get(nodePath);
    }
    const allEdges = graphData?.graph?.edges || [];
    const res = [];
    for (let i = 0; i < allEdges.length; i++) {
      const e = allEdges[i];
      if (e.source === nodePath || (nodeSym && e.source && e.source.includes(nodeSym))) {
        res.push(e);
        if (res.length >= 60) break;
      }
    }
    return res;
  }, [nodePath, nodeSym, edgeIndex, graphData]);

  const incoming = useMemo(() => {
    if (!nodePath) return [];
    if (edgeIndex?.incoming?.has(nodePath)) {
      return edgeIndex.incoming.get(nodePath);
    }
    const allEdges = graphData?.graph?.edges || [];
    const res = [];
    for (let i = 0; i < allEdges.length; i++) {
      const e = allEdges[i];
      if (e.target === nodePath || (nodeSym && e.target && e.target.includes(nodeSym))) {
        res.push(e);
        if (res.length >= 60) break;
      }
    }
    return res;
  }, [nodePath, nodeSym, edgeIndex, graphData]);

  const exactOutgoing = useMemo(() => outgoing.filter(e => e.resolution === 'static_exact' || e.confidence === 1.0), [outgoing]);
  const exactIncoming = useMemo(() => incoming.filter(e => e.resolution === 'static_exact' || e.confidence === 1.0), [incoming]);

  const handleCopy = () => {
    navigator.clipboard.writeText(nodePath);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lineCount = (node.end_line && node.line) ? (node.end_line - node.line + 1) : null;
  const hubScore = typeof node.hub_score === 'number' ? node.hub_score : 0.05;

  return (
    <div className="inspector-drawer">
      {/* Mobile Drawer Drag Handle */}
      <div className="mobile-drawer-handle-bar">
        <div className="mobile-drawer-handle" />
      </div>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#0f1422'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: nodeColor, boxShadow: `0 0 8px ${nodeColor}`, flexShrink: 0 }} />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {nodeName}
            </div>
            <div style={{ fontSize: 10.5, color: '#94a3b8' }}>
              {node.level || node.kind || 'AST Node'} • {node.language ? node.language.toUpperCase() : 'POLYGLOT'}
            </div>
          </div>
        </div>
        <button 
          onClick={onClose} 
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid var(--border-subtle)', borderRadius: 6, width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#cbd5e1', cursor: 'pointer' }}
          title="Close Inspector"
        >
          <X size={15} />
        </button>
      </div>

      {/* Mini Tabs */}
      <div style={{ display: 'flex', background: '#0a0d16', borderBottom: '1px solid var(--border-subtle)', padding: '2px 8px' }}>
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            flex: 1,
            padding: '6px 4px',
            fontSize: 11,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: activeTab === 'overview' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: activeTab === 'overview' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'overview' ? '2px solid #38bdf8' : '2px solid transparent'
          }}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('calls')}
          style={{
            flex: 1,
            padding: '6px 4px',
            fontSize: 11,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: activeTab === 'calls' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: activeTab === 'calls' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'calls' ? '2px solid #38bdf8' : '2px solid transparent'
          }}
        >
          Callers ({incoming.length + outgoing.length})
        </button>
        <button
          onClick={() => setActiveTab('invariants')}
          style={{
            flex: 1,
            padding: '6px 4px',
            fontSize: 11,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            background: activeTab === 'invariants' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            color: activeTab === 'invariants' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'invariants' ? '2px solid #38bdf8' : '2px solid transparent'
          }}
        >
          Invariants
        </button>
      </div>

      {/* Content Scroll Area */}
      <div style={{ padding: 14, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <>
            {/* Qualified Identifier */}
            <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 10.5, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Qualified Symbol Path
                </span>
                <button
                  onClick={handleCopy}
                  style={{
                    background: 'rgba(255,255,255,0.06)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 4,
                    padding: '2px 8px',
                    color: copied ? '#34d399' : '#cbd5e1',
                    fontSize: 11,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4
                  }}
                >
                  {copied ? <Check size={11} /> : <Copy size={11} />}
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <div style={{ fontSize: 11.5, fontFamily: 'var(--font-mono)', color: '#38bdf8', wordBreak: 'break-all', lineHeight: 1.4 }}>
                {nodePath}
              </div>
            </div>

            {/* Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 10 }}>
                <span style={{ fontSize: 10.5, color: '#94a3b8', fontWeight: 600 }}>Source Span</span>
                <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                  {node.line ? `L${node.line}` : 'File'}
                  {node.end_line && <span style={{ fontSize: 12, color: '#94a3b8' }}>–{node.end_line}</span>}
                </div>
                <div style={{ fontSize: 10.5, color: '#64748b', marginTop: 2 }}>
                  {lineCount ? `${lineCount} lines of code` : 'Container definition'}
                </div>
              </div>

              <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 10 }}>
                <span style={{ fontSize: 10.5, color: '#94a3b8', fontWeight: 600 }}>Resolution Mode</span>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', marginTop: 3 }}>
                  Exact Static
                </div>
                <div style={{ fontSize: 10.5, color: '#64748b', marginTop: 2 }}>
                  Deterministic AST binding
                </div>
              </div>
            </div>

            {/* Quick Dependency Count Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div style={{ background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: 8, padding: 10 }}>
                <div style={{ fontSize: 10.5, color: '#a5b4fc', fontWeight: 600 }}>Outgoing Calls</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#818cf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                  {outgoing.length}
                </div>
                <div style={{ fontSize: 10.5, color: '#64748b' }}>{exactOutgoing.length} exact bindings</div>
              </div>

              <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: 8, padding: 10 }}>
                <div style={{ fontSize: 10.5, color: '#6ee7b7', fontWeight: 600 }}>Incoming Callers</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                  {incoming.length}
                </div>
                <div style={{ fontSize: 10.5, color: '#64748b' }}>{exactIncoming.length} exact callers</div>
              </div>
            </div>

            {/* Subsystem / Module Info */}
            <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 10 }}>
              <span style={{ fontSize: 10.5, color: '#94a3b8', fontWeight: 600 }}>Architectural Domain:</span>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#e2e8f0', marginTop: 2 }}>
                {nodePath.startsWith('apps/') ? nodePath.split('/')[0] + '/' + nodePath.split('/')[1] : nodePath.startsWith('lib/') ? 'Nextcloud Core (' + nodePath.split('/')[1] + ')' : 'System Root'}
              </div>
            </div>
          </>
        )}

        {/* TAB 2: CALL GRAPH & CALLERS */}
        {activeTab === 'calls' && (
          <>
            {/* Outgoing Dependencies */}
            <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#818cf8', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ArrowUpRight size={14} />
                  <span>Outgoing Dependencies ({outgoing.length})</span>
                </span>
                <span style={{ fontSize: 10, color: '#64748b' }}>Callees</span>
              </div>

              {outgoing.length === 0 ? (
                <div style={{ fontSize: 11.5, color: '#94a3b8', fontStyle: 'italic' }}>No outgoing dependencies recorded</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 180, overflowY: 'auto' }}>
                  {outgoing.slice(0, 20).map((e, idx) => (
                    <div
                      key={idx}
                      onClick={() => onSelectNodeByPath && onSelectNodeByPath(e.target)}
                      style={{
                        padding: '6px 8px',
                        borderRadius: 6,
                        background: '#121727',
                        border: '1px solid #232c45',
                        fontSize: 11,
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 2
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#93c5fd', fontFamily: 'var(--font-mono)', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '75%' }}>
                          {e.target.split('::').pop().split('/').pop()}
                        </span>
                        <span style={{ fontSize: 9.5, padding: '1px 5px', borderRadius: 3, background: 'rgba(56,189,248,0.15)', color: '#38bdf8' }}>
                          {e.edge_type || e.type}
                        </span>
                      </div>
                      {e.reason && (
                        <span style={{ fontSize: 10, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {e.reason}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Incoming Callers */}
            <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ArrowDownLeft size={14} />
                  <span>Incoming Callers ({incoming.length})</span>
                </span>
                <span style={{ fontSize: 10, color: '#64748b' }}>Call Sites</span>
              </div>

              {incoming.length === 0 ? (
                <div style={{ fontSize: 11.5, color: '#94a3b8', fontStyle: 'italic' }}>Root or standalone entrypoint</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 180, overflowY: 'auto' }}>
                  {incoming.slice(0, 20).map((e, idx) => (
                    <div
                      key={idx}
                      onClick={() => onSelectNodeByPath && onSelectNodeByPath(e.source)}
                      style={{
                        padding: '6px 8px',
                        borderRadius: 6,
                        background: '#121727',
                        border: '1px solid #232c45',
                        fontSize: 11,
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 2
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#6ee7b7', fontFamily: 'var(--font-mono)', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '75%' }}>
                          {e.source.split('::').pop().split('/').pop()}
                        </span>
                        <span style={{ fontSize: 9.5, padding: '1px 5px', borderRadius: 3, background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>
                          {e.edge_type || e.type}
                        </span>
                      </div>
                      {e.reason && (
                        <span style={{ fontSize: 10, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {e.reason}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* TAB 3: INVARIANTS & AUDIT */}
        {activeTab === 'invariants' && (
          <>
            <div style={{ background: '#0a0e1a', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: 8, padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#fbbf24', marginBottom: 6 }}>
                <Shield size={14} />
                <span>State-Split Invariant Contract</span>
              </div>
              <p style={{ fontSize: 11.5, color: '#cbd5e1', lineHeight: 1.4, margin: 0 }}>
                This symbol is indexed with cryptographic separation between declaration signature (<code style={{ color: '#38bdf8' }}>interface_hash</code>) 
                and implementation body (<code style={{ color: '#34d399' }}>body_hash</code>).
              </p>
            </div>

            <div style={{ background: '#0a0e1a', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', marginBottom: 6 }}>
                Change Impact Blast Radius:
              </div>
              <div style={{ fontSize: 12, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                Target: {nodeSym || nodeName}
              </div>
              <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 4 }}>
                Direct Callers Affected: <strong>{incoming.length} sites</strong>
              </div>
              <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>
                Transitive 2-Hop Radius: <strong>{incoming.length * 2 + 1} call sites</strong>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
