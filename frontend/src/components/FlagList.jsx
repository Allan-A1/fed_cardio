import React from 'react';
import { AlertOctagon, AlertTriangle, Info, CheckCircle } from 'lucide-react';

export default function FlagList({ flags = [] }) {
  if (!flags || flags.length === 0) {
    return (
      <div
        className="card"
        style={{
          padding: 'var(--sp-5)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'hsla(142, 70%, 97%, 0.6)',
          borderColor: 'hsla(142, 70%, 42%, 0.25)',
        }}
      >
        <CheckCircle size={20} color="var(--brand-success)" />
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: '500' }}>
          No quality, artifact, or demographic risk warnings triggered for this recording.
        </span>
      </div>
    );
  }

  const getStyle = (level) => {
    switch ((level || '').toLowerCase()) {
      case 'danger':
        return {
          bg: 'hsla(0, 84%, 60%, 0.06)',
          border: 'hsla(0, 84%, 60%, 0.3)',
          color: 'hsl(0, 75%, 45%)',
          badgeBg: 'hsla(0, 84%, 60%, 0.15)',
          icon: AlertOctagon,
          badgeText: 'High Clinical Priority',
        };
      case 'warning':
        return {
          bg: 'hsla(35, 95%, 52%, 0.07)',
          border: 'hsla(35, 95%, 52%, 0.35)',
          color: 'hsl(35, 95%, 38%)',
          badgeBg: 'hsla(35, 95%, 52%, 0.18)',
          icon: AlertTriangle,
          badgeText: 'Attention Needed',
        };
      case 'info':
      default:
        return {
          bg: 'hsla(221, 100%, 55%, 0.05)',
          border: 'hsla(221, 100%, 55%, 0.22)',
          color: 'hsl(221, 100%, 45%)',
          badgeBg: 'hsla(221, 100%, 55%, 0.12)',
          icon: Info,
          badgeText: 'Clinical Note',
        };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {flags.map((flag, idx) => {
        const style = getStyle(flag.level);
        const IconComponent = style.icon;

        return (
          <div
            key={idx}
            style={{
              padding: '14px 16px',
              borderRadius: 'var(--radius-md)',
              background: style.bg,
              border: `1px solid ${style.border}`,
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              transition: 'transform var(--transition-fast)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: style.badgeBg,
                color: style.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '1px',
              }}
            >
              <IconComponent size={18} strokeWidth={2.2} />
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '3px' }}>
                <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)' }}>
                  {flag.title || 'Signal Notice'}
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: '700',
                    color: style.color,
                    background: style.badgeBg,
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  {style.badgeText}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: 0 }}>
                {flag.message}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
