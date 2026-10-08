import React, { useState, useEffect } from 'react';
import { Layers, ShieldCheck, Menu, PanelLeft, CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

export function Header({
  currentDatasetId,
  onSelectDataset,
  onToggleMobileSidebar,
  isSidebarCollapsed = false,
  onToggleSidebarCollapse,
  onOpenProofModal
}) {
  const [status, setStatus] = useState({
    evidence_state: 'VALIDATED',
    evidence_run_id: 'final_blind_validation',
    active_repository: 'nextcloud-server'
  });

  useEffect(() => {
    fetch('/data/system_status.json')
      .then(r => r.json())
      .then(d => {
        if (d) setStatus(d);
      })
      .catch(err => console.warn('Could not load system_status.json', err));
  }, []);

  const getBadgeStyle = (state) => {
    switch (state) {
      case 'VALIDATED':
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: '1px solid rgba(16, 185, 129, 0.35)' };
      case 'PARTIAL':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.35)' };
      case 'INVALID':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: '1px solid rgba(239, 68, 68, 0.35)' };
      default: // DEVELOPMENT
        return { bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.35)' };
    }
  };

  const badgeStyle = getBadgeStyle(status.evidence_state);

  return (
    <header className="top-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 16px', height: 48, background: 'var(--bg-header)', borderBottom: '1px solid var(--border-default)' }}>
      {/* Brand & Repo Selector */}
      <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
        {/* Mobile Hamburger Menu Toggle */}
        <button
          className="mobile-menu-btn"
          onClick={onToggleMobileSidebar}
          aria-label="Open Navigation Menu"
        >
          <Menu size={18} />
        </button>

        {/* Desktop Sidebar Collapse Toggle */}
        <button
          className="header-sidebar-toggle"
          onClick={onToggleSidebarCollapse}
          title={isSidebarCollapsed ? "Expand sidebar (Ctrl+B)" : "Collapse sidebar (Ctrl+B)"}
          aria-label="Toggle Sidebar"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 28,
            height: 28,
            borderRadius: 6,
            background: isSidebarCollapsed ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
            border: isSidebarCollapsed ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
            color: isSidebarCollapsed ? '#818cf8' : '#cbd5e1',
            cursor: 'pointer',
            flexShrink: 0
          }}
        >
          <PanelLeft size={15} />
        </button>

        {/* Brand Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div style={{
            width: 26,
            height: 26,
            borderRadius: 5,
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Layers size={14} color="#fff" />
          </div>
          <div className="header-brand-title" style={{ display: 'flex', alignItems: 'baseline', gap: 5 }}>
            <span style={{ fontWeight: 800, fontSize: 13.5, color: '#ffffff', letterSpacing: '-0.01em' }}>PolyFlow</span>
            <span style={{ fontSize: 9.5, padding: '1px 5px', background: '#20263d', color: '#a5b4fc', borderRadius: 3, border: '1px solid #323b5c', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              RCIR v3.4
            </span>
          </div>
        </div>

        {/* Repository Selector */}
        <select
          value={currentDatasetId}
          onChange={(e) => onSelectDataset(e.target.value)}
          className="header-dataset-select"
          style={{
            background: '#161928',
            border: '1px solid #333c56',
            color: '#ffffff',
            padding: '4px 10px',
            borderRadius: 6,
            fontSize: 11.5,
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none',
            maxWidth: 280
          }}
        >
          <option value="nextcloud">Nextcloud Server Core (PHP / TS / Vue Monolith)</option>
          <option value="erpnext">Frappe / ERPNext (Python / JS Enterprise)</option>
          <option value="polyflow">PolyFlow Core (Isolated Runtime Sandboxes)</option>
        </select>
      </div>

      {/* Center Evidence Lineage & Run ID */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Evidence Run:</span>
          <span style={{ color: '#ffffff', fontWeight: 600 }}>{status.evidence_run_id}</span>
        </div>

        {/* Evidence State Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          padding: '2px 8px',
          borderRadius: 4,
          fontSize: 10.5,
          fontWeight: 700,
          fontFamily: 'var(--font-mono)',
          background: badgeStyle.bg,
          color: badgeStyle.text,
          border: badgeStyle.border
        }}>
          {status.evidence_state === 'VALIDATED' && <CheckCircle2 size={11} />}
          {status.evidence_state === 'PARTIAL' && <AlertTriangle size={11} />}
          {status.evidence_state === 'INVALID' && <XCircle size={11} />}
          {status.evidence_state === 'DEVELOPMENT' && <Info size={11} />}
          <span>{status.evidence_state}</span>
        </div>
      </div>

      {/* Right Action: Audit Proof Modal */}
      <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button
          onClick={onOpenProofModal}
          className="btn btn-secondary"
          style={{ height: 28, padding: '0 10px', fontSize: 11, display: 'flex', alignItems: 'center', gap: 5 }}
          title="Inspect SHA-256 Hashes and Cryptographic Receipts"
        >
          <ShieldCheck size={13} color="#10b981" />
          <span>Proof & Audit</span>
        </button>
      </div>
    </header>
  );
}
