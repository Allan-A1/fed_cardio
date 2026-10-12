import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function ConfidenceBar({ confidence = 0.5, prediction = 'Normal' }) {
  const pct = Math.round(confidence * 100);

  let statusLabel = 'High Model Certainty';
  let barColor = 'var(--brand-secondary)';
  let textColor = 'var(--brand-secondary)';
  let pillBg = 'var(--brand-secondary-light)';
  let pillBorder = '#C2E2E7';

  if (pct >= 85) {
    statusLabel = 'High Posterior Certainty';
    barColor = 'var(--brand-secondary)';
    textColor = 'var(--brand-secondary)';
    pillBg = 'var(--brand-secondary-light)';
    pillBorder = '#C2E2E7';
  } else if (pct >= 65) {
    statusLabel = 'Moderate Decision Confidence';
    barColor = 'var(--brand-warning)';
    textColor = 'var(--brand-warning)';
    pillBg = 'var(--brand-warning-bg)';
    pillBorder = 'var(--brand-warning-border)';
  } else {
    statusLabel = 'Borderline Decision Boundary';
    barColor = 'var(--brand-danger)';
    textColor = 'var(--brand-danger)';
    pillBg = 'var(--brand-danger-bg)';
    pillBorder = 'var(--brand-danger-border)';
  }

  return (
    <div
      className="card"
      style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        background: '#FFFFFF',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={16} color="var(--brand-secondary)" />
          <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Posterior Probability Confidence
          </span>
        </div>

        <span
          style={{
            fontSize: '11px',
            fontWeight: '700',
            color: textColor,
            background: pillBg,
            border: `1px solid ${pillBorder}`,
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          {statusLabel}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.02em', lineHeight: 1 }} className="tabular-num">
          {pct}%
        </span>
        <span style={{ fontSize: '12.5px', color: 'var(--text-muted)', fontWeight: '500' }}>
          model posterior score ({confidence.toFixed(3)})
        </span>
      </div>

      {/* Flat Architectural Track */}
      <div
        style={{
          width: '100%',
          height: '8px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
          position: 'relative',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: barColor,
            borderRadius: 'var(--radius-sm)',
            transition: 'width 0.6s ease',
          }}
        />
      </div>

      {/* Reference Markers */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
        <span>0%</span>
        <span>50% Triage Threshold</span>
        <span>100% Certainty</span>
      </div>
    </div>
  );
}
