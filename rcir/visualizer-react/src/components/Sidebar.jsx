import React from 'react';
import { Layers, PlayCircle, Network, ShieldCheck, Database, X, ChevronLeft, ChevronRight } from 'lucide-react';

export function Sidebar({
  activeTab,
  onSelectTab,
  isOpen,
  onClose,
  isCollapsed = false,
  onToggleCollapse
}) {
  const tabs = [
    { id: 'polyflow', label: '01 PolyFlow — Feature Closure', icon: Layers, badge: 'Architecture' },
    { id: 'interpreter', label: '02 Interpreter', icon: PlayCircle, badge: 'Runtime' },
    { id: 'rcir', label: '03 RCIR', icon: Network, badge: 'Context' },
    { id: 'agent', label: '04 Agent & Validation', icon: ShieldCheck, badge: 'Blind A/B' },
    { id: 'erpnext', label: '05 ERPNext Scale', icon: Database, badge: 'Enterprise' }
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
          <span style={{ fontSize: 13, fontWeight: 800, color: '#fff' }}>PolyFlow</span>
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
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Network size={13} color="#fff" />
              </div>
              <span style={{ fontSize: 12, fontWeight: 800, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                PolyFlow
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

        {/* Navigation Items (Exactly 5 Primary Tabs) */}
        <div style={{ padding: isCollapsed ? '12px 6px' : '14px 10px', display: 'flex', flexDirection: 'column', gap: 4, flex: 1, overflowY: 'auto' }}>
          {!isCollapsed && (
            <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 8px 6px' }}>
              System Showcase
            </div>
          )}
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  onSelectTab(tab.id);
                  if (isOpen) onClose();
                }}
                className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                title={isCollapsed ? tab.label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  width: '100%',
                  padding: isCollapsed ? '8px 0' : '8px 10px',
                  justifyContent: isCollapsed ? 'center' : 'flex-start',
                  borderRadius: 6,
                  border: 'none',
                  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  color: isActive ? '#ffffff' : '#94a3b8',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <Icon size={16} color={isActive ? '#818cf8' : '#94a3b8'} style={{ flexShrink: 0 }} />
                {!isCollapsed && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flex: 1, minWidth: 0 }}>
                    <span style={{ fontSize: 12, fontWeight: isActive ? 700 : 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {tab.label}
                    </span>
                    <span style={{ fontSize: 9.5, padding: '1px 5px', borderRadius: 3, background: isActive ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.05)', color: isActive ? '#c7d2fe' : '#64748b', fontFamily: 'var(--font-mono)' }}>
                      {tab.badge}
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Sidebar Footer Metadata */}
        {!isCollapsed && (
          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border-subtle)', background: 'rgba(10, 12, 18, 0.5)' }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Protocol: Rule 0 Blind
            </div>
            <div style={{ fontSize: 10, color: '#34d399', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              Evidence: Cryp-Signed
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
