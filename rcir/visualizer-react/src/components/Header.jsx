import React from 'react';
import { Network, Search, RefreshCw, ShieldCheck, Compass, GitBranch, Menu, PanelLeft } from 'lucide-react';

export function Header({
  manifest = [],
  currentDatasetId,
  onSelectDataset,
  layoutMode,
  onToggleLayout,
  searchQuery,
  onSearchChange,
  onResetCamera,
  onOpenProofModal,
  onToggleMobileSidebar,
  isSidebarCollapsed = false,
  onToggleSidebarCollapse
}) {
  return (
    <header className="top-header">
      {/* Brand & Dataset Select */}
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

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div style={{
            width: 28,
            height: 28,
            borderRadius: 6,
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Network size={15} color="#fff" />
          </div>
          <div className="header-brand-title" style={{ display: 'flex', alignItems: 'baseline', gap: 5 }}>
            <span style={{ fontWeight: 800, fontSize: 13.5, color: '#ffffff', letterSpacing: '-0.01em' }}>RCIR</span>
            <span style={{ fontSize: 9, padding: '1px 4px', background: '#252a3f', color: '#a5b4fc', borderRadius: 4, border: '1px solid #3d4668', fontWeight: 600 }}>v3.4</span>
          </div>
        </div>

        <select
          value={currentDatasetId}
          onChange={(e) => onSelectDataset(e.target.value)}
          className="header-dataset-select"
          style={{
            background: '#161928',
            border: '1px solid #333c56',
            color: '#ffffff',
            padding: '5px 10px',
            borderRadius: 6,
            fontSize: 12,
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none',
            maxWidth: 260
          }}
        >
          <optgroup label="Enterprise Core Target (Validated Subject)">
            <option value="nextcloud">☁️ Nextcloud Server Core (50k nodes · 143k edges)</option>
          </optgroup>
          <optgroup label="Microservice Reference Benchmarks">
            <option value="otel_recommendation">🔭 OTel Astronomy Shop — Recommendation (101 nodes)</option>
            <option value="otel_agent">🤖 OTel Astronomy Shop — Agent Service (28 nodes)</option>
          </optgroup>
          <optgroup label="Standard Repositories">
            <option value="requests">📦 PSF / Requests (320 nodes)</option>
            <option value="flask">🌶️ Pallets / Flask (442 nodes)</option>
            <option value="polyflow">⚡ PolyFlow Core (110 nodes)</option>
          </optgroup>
        </select>
      </div>

      {/* Center Search Bar */}
      <div className="header-search-bar" style={{ display: 'flex', alignItems: 'center', position: 'relative', width: 240 }}>
        <Search size={14} style={{ position: 'absolute', left: 9, color: '#94a3b8' }} />
        <input
          type="text"
          className="input-text header-search-input"
          placeholder="Filter nodes (e.g. Service)..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{ width: '100%', paddingLeft: 30, paddingRight: 24, height: 30, fontSize: 12 }}
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            style={{ position: 'absolute', right: 6, background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: 12 }}
          >
            ×
          </button>
        )}
      </div>

      {/* Right Action Controls */}
      <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* Layout Switcher */}
        <div style={{ display: 'flex', background: '#161928', borderRadius: 6, border: '1px solid #2d354e', padding: 2 }}>
          <button
            onClick={() => onToggleLayout('3d')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 11,
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              background: layoutMode === '3d' ? '#272f48' : 'transparent',
              color: layoutMode === '3d' ? '#38bdf8' : '#94a3b8'
            }}
            title="3D WebGL Galaxy Orbit (Hardware Accelerated)"
          >
            <span>3D Space</span>
          </button>
          <button
            onClick={() => onToggleLayout('flow')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 11,
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              background: layoutMode === 'flow' ? '#272f48' : 'transparent',
              color: layoutMode === 'flow' ? '#ffffff' : '#94a3b8'
            }}
            title="Hierarchical Architecture Flow DAG"
          >
            <span>2D Flow</span>
          </button>
          <button
            onClick={() => onToggleLayout('force')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 11,
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
              background: layoutMode === 'force' ? '#272f48' : 'transparent',
              color: layoutMode === 'force' ? '#ffffff' : '#94a3b8'
            }}
            title="Force Clusters"
          >
            <span>Force</span>
          </button>
        </div>

        {/* Reset View */}
        <button className="btn-icon" onClick={onResetCamera} title="Reset Camera">
          <RefreshCw size={13} />
        </button>

        {/* CLI Proof Button */}
        <button
          onClick={onOpenProofModal}
          className="btn btn-secondary"
          style={{ height: 30, padding: '0 10px', fontSize: 11.5 }}
          title="Verify Real AST CLI Extraction"
        >
          <ShieldCheck size={13} color="#10b981" />
          <span>Proof</span>
        </button>
      </div>
    </header>
  );
}
