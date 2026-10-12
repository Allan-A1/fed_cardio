import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function StatCard({ icon: Icon, iconColor, iconBg, value, label, delta, deltaLabel, id }) {
  const isPositive = delta >= 0;
  return (
    <div className="card stat-card" id={id}>
      <div className="stat-card-icon" style={{ background: iconBg || 'var(--bg-elevated)' }}>
        <Icon size={20} color={iconColor || 'var(--brand-primary)'} />
      </div>
      <div className="stat-card-value tabular-num" style={{ color: iconColor || 'var(--text-primary)' }}>{value}</div>
      <div className="stat-card-label">{label}</div>
      {delta !== undefined && (
        <div className={`stat-card-delta ${isPositive ? 'delta-up' : 'delta-down'}`}>
          {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {isPositive ? '+' : ''}{delta} {deltaLabel}
        </div>
      )}
    </div>
  );
}

export function Badge({ type = 'idle', label }) {
  const map = {
    active: { cls: 'badge-active', text: label || 'Active' },
    training: { cls: 'badge-training', text: label || 'Training' },
    idle: { cls: 'badge-idle', text: label || 'Idle' },
    warning: { cls: 'badge-warning', text: label || 'Warning' },
  };
  const { cls, text } = map[type] || map.idle;
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {text}
    </span>
  );
}

export function ProgressBar({ value, max = 100, color }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div>
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${pct}%`, background: color || 'var(--brand-secondary)' }}
        />
      </div>
    </div>
  );
}

export function SectionTitle({ children, icon: Icon }) {
  return (
    <div className="section-title">
      {Icon && <Icon size={15} color="var(--brand-secondary)" />}
      <span>{children}</span>
    </div>
  );
}

export function Modal({ open, onClose, title, children, id }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="card modal-card" id={id} style={{ background: '#FFFFFF', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)' }}>
        <div className="modal-header" style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px', marginBottom: '18px' }}>
          <h2 className="modal-title" style={{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontWeight: 600, color: 'var(--brand-primary)' }}>{title}</h2>
          <button className="btn btn-ghost btn-icon" onClick={onClose} style={{ padding: '4px 8px' }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function LogTerminal({ logs }) {
  const typeClass = { info: 'log-msg-info', success: 'log-msg-success', warning: 'log-msg-warning', error: 'log-msg-error' };
  return (
    <div className="log-terminal" id="log-terminal">
      {logs.map((l, i) => (
        <div key={i} className="log-line">
          <span className="log-time">[{l.time}]</span>
          <span className={typeClass[l.type] || 'log-msg-info'}>{l.msg}</span>
        </div>
      ))}
    </div>
  );
}
