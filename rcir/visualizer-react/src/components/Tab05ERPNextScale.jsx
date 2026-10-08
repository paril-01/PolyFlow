import React, { useState, useEffect } from 'react';
import { Layers, Database, GitBranch, ArrowRight, CheckCircle2, FileText, Search, Activity, Code2, Server } from 'lucide-react';

export function Tab05ERPNextScale() {
  const [data, setData] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    fetch('/data/erpnext_scale.json')
      .then(r => r.json())
      .then(d => {
        setData(d);
        if (d?.modules_grid?.length > 0) {
          setSelectedModule(d.modules_grid[0]);
        }
        if (d?.preset_rcir_tasks?.length > 0) {
          setSelectedTask(d.preset_rcir_tasks[0]);
        }
      })
      .catch(err => console.warn('Could not load erpnext_scale.json', err));
  }, []);

  if (!data) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
        Loading ERPNext Scale Data...
      </div>
    );
  }

  const { repositories, scale_inventory, coverage_breakdown, modules_grid, preset_rcir_tasks } = data;

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top Header Card */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)', fontFamily: 'var(--font-mono)' }}>
                TAB 05 / ENTERPRISE SCALE
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Frappe ({repositories.frappe.commit.substring(0, 8)}) + ERPNext ({repositories.erpnext.commit.substring(0, 8)})
              </span>
            </div>
            <h1 style={{ fontSize: 20, fontWeight: 800, color: '#ffffff', margin: 0 }}>
              ERPNext Enterprise Scale & Architectural Mapping
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, maxWidth: 880 }}>
              Question: Does this work on a large, complicated enterprise system? RCIR and PolyFlow project ERPNext's 840 DocType schemas and 712k LOC into structured modules with 55.1x bounded context window compression.
            </p>
          </div>
        </div>

        {/* Measured Scale Inventory */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10, marginTop: 18 }}>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>DocType Schemas</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {scale_inventory.doctype_schema_count}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Poly Features</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {scale_inventory.generated_poly_feature_count}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Source Files</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {scale_inventory.total_source_files.toLocaleString()}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Total LOC</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {scale_inventory.total_loc.toLocaleString()}
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Source Token Footprint</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#fbbf24', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {(scale_inventory.source_token_footprint.count / 1000000).toFixed(2)}M
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Context Compression</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {scale_inventory.bounded_context_window_compression.factor}
            </div>
          </div>
        </div>
      </div>

      {/* Distinct Coverage Breakdown Card */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
          Formal Coverage Taxonomy
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Artifact Accounting</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {coverage_breakdown.artifact_accounting_coverage_pct}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
              Every repo file cataloged with hash
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Semantic Mapping</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {coverage_breakdown.semantic_mapping_coverage_pct}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
              DocTypes mapped to .poly specs
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Executable Verticals</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#a78bfa', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {coverage_breakdown.executable_vertical_coverage_pct}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
              Full sandboxed execution
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Behavioral Parity</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#fbbf24', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {coverage_breakdown.behavioral_parity_coverage_pct}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
              Dual-run verification passing
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Unresolved</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {coverage_breakdown.unresolved_count}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3 }}>
              Missing or broken links
            </div>
          </div>
        </div>
      </div>

      {/* Module Grid & Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 16 }}>
        {/* Module Grid (Not a hairball graph!) */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 12 }}>
            ERPNext Subsystem Modules ({modules_grid.length} Modules)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
            {modules_grid.map(mod => {
              const isSelected = selectedModule?.module === mod.module;
              return (
                <div
                  key={mod.module}
                  onClick={() => setSelectedModule(mod)}
                  style={{
                    background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-surface)',
                    border: isSelected ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: 12,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontSize: 12, fontWeight: 700, color: isSelected ? '#ffffff' : '#cbd5e1' }}>
                    {mod.module}
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span>{mod.doctypes} DocTypes</span>
                    <span>{mod.native_files} files</span>
                    <span style={{ color: '#38bdf8' }}>{mod.poly_features} features</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Module Detail Panel */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18, display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 12 }}>
            Module Provenance: {selectedModule?.module}
          </div>
          {selectedModule ? (
            <div style={{ background: 'var(--bg-surface)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)', flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Native Files</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{selectedModule.native_files}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>DocTypes</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{selectedModule.doctypes}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Poly Features</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)' }}>{selectedModule.poly_features}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Unit Tests</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)' }}>{selectedModule.tests}</div>
                </div>
              </div>

              <div style={{ marginTop: 6 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#cbd5e1', marginBottom: 6 }}>Critical Source Files:</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {selectedModule.critical_sources.map(src => (
                    <div key={src} style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', padding: '4px 6px', borderRadius: 4 }}>
                      {src}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>Select a module from the grid</div>
          )}
        </div>
      </div>

      {/* Preset RCIR Tasks on ERPNext */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 10, padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>
            Preset Enterprise RCIR Retrieval Tasks
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {preset_rcir_tasks.map(pt => (
              <button
                key={pt.task_id}
                onClick={() => setSelectedTask(pt)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  background: selectedTask?.task_id === pt.task_id ? '#272f48' : 'var(--bg-surface)',
                  color: selectedTask?.task_id === pt.task_id ? '#ffffff' : '#94a3b8'
                }}
              >
                {pt.scope}: {pt.task_id}
              </button>
            ))}
          </div>
        </div>

        {selectedTask && (
          <div style={{ background: 'var(--bg-surface)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: 11, color: '#818cf8', fontWeight: 600, textTransform: 'uppercase' }}>Scope: {selectedTask.scope}</span>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginTop: 2 }}>{selectedTask.title}</div>
              </div>
              <div style={{ display: 'flex', gap: 14 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Recall</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#10b981', fontFamily: 'var(--font-mono)' }}>{selectedTask.recall_pct}%</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>MRR</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{selectedTask.mrr}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Context Tokens</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)' }}>{selectedTask.context_tokens}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Latency</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>{selectedTask.query_latency_ms} ms</div>
                </div>
              </div>
            </div>
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border-subtle)', fontSize: 11, color: 'var(--text-muted)' }}>
              Target Symbol: <span style={{ color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>{selectedTask.target_symbol}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
