import React from 'react';
import { Network, Search, RefreshCw, ShieldCheck, Compass, GitBranch } from 'lucide-react';

export function Header({
  manifest = [],
  currentDatasetId,
  onSelectDataset,
  layoutMode,
  onToggleLayout,
  searchQuery,
  onSearchChange,
  onResetCamera,
  onOpenProofModal
}) {
  return (
    <header className="top-header">
      {/* Brand & Dataset Select */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 30,
            height: 30,
            borderRadius: 6,
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Network size={16} color="#fff" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontWeight: 800, fontSize: 14, color: '#ffffff', letterSpacing: '-0.01em' }}>RCIR</span>
            <span style={{ fontSize: 9.5, padding: '1px 5px', background: '#252a3f', color: '#a5b4fc', borderRadius: 4, border: '1px solid #3d4668', fontWeight: 600 }}>v3.4</span>
          </div>
        </div>

        {/* Dataset Dropdown */}
        <select
          value={currentDatasetId}
          onChange={(e) => onSelectDataset(e.target.value)}
          style={{
            background: '#161928',
            border: '1px solid #333c56',
            color: '#ffffff',
            padding: '5px 12px',
            borderRadius: 6,
            fontSize: 12,
            fontWeight: 500,
            cursor: 'pointer',
            outline: 'none'
          }}
        >
          <optgroup label="Microservice Reference (Recommended)">
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
      <div style={{ display: 'flex', alignItems: 'center', position: 'relative', width: 280 }}>
        <Search size={14} style={{ position: 'absolute', left: 9, color: '#94a3b8' }} />
        <input
          type="text"
          className="input-text"
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* Layout Switcher */}
        <div style={{ display: 'flex', background: '#161928', borderRadius: 6, border: '1px solid #2d354e', padding: 2 }}>
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
            <span>Flow</span>
          </button>
          <button
            onClick={() => onToggleLayout('radial')}
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
              background: layoutMode === 'radial' ? '#272f48' : 'transparent',
              color: layoutMode === 'radial' ? '#ffffff' : '#94a3b8'
            }}
            title="Concentric Stagnant Radial Tree"
          >
            <span>Radial</span>
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
