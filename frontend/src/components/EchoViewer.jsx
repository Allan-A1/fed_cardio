import React, { useState, useEffect } from 'react';
import { Activity, Play, Pause, Layers } from 'lucide-react';

export default function EchoViewer({ edFrameUrl, esFrameUrl, efValue = 54.0, prediction = 'Normal' }) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [activeFrame, setActiveFrame] = useState('ED');

  const isReduced = efValue !== null && efValue !== undefined && efValue < 55.0;

  // Toggle animation interval between ED and ES frames
  useEffect(() => {
    let interval = null;
    if (isAnimating) {
      interval = setInterval(() => {
        setActiveFrame((prev) => (prev === 'ED' ? 'ES' : 'ED'));
      }, 350); // ~85 bpm cardiac cycle approximation
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAnimating]);

  return (
    <div
      className="card"
      style={{
        padding: 'var(--sp-6)',
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
            Echocardiogram Apical 4-Chamber (A4C) View
          </h4>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Biplane Volume Frame Extraction (EchoNet-Pediatric Pipeline)
          </span>
        </div>

        <button
          className={`btn btn-sm ${isAnimating ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setIsAnimating(!isAnimating)}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          {isAnimating ? <Pause size={14} /> : <Play size={14} />}
          {isAnimating ? 'Stop Animation' : 'Cine Loop Preview'}
        </button>
      </div>

      {/* Frame Comparison Panels */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px',
          marginBottom: '18px',
        }}
      >
        {/* ED Frame */}
        <div
          style={{
            background: 'hsl(210, 25%, 97%)',
            borderRadius: 'var(--radius-md)',
            border: `2px solid ${activeFrame === 'ED' && isAnimating ? 'var(--brand-primary)' : 'var(--border-subtle)'}`,
            padding: '12px',
            textAlign: 'center',
            transition: 'border-color var(--transition-fast)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)' }}>
              End-Diastole (ED)
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Max LV Relaxation</span>
          </div>

          <div
            style={{
              width: '100%',
              height: '200px',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              background: '#0a0d14',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            {edFrameUrl ? (
              <img
                src={edFrameUrl}
                alt="End-Diastolic Frame"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px', textAlign: 'center' }}>
                <Layers size={28} style={{ margin: '0 auto 6px' }} />
                <span>ED Frame (112×112)</span>
              </div>
            )}
            <div
              style={{
                position: 'absolute',
                bottom: '6px',
                right: '8px',
                background: 'rgba(0,0,0,0.65)',
                color: '#fff',
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              Frame 0
            </div>
          </div>
        </div>

        {/* ES Frame */}
        <div
          style={{
            background: 'hsl(210, 25%, 97%)',
            borderRadius: 'var(--radius-md)',
            border: `2px solid ${activeFrame === 'ES' && isAnimating ? 'var(--brand-primary)' : 'var(--border-subtle)'}`,
            padding: '12px',
            textAlign: 'center',
            transition: 'border-color var(--transition-fast)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)' }}>
              End-Systole (ES)
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Peak LV Contraction</span>
          </div>

          <div
            style={{
              width: '100%',
              height: '200px',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              background: '#0a0d14',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            {esFrameUrl ? (
              <img
                src={esFrameUrl}
                alt="End-Systolic Frame"
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : (
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px', textAlign: 'center' }}>
                <Layers size={28} style={{ margin: '0 auto 6px' }} />
                <span>ES Frame (112×112)</span>
              </div>
            )}
            <div
              style={{
                position: 'absolute',
                bottom: '6px',
                right: '8px',
                background: 'rgba(0,0,0,0.65)',
                color: '#fff',
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              Frame Mid
            </div>
          </div>
        </div>
      </div>

      {/* EF Metrics Strip */}
      <div
        style={{
          padding: '16px',
          background: isReduced ? 'hsla(0, 84%, 60%, 0.08)' : 'hsla(142, 70%, 42%, 0.08)',
          border: `1px solid ${isReduced ? 'hsla(0, 84%, 60%, 0.3)' : 'hsla(142, 70%, 42%, 0.3)'}`,
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: 'var(--radius-md)',
              background: isReduced ? 'var(--brand-danger)' : 'var(--brand-success)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <Activity size={24} />
          </div>

          <div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)' }}>
              Left Ventricular Ejection Fraction (LVEF)
            </div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: isReduced ? 'var(--brand-danger)' : 'var(--brand-success)' }}>
              {efValue !== null && efValue !== undefined ? `${efValue.toFixed(1)}%` : '—'}
            </div>
          </div>
        </div>

        {/* Clinical Reference Range */}
        <div style={{ textAlign: 'right' }}>
          <span
            style={{
              fontSize: '12px',
              fontWeight: '700',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: isReduced ? 'hsla(0, 84%, 60%, 0.2)' : 'hsla(142, 70%, 42%, 0.2)',
              color: isReduced ? 'hsl(0, 80%, 40%)' : 'hsl(142, 75%, 28%)',
            }}
          >
            {isReduced ? '⚠️ Reduced Systolic Function (<55%)' : '✅ Preserved Normal Function (≥55%)'}
          </span>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            ASE Pediatric Standard: Normal ≥ 55% | Borderline 50–54% | Depressed &lt; 50%
          </div>
        </div>
      </div>
    </div>
  );
}
