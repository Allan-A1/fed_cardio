import React from 'react';
import { AlertCircle, CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function ResultBadge({ prediction, modality = 'PCG', efValue, confidence, size = 'large' }) {
  const isAbnormal = (prediction || '').toLowerCase() === 'abnormal';

  // Subtitle generation based on modality and findings
  let subtitle = '';
  if (modality === 'PCG') {
    subtitle = isAbnormal ? 'Pathological Murmur Detected (Turbulent Systolic Energy)' : 'Physiological S1/S2 Acoustic Baseline';
  } else if (modality === 'Echo') {
    if (efValue !== undefined && efValue !== null) {
      subtitle = isAbnormal
        ? `Reduced Left Ventricular Ejection Fraction (${efValue.toFixed(1)}% < 55% Threshold)`
        : `Preserved Left Ventricular Contractility (${efValue.toFixed(1)}% ≥ 55% Normal Baseline)`;
    } else {
      subtitle = isAbnormal ? 'Reduced LV Systolic Function' : 'Normal Ventricular Kinetic Function';
    }
  } else {
    subtitle = isAbnormal ? 'Clinical Anomaly Flagged for Pediatric Triage' : 'Normal Multi-Modal Cardiac Pattern';
  }

  const isLarge = size === 'large';

  return (
    <div
      className={`result-badge-card ${isAbnormal ? 'result-abnormal' : 'result-normal'}`}
      style={{
        padding: isLarge ? '18px 22px' : '12px 16px',
        borderRadius: 'var(--radius-md)',
        border: `1px solid ${isAbnormal ? 'var(--brand-danger-border)' : 'var(--brand-success-border)'}`,
        background: isAbnormal ? 'var(--brand-danger-bg)' : 'var(--brand-success-bg)',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: isLarge ? '16px' : '12px' }}>
        <div
          style={{
            width: isLarge ? '48px' : '36px',
            height: isLarge ? '48px' : '36px',
            borderRadius: 'var(--radius-sm)',
            background: isAbnormal ? 'var(--brand-danger)' : 'var(--brand-success)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            flexShrink: 0,
          }}
        >
          {isAbnormal ? (
            <AlertCircle size={isLarge ? 24 : 18} strokeWidth={2.2} />
          ) : (
            <CheckCircle2 size={isLarge ? 24 : 18} strokeWidth={2.2} />
          )}
        </div>

        <div>
          <div
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: isLarge ? '22px' : '17px',
              fontWeight: '700',
              letterSpacing: '0.02em',
              color: isAbnormal ? 'var(--brand-danger)' : 'var(--brand-success)',
              lineHeight: 1.15,
            }}
          >
            {isAbnormal ? 'PATHOLOGY FLAGGED' : 'NORMAL / PHYSIOLOGICAL'}
          </div>
          <div
            style={{
              fontSize: isLarge ? '13px' : '11.5px',
              fontWeight: '500',
              color: 'var(--text-secondary)',
              marginTop: '4px',
              lineHeight: 1.4,
            }}
          >
            {subtitle}
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '11px',
          fontWeight: '700',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          color: isAbnormal ? 'var(--brand-danger)' : 'var(--brand-success)',
          background: '#FFFFFF',
          border: `1px solid ${isAbnormal ? 'var(--brand-danger-border)' : 'var(--brand-success-border)'}`,
          padding: '4px 10px',
          borderRadius: 'var(--radius-sm)',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: isAbnormal ? 'var(--brand-danger)' : 'var(--brand-success)',
          }}
        />
        {isAbnormal ? 'Requires Specialist Triage' : 'Routine Baseline'}
      </div>
    </div>
  );
}
