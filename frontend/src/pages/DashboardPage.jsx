import React, { useState, useEffect } from 'react';
import {
  Network, Hospital, TrendingUp, Award, ShieldCheck, Activity, Bell
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { StatCard, Badge, ProgressBar, SectionTitle } from '../components/UI';

const CUSTOM_TOOLTIP = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', padding: '10px 14px', fontSize: 13, boxShadow: 'var(--shadow-md)' }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>Round {label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {p.value.toFixed(1)}%
        </p>
      ))}
    </div>
  );
};

export default function DashboardPage() {
  const { hospital, clusters, notifications } = useApp();
  const [accuracyHistory, setAccuracyHistory] = useState([]);
  const [networkHospitals, setNetworkHospitals] = useState([]);

  useEffect(() => {
    api.clusterMetrics('cluster-pcg')
      .then((res) => setAccuracyHistory(res?.history || []))
      .catch((err) => console.error('Failed loading metrics history:', err));

    api.adminHospitals()
      .then((res) => setNetworkHospitals(res || []))
      .catch((err) => console.error('Failed loading hospitals:', err));
  }, []);

  const joinedClusters = clusters.filter(c => c.joined);
  const activePcg = clusters.find(c => c.id === 'cluster-pcg');

  return (
    <div className="page-container animate-fade-in">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Welcome back, <span style={{ color: 'var(--brand-secondary)' }}>{hospital.name}</span></h1>
        <p className="page-subtitle">Your medical center node is actively contributing to {joinedClusters.length} federated pediatric cardiology cluster{joinedClusters.length !== 1 ? 's' : ''}.</p>
      </div>

      {/* Notification Banner */}
      {notifications.length > 0 && (
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--sp-3) var(--sp-5)', display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', marginBottom: 'var(--sp-6)' }} id="notif-banner">
          <Bell size={16} color="var(--brand-secondary)" />
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>You have <strong style={{ color: 'var(--brand-primary)' }}>{notifications.length} clinical network notification{notifications.length > 1 ? 's' : ''}</strong></span>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid-4 mb-6">
        <StatCard
          id="stat-accuracy"
          icon={TrendingUp}
          iconColor="var(--brand-secondary)"
          iconBg="var(--brand-secondary-light)"
          value={activePcg ? `${activePcg.globalAccuracy}%` : '—'}
          label="Global Model Accuracy (PCG)"
          delta={activePcg ? +(activePcg.globalAccuracy - activePcg.prevAccuracy).toFixed(1) : null}
          deltaLabel="vs prev round"
        />
        <StatCard
          id="stat-hospitals"
          icon={Hospital}
          iconColor="var(--brand-primary)"
          iconBg="var(--bg-elevated)"
          value={clusters.length > 0 ? clusters.reduce((s, c) => s + (c.hospitals || 0), 0) : '—'}
          label="Consortium Hospitals"
          delta={null}
          deltaLabel=""
        />
        <StatCard
          id="stat-samples"
          icon={Activity}
          iconColor="var(--brand-success)"
          iconBg="var(--brand-success-bg)"
          value={hospital.patientsContributed > 0 ? hospital.patientsContributed.toLocaleString() : '—'}
          label="Pediatric Records Contributed"
          delta={null}
          deltaLabel=""
        />
        <StatCard
          id="stat-rounds"
          icon={Award}
          iconColor="var(--brand-warning)"
          iconBg="var(--brand-warning-bg)"
          value={hospital.roundsParticipated > 0 ? hospital.roundsParticipated : '—'}
          label="FL Aggregation Rounds"
          delta={null}
          deltaLabel=""
        />
      </div>

      {/* Charts Row */}
      <div className="grid-2 mb-6">
        {/* Global Accuracy Chart */}
        <div className="card animate-fade-up" id="chart-accuracy">
          <SectionTitle icon={TrendingUp}>Global vs Local Accuracy (PCG Cluster)</SectionTitle>
          {accuracyHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={accuracyHistory} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="round" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} label={{ value: 'FL Round', position: 'insideBottom', offset: -2, fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} unit="%" />
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Line type="monotone" dataKey="global" stroke="hsl(210,100%,56%)" strokeWidth={2.5} dot={false} name="Global Model" />
                <Line type="monotone" dataKey="local" stroke="hsl(145,65%,50%)" strokeWidth={2} strokeDasharray="5 4" dot={false} name="Your Local Model" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              Loading training convergence curves...
            </div>
          )}
        </div>

        {/* Cluster Summary */}
        <div className="card animate-fade-up" id="card-cluster-summary">
          <SectionTitle icon={Network}>Active Clusters</SectionTitle>
          {clusters.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
              {clusters.map(c => (
                <div key={c.id} style={{ padding: 'var(--sp-3) var(--sp-4)', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: `1px solid ${c.joined ? c.borderColor : 'var(--border-subtle)'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>{c.icon}</span>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</span>
                    </div>
                    <Badge type={c.status} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span className="text-sm text-muted">Round {c.currentRound}/{c.totalRounds}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: c.color }}>{c.globalAccuracy}%</span>
                  </div>
                  <ProgressBar value={c.currentRound} max={c.totalRounds} color={c.color} />
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 'var(--sp-8)', color: 'var(--text-muted)', fontSize: 13 }}>
              No clusters available
            </div>
          )}
        </div>
      </div>

      {/* Hospital Contributions Table */}
      <div className="card animate-fade-up" id="card-contributions">
        <SectionTitle icon={Hospital}>Participating Hospital Nodes & Contributions</SectionTitle>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                {['Hospital', 'City', 'Patient Samples', 'Accuracy / Score', 'Status'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, fontSize: 11, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {networkHospitals.length > 0 ? networkHospitals.map((h) => (
                <tr key={h.id} style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background var(--transition-fast)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-glass)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>
                    {h.name}
                    {h.id === hospital.id && (
                      <span style={{ marginLeft: 6, fontSize: 10, color: 'var(--brand-primary)', background: 'hsla(210,100%,56%,0.1)', padding: '2px 7px', borderRadius: 999 }}>
                        Current Node
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{h.city}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)' }}>{h.patients_contributed.toLocaleString()}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--brand-success)' }}>{h.contribution_score}%</span>
                  </td>
                  <td style={{ padding: '10px 12px' }}><Badge type={h.status} /></td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>Loading hospital contributions...</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Privacy / Security Card */}
      <div className="card mt-6 animate-fade-up" style={{ background: 'var(--brand-success-bg)', borderColor: 'var(--brand-success-border)' }} id="card-privacy">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-4)' }}>
          <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-sm)', background: '#FFFFFF', border: '1px solid var(--brand-success-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <ShieldCheck size={20} color="var(--brand-success)" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 13.5, color: 'var(--brand-primary)', marginBottom: 2 }}>Privacy-Preserving Federated Learning Architecture</div>
            <div style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
              Identifiable patient records remain strictly within hospital firewall perimeter. Differential privacy parameter (ε=1.5) and secure parameter aggregation prevent model inversion attacks.
            </div>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--sp-4)', flexShrink: 0 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--brand-success)' }}>ε=1.5</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Privacy Budget</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--brand-success)' }}>AES-256</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Encryption</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
