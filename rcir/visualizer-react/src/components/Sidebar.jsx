import React from 'react';
import { Network, FolderTree, Cpu, BarChart3, Bot, Sparkles, ShieldCheck } from 'lucide-react';
import { LEVEL_COLORS } from '../lib/colors';

export function Sidebar({ activeTab, onSelectTab, datasetInfo, nodeCount = 0, edgeCount = 0 }) {
  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: Sparkles, badge: 'Key Proofs', highlight: true },
    { id: 'graph', label: 'Nextcloud 50k Graph', icon: Network, badge: '110k Edges' },
    { id: 'agent', label: '6-Stage Agent Pool', icon: Bot, badge: 'AEF Gatekeeper' },
    { id: 'benchmarks', label: 'Benchmark Arena', icon: BarChart3, badge: 'Empirical' },
    { id: 'studio', label: 'Polyglot Studio', icon: Cpu, badge: 'Native SDK' },
    { id: 'proof', label: 'Proof & Audit Center', icon: ShieldCheck, badge: 'Verifiable' },
    { id: 'tree', label: 'Tree Explorer', icon: FolderTree, badge: 'Hierarchy' },
    { id: 'retrieval', label: 'Retrieval Simulator', icon: Network, badge: 'Knapsack' }
  ];

  return (
    <aside className="sidebar-panel">
      {/* Navigation Items */}
      <div style={{ padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
        <div style={{ fontSize: 10.5, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 8px 8px' }}>
          System Modules
        </div>

        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <div
              key={tab.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(tab.id)}
            >
              <Icon size={16} color={isActive ? '#818cf8' : tab.highlight ? '#ec4899' : '#cbd5e1'} />
              <span style={{ flex: 1 }}>{tab.label}</span>
              {tab.highlight ? (
                <span className="badge badge-purple" style={{ fontSize: 9.5, padding: '1px 5px' }}>
                  <Sparkles size={9} />
                  <span>{tab.badge}</span>
                </span>
              ) : (
                <span style={{ fontSize: 10, color: '#94a3b8' }}>{tab.badge}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* AST Level Legend */}
      <div className="sidebar-legend" style={{ padding: '12px 14px', borderTop: '1px solid var(--border-default)', background: '#121520' }}>
        <div style={{ fontSize: 10.5, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
          AST Hierarchy Levels
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, fontSize: 11.5 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: LEVEL_COLORS.root }} />
            <span style={{ color: '#e2e8f0' }}>Root Package</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: LEVEL_COLORS.module }} />
            <span style={{ color: '#e2e8f0' }}>Module / Dir</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: LEVEL_COLORS.file }} />
            <span style={{ color: '#e2e8f0' }}>Source File</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: LEVEL_COLORS.class }} />
            <span style={{ color: '#e2e8f0' }}>Class Def</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: LEVEL_COLORS.function }} />
            <span style={{ color: '#e2e8f0' }}>Function / Method</span>
          </div>
        </div>
      </div>

      {/* Dataset Summary Footer */}
      <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border-default)', background: '#0e111a' }}>
        <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Active Repo</div>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 2 }}>
          {datasetInfo?.name || 'OTel Recommendation'}
        </div>
        <div style={{ display: 'flex', gap: 6, marginTop: 4, fontSize: 11, color: '#a5b4fc', fontFamily: 'var(--font-mono)' }}>
          <span>{nodeCount} nodes</span>
          <span>•</span>
          <span>{edgeCount} edges</span>
        </div>
      </div>
    </aside>
  );
}
