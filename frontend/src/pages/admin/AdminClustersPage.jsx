import React, { useState, useEffect } from 'react';
import {
  Network,
  Activity,
  Users,
  Shield,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { api } from '../../api/client';

export default function AdminClustersPage() {
  const [clusters, setClusters] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cList, hList] = await Promise.all([
          api.clusters(),
          api.adminHospitals(),
        ]);
        setClusters(cList || []);
        setHospitals(hList || []);
      } catch (e) {
        console.error('Failed loading clusters oversight:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="page-container" style={{ padding: 'var(--sp-6)', maxWidth: 1280, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--sp-6)' }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Network Topology
        </span>
        <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em', margin: '4px 0 2px' }}>
          Federated Cluster Overseer
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Supervise global aggregation progress, modality sharding, and participating hospital nodes across clusters.
        </p>
      </div>

      {loading ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading network cluster data...
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 'var(--sp-6)' }}>
          {clusters.map((cluster) => {
            const memberHospitals = hospitals.filter((h) =>
              h.joined_clusters?.includes(cluster.id)
            );

            return (
              <div
                key={cluster.id}
                className="card"
                style={{
                  padding: 'var(--sp-6)',
                  borderTop: `4px solid ${cluster.color}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  {/* Top Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--sp-3)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 24 }}>{cluster.icon}</span>
                      <div>
                        <div style={{ fontSize: 16, fontWeight: 800 }}>{cluster.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{cluster.id}</div>
                      </div>
                    </div>

                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 999,
                        fontSize: 10,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background: cluster.status === 'training' ? 'hsla(35, 95%, 52%, 0.15)' : 'hsla(142, 70%, 42%, 0.15)',
                        color: cluster.status === 'training' ? 'var(--brand-warning)' : 'var(--brand-success)',
                      }}
                    >
                      {cluster.status}
                    </span>
                  </div>

                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 'var(--sp-4)' }}>
                    {cluster.description}
                  </p>

                  {/* Metrics Row */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, padding: 'var(--sp-3)', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--sp-5)' }}>
                    <div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Global Acc</div>
                      <div style={{ fontSize: 16, fontWeight: 800, color: cluster.color }}>{cluster.globalAccuracy}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>FL Rounds</div>
                      <div style={{ fontSize: 16, fontWeight: 800 }}>{cluster.currentRound} / {cluster.totalRounds}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Nodes</div>
                      <div style={{ fontSize: 16, fontWeight: 800 }}>{memberHospitals.length}</div>
                    </div>
                  </div>

                  {/* Connected Hospitals List */}
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Users size={14} color="var(--brand-primary)" />
                      Connected Hospital Nodes ({memberHospitals.length})
                    </div>

                    {memberHospitals.length === 0 ? (
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', padding: '8px 0' }}>
                        No hospitals currently joined to this cluster.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {memberHospitals.map((h) => (
                          <div
                            key={h.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '8px 10px',
                              background: 'var(--bg-base)',
                              border: '1px solid var(--border-subtle)',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: 12,
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{h.name}</span>
                              <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>({h.id})</span>
                            </div>
                            <span style={{ fontSize: 11, color: 'var(--brand-success)', fontWeight: 600 }}>
                              Score: {h.contribution_score}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ marginTop: 'var(--sp-5)', paddingTop: 'var(--sp-4)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Modality Target: <strong>{cluster.modality}</strong>
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Sync: {cluster.lastSync}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
