import React, { useState } from 'react';
import { useLocation, NavLink } from 'react-router-dom';
import { Bell, X, Shield, Building2, Stethoscope, Globe, CheckCircle2 } from 'lucide-react';
import { useApp } from '../context/AppContext';

const PAGE_META = {
  // Public Institute
  '/institute': { title: 'St. Jude & St. Luke Pediatric Heart Institute', subtitle: 'Public academic institute overview, clinical divisions & faculty' },

  // Admin routes
  '/admin/hospitals': { title: 'Consortium Hospital Registry', subtitle: 'Authorized medical centers, node tokens & regional clearances' },
  '/admin/clusters': { title: 'Cluster Topology Overseer', subtitle: 'Global model convergence & participant node health' },

  // Hospital routes
  '/hospital/dashboard': { title: 'Node Operational Dashboard', subtitle: 'Local model metrics, cluster membership & telemetry' },
  '/hospital/clusters': { title: 'Federated Cluster Management', subtitle: 'Join multi-center clusters & configure privacy thresholds' },
  '/hospital/data': { title: 'Local Dataset Configuration', subtitle: 'Cohort demographics, phonocardiograms & echo telemetry' },
  '/hospital/training': { title: 'Federated Model Optimization', subtitle: 'Local epoch execution & gradient aggregation cycles' },
  '/hospital/settings': { title: 'Hospital Node Settings', subtitle: 'Node credentials, network endpoints & HIPAA parameters' },

  // Technician routes
  '/technician/screening': { title: 'Pediatric Cardiac Screening', subtitle: 'Multi-modal PCG phonocardiography & echocardiogram analysis' },
  '/technician/history': { title: 'Screening Audit Log & History', subtitle: 'Temporal triage records, physician confirmations & referrals' },

  // Fallbacks
  '/dashboard': { title: 'Node Operational Dashboard', subtitle: 'Local model metrics, cluster membership & telemetry' },
  '/clusters': { title: 'Cluster Management', subtitle: 'Join multi-center clusters' },
  '/data': { title: 'Data Configuration', subtitle: 'Local patient dataset' },
  '/training': { title: 'Training Status', subtitle: 'Model execution' },
  '/settings': { title: 'Settings', subtitle: 'Node preferences' },
  '/screening': { title: 'Clinical Screening', subtitle: 'Auscultation & Echo' },
};

const TYPE_COLOR = {
  success: 'var(--brand-success)',
  info: 'var(--brand-secondary)',
  warning: 'var(--brand-warning)',
  error: 'var(--brand-danger)',
};

export default function Topbar() {
  const { pathname } = useLocation();
  const { currentUser, hospital, notifications } = useApp();
  const [showNotifs, setShowNotifs] = useState(false);

  // Match report details path or meta
  let meta = PAGE_META[pathname];
  if (!meta) {
    if (pathname.includes('/report/')) {
      meta = { title: 'Diagnostic Screening Report', subtitle: 'Acoustic murmur grading, Grad-CAM attention heatmap & referral notes' };
    } else {
      meta = { title: 'FedMed Network', subtitle: 'Pediatric Congenital Heart Screening System' };
    }
  }

  const role = currentUser?.role || 'hospital';

  return (
    <header className="topbar" id="topbar">
      <div className="topbar-left">
        <span className="topbar-title">{meta.title}</span>
        <span className="topbar-subtitle">{meta.subtitle}</span>
      </div>

      <div className="topbar-right">
        {/* Hospital Public Website Shortcut */}
        <NavLink
          to="/institute"
          className="btn btn-secondary btn-sm"
          style={{ fontSize: 12, padding: '5px 10px', gap: 6 }}
          title="View Public Hospital Website"
        >
          <Globe size={13} />
          <span>Hospital Website</span>
        </NavLink>

        {/* Role Clearance Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 9px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            fontSize: 11.5,
            fontWeight: 600,
            color: 'var(--text-secondary)',
          }}
        >
          {role === 'admin' ? (
            <Shield size={13} color="var(--brand-primary)" />
          ) : role === 'technician' ? (
            <Stethoscope size={13} color="var(--brand-secondary)" />
          ) : (
            <Building2 size={13} color="var(--brand-primary)" />
          )}
          <span>
            {role === 'admin' && 'Central Overseer'}
            {role === 'technician' && `Triage: ${currentUser?.name?.split(' ')[0] || 'Clinician'}`}
            {role === 'hospital' && (hospital.id || 'Hospital Node')}
          </span>
        </div>

        {/* Notification Bell */}
        <div style={{ position: 'relative' }}>
          <button
            id="btn-notifications"
            className="btn btn-ghost btn-icon"
            style={{ position: 'relative' }}
            onClick={() => setShowNotifs((v) => !v)}
          >
            <Bell size={16} />
            {notifications.length > 0 && <span className="notif-dot" />}
          </button>

          {showNotifs && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: '320px',
                background: '#FFFFFF',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 500,
                overflow: 'hidden',
              }}
            >
              <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)' }}>
                <span style={{ fontWeight: 700, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)' }}>System Notifications</span>
                <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setShowNotifs(false)}>
                  <X size={13} />
                </button>
              </div>
              {notifications.length === 0 && (
                <div style={{ padding: '20px 14px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12.5 }}>
                  No active system alerts
                </div>
              )}
              {notifications.map((n) => (
                <div
                  key={n.id}
                  style={{
                    padding: '10px 14px',
                    borderBottom: '1px solid var(--border-subtle)',
                    display: 'flex',
                    gap: 10,
                    alignItems: 'flex-start',
                  }}
                >
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: TYPE_COLOR[n.type] || 'var(--brand-primary)', marginTop: 6, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--text-primary)' }}>{n.title}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: 11.5, marginTop: 2 }}>{n.msg}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 10.5, marginTop: 4 }}>{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Node Verification Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
          <span className="badge-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--brand-success)', flexShrink: 0 }} />
          <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-secondary)' }}>
            {role === 'admin' ? 'Coordinating Hub' : `${hospital.city || 'Local Node'} (Secure)`}
          </span>
        </div>

        {/* User Monogram Avatar */}
        <div className="avatar" id="topbar-avatar" title={role === 'admin' ? 'Administrator' : hospital.name}>
          {role === 'admin' ? 'AD' : role === 'technician' ? 'LT' : hospital.initials}
        </div>
      </div>
    </header>
  );
}
