import React from 'react';
import { Network, FolderTree, Cpu, BarChart3, Bot, Sparkles, ShieldCheck, X, ChevronLeft, ChevronRight, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { LEVEL_COLORS } from '../lib/colors';

export function Sidebar({
  activeTab,
  onSelectTab,
  datasetInfo,
  nodeCount = 0,
  edgeCount = 0,
  isOpen,
  onClose,
  isCollapsed = false,
  onToggleCollapse
}) {
  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: Sparkles, badge: 'Key Proofs', highlight: true },
    { id: 'graph', label: 'Nextcloud 50k Graph', icon: Network, badge: '143k Edges' },
    { id: 'agent', label: '6-Stage Agent Pool', icon: Bot, badge: 'AEF Gatekeeper' },
    { id: 'benchmarks', label: 'Benchmark Arena', icon: BarChart3, badge: 'Empirical' },
    { id: 'studio', label: 'Polyglot Studio', icon: Cpu, badge: 'Native SDK' },
    { id: 'proof', label: 'Proof & Audit Center', icon: ShieldCheck, badge: 'Verifiable' },
    { id: 'tree', label: 'Tree Explorer', icon: FolderTree, badge: 'Hierarchy' },
    { id: 'retrieval', label: 'Retrieval Simulator', icon: Network, badge: 'Knapsack' }
  ];

  return (
    <>
      {isOpen && (
        <div 
          className="mobile-overlay" 
          onClick={onClose} 
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)', zIndex: 90 }} 
        />
      )}
      <aside className={`sidebar-panel ${isOpen ? 'mobile-open' : ''} ${isCollapsed ? 'collapsed' : ''}`}>
        {/* Mobile Header with Close Button */}
        <div className="mobile-sidebar-header" style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-subtle)', display: 'none', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 800, color: '#fff' }}>PolyFlow Suite</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* Desktop Collapse / Expand Header Bar */}
        <div className="sidebar-desktop-header" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          padding: isCollapsed ? '10px 0' : '10px 12px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(18, 21, 32, 0.9)'
        }}>
          {!isCollapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, minWidth: 0 }}>
              <div style={{
                width: 22,
                height: 22,
                borderRadius: 5,
                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Network size={13} color="#fff" />
              </div>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                PolyFlow Suite
              </span>
            </div>
          )}
          <button
            onClick={onToggleCollapse}
            className="sidebar-collapse-btn"
            title={isCollapsed ? "Expand sidebar (Ctrl+B)" : "Collapse sidebar (Ctrl+B)"}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 5,
              width: 26,
              height: 26,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#94a3b8',
              cursor: 'pointer',
              flexShrink: 0
            }}
          >
            {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>

        {/* Navigation Items */}
        <div style={{ padding: isCollapsed ? '12px 6px' : '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, flex: 1, overflowY: 'auto' }}>
          {!isCollapsed && (
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 8px 6px' }}>
              System Modules
            </div>
          )}

          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <div
                key={tab.id}
                className={`nav-item ${isActive ? 'active' : ''} ${isCollapsed ? 'collapsed' : ''}`}
                title={tab.label}
                onClick={() => {
                  onSelectTab(tab.id);
                  if (onClose) onClose();
                }}
                style={{
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  padding: isCollapsed ? '9px 0' : '9px 12px'
                }}
              >
                <Icon size={16} color={isActive ? '#818cf8' : tab.highlight ? '#ec4899' : '#cbd5e1'} style={{ flexShrink: 0 }} />
                {!isCollapsed && (
                  <>
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tab.label}</span>
                    {tab.highlight ? (
                      <span className="badge badge-purple" style={{ fontSize: 9, padding: '1px 5px', flexShrink: 0 }}>
                        <Sparkles size={8.5} />
                        <span>{tab.badge}</span>
                      </span>
                    ) : (
                      <span style={{ fontSize: 9.5, color: '#94a3b8', flexShrink: 0 }}>{tab.badge}</span>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>

        {/* AST Level Legend (shown only when expanded) */}
        {!isCollapsed && (
          <div className="sidebar-legend" style={{ padding: '10px 12px', borderTop: '1px solid var(--border-default)', background: '#121520' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              AST Hierarchy Levels
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: LEVEL_COLORS.root, flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0' }}>Root Package</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: LEVEL_COLORS.module, flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0' }}>Module / Dir</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: LEVEL_COLORS.file, flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0' }}>Source File</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: LEVEL_COLORS.class, flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0' }}>Class Def</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: LEVEL_COLORS.function, flexShrink: 0 }} />
                <span style={{ color: '#e2e8f0' }}>Function / Method</span>
              </div>
            </div>
          </div>
        )}

        {/* Dataset Summary Footer */}
        <div style={{ padding: isCollapsed ? '8px 4px' : '10px 12px', borderTop: '1px solid var(--border-default)', background: '#0e111a', textAlign: isCollapsed ? 'center' : 'left' }}>
          {!isCollapsed ? (
            <>
              <div style={{ fontSize: 9.5, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Active Repo</div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 1 }}>
                {datasetInfo?.name || 'Nextcloud Server Core'}
              </div>
              <div style={{ display: 'flex', gap: 5, marginTop: 3, fontSize: 10.5, color: '#a5b4fc', fontFamily: 'var(--font-mono)' }}>
                <span>{nodeCount} nodes</span>
                <span>•</span>
                <span>{edgeCount} edges</span>
              </div>
            </>
          ) : (
            <div title={`${datasetInfo?.name || 'Nextcloud'} (${nodeCount} nodes, ${edgeCount} edges)`} style={{ display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
