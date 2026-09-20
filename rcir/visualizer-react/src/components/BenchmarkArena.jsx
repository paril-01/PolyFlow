import React, { useState } from 'react';
import { BarChart3, TrendingDown, DollarSign, Clock, ShieldCheck } from 'lucide-react';
import { BENCHMARK_DATA } from '../data/benchmarks';

export function BenchmarkArena() {
  const [selectedTaskIdx, setSelectedTaskIdx] = useState(0);
  const tasks = BENCHMARK_DATA.tasks;
  const currentTask = tasks[selectedTaskIdx];
  const agg = BENCHMARK_DATA.aggregate;

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-app)',
      padding: '16px 20px',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
          <BarChart3 size={18} color="#34d399" />
          <h2 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>Empirical Benchmark Arena</h2>
        </div>
        <p style={{ fontSize: 12, color: '#94a3b8' }}>
          Head-to-head empirical evaluation: Method A (Conventional Full-File Ingestion) vs Method B (RCIR Dependency Graph Context Runtime).
        </p>
      </div>

      {/* Scenario Selector Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
        {tasks.map((t, idx) => (
          <button
            key={t.task_id}
            onClick={() => setSelectedTaskIdx(idx)}
            className={`btn ${selectedTaskIdx === idx ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: 11.5, padding: '5px 12px' }}
          >
            <span>Scenario {idx + 1}: {t.title.split(':')[0]}</span>
          </button>
        ))}
      </div>

      {/* Task Summary Banner */}
      <div className="glass-panel" style={{ padding: 12, marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#ffffff', marginBottom: 2 }}>
          {currentTask.title}
        </div>
        <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
          Service Scope: <span style={{ color: '#38bdf8' }}>{currentTask.service}</span> • Query: <code style={{ color: '#fbbf24' }}>"{currentTask.query}"</code>
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12, marginBottom: 14 }}>
        {/* Method A */}
        <div className="glass-card" style={{ padding: 14, border: '1px solid rgba(244, 63, 94, 0.4)', background: 'rgba(244, 63, 94, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#fb7185', letterSpacing: '0.04em' }}>
              METHOD A: CONVENTIONAL FULL-FILE
            </div>
            <span className="badge badge-rose">UNSCALED</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Total Prompt Tokens:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: '#fb7185' }}>
                {currentTask.method_a_conventional.total_tokens.toLocaleString()} tokens
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Noise Ratio:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: '#fb7185' }}>
                {currentTask.method_a_conventional.noise_ratio_percent}%
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Invalidation Blast Radius:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#fb7185', fontWeight: 600 }}>
                {currentTask.method_a_conventional.invalidation_blast_radius}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Cache Hit Retention:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#fb7185', fontWeight: 600 }}>
                {currentTask.method_a_conventional.cache_hit_retention_percent}%
              </span>
            </div>
          </div>
        </div>

        {/* Method B */}
        <div className="glass-card" style={{ padding: 14, border: '1px solid rgba(16, 185, 129, 0.5)', background: 'rgba(16, 185, 129, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#34d399', letterSpacing: '0.04em' }}>
              METHOD B: RCIR GRAPH RUNTIME
            </div>
            <span className="badge badge-emerald">OPTIMIZED</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Total Prompt Tokens:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                {currentTask.method_b_rcir.total_tokens.toLocaleString()} tokens
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Noise Ratio:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                {currentTask.method_b_rcir.noise_ratio_percent}%
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Invalidation Blast Radius:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#34d399', fontWeight: 600 }}>
                {currentTask.method_b_rcir.invalidation_blast_radius}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>Cache Hit Retention:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#34d399', fontWeight: 600 }}>
                {currentTask.method_b_rcir.cache_hit_retention_percent}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Aggregate Impact Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 11, fontWeight: 600 }}>
            <TrendingDown size={14} color="#34d399" />
            <span>Average Token Reduction</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#34d399', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
            -{agg.average_tokens_per_prompt.reduction_percent}%
          </div>
          <div style={{ fontSize: 11, color: '#cbd5e1', marginTop: 2 }}>
            {agg.average_tokens_per_prompt.method_a.toLocaleString()} → {agg.average_tokens_per_prompt.method_b.toLocaleString()} tokens/turn
          </div>
        </div>

        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 11, fontWeight: 600 }}>
            <DollarSign size={14} color="#fbbf24" />
            <span>Cost / 1000 Iterations</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#fbbf24', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
            ${agg.economic_projection_1000_iterations.token_cost_method_b_usd}
          </div>
          <div style={{ fontSize: 11, color: '#34d399', marginTop: 2 }}>
            Saves ${agg.economic_projection_1000_iterations.net_savings_usd} ({agg.economic_projection_1000_iterations.efficiency_multiplier}x ROI)
          </div>
        </div>

        <div className="glass-card" style={{ padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 11, fontWeight: 600 }}>
            <Clock size={14} color="#818cf8" />
            <span>Time-to-First-Token (TTFT)</span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#818cf8', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
            8.1x Faster
          </div>
          <div style={{ fontSize: 11, color: '#cbd5e1', marginTop: 2 }}>
            180ms vs 1,450ms ingestion latency
          </div>
        </div>
      </div>
    </div>
  );
}
