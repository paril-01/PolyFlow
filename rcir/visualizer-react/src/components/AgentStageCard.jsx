import React from 'react';
import { CheckCircle2, Clock, Loader2, UserCheck, Code, ShieldCheck, Sparkles, Database } from 'lucide-react';

export function AgentStageCard({ stage, isSelected, onSelect }) {
  const getIcon = () => {
    switch (stage.id) {
      case 'maker': return <Sparkles size={16} color={stage.color} />;
      case 'reviewer_plan': return <UserCheck size={16} color={stage.color} />;
      case 'implementer': return <Code size={16} color={stage.color} />;
      case 'gatekeeper': return <ShieldCheck size={16} color={stage.color} />;
      case 'historian': return <Database size={16} color={stage.color} />;
      default: return <Sparkles size={16} color={stage.color} />;
    }
  };

  const getStatusBadge = () => {
    switch (stage.status) {
      case 'completed':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#34d399', fontSize: 11, fontWeight: 700 }}>
            <CheckCircle2 size={13} />
            <span>Done</span>
          </span>
        );
      case 'running':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#818cf8', fontSize: 11, fontWeight: 700 }}>
            <Loader2 size={13} className="spin-slow" />
            <span>Active</span>
          </span>
        );
      case 'pending':
        return (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#94a3b8', fontSize: 11 }}>
            <Clock size={13} />
            <span>Queued</span>
          </span>
        );
      default:
        return (
          <span style={{ color: '#94a3b8', fontSize: 11 }}>
            Ready
          </span>
        );
    }
  };

  return (
    <div
      onClick={onSelect}
      className="glass-card"
      style={{
        padding: '12px 14px',
        cursor: 'pointer',
        border: isSelected ? `1px solid ${stage.color}` : '1px solid var(--border-default)',
        background: isSelected ? '#1e2438' : 'var(--bg-card)',
        boxShadow: isSelected ? `0 0 14px ${stage.color}40` : 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        transition: 'all 0.15s ease'
      }}
    >
      {/* Top Row: Icon + Role + Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 26,
            height: 26,
            borderRadius: 6,
            background: '#1a1f30',
            border: `1px solid ${stage.color}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {getIcon()}
          </div>
          <div>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: '#ffffff' }}>{stage.role}</div>
            <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase' }}>{stage.badge}</div>
          </div>
        </div>
        {getStatusBadge()}
      </div>

      {/* Description */}
      <div style={{ fontSize: 11, color: '#cbd5e1', lineHeight: 1.35 }}>
        {stage.description}
      </div>

      {/* Timing footer */}
      {stage.status === 'completed' && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.5, color: '#94a3b8', paddingTop: 4, borderTop: '1px solid #232a3e', fontFamily: 'var(--font-mono)' }}>
          <span>{stage.durationMs}ms</span>
          <span>~{stage.tokensUsed} tokens</span>
        </div>
      )}
    </div>
  );
}
