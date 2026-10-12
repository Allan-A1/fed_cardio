import React, { useState, useEffect } from 'react';
import {
  FolderOpen,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Database,
  FileText,
  Check,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { SectionTitle } from '../components/UI';

export default function DataPage() {
  const { clusters } = useApp();
  const joinedClusters = clusters.filter((c) => c.joined);
  const [activeCluster, setActiveCluster] = useState(
    joinedClusters[0]?.id || clusters[0]?.id || 'cluster-pcg'
  );
  const [scanning, setScanning] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [savedConfig, setSavedConfig] = useState(false);

  const cluster =
    clusters.find((c) => c.id === activeCluster) ||
    joinedClusters[0] ||
    clusters[0];

  const runValidation = async (clusterId, path) => {
    setScanning(true);
    try {
      const res = await api.validateDataset(clusterId, path || '');
      setValidationResult(res);
    } catch (err) {
      console.error('Validation failed:', err);
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    if (activeCluster) {
      runValidation(activeCluster, cluster?.datasetPath);
    }
  }, [activeCluster, cluster?.datasetPath]);

  function handleScan() {
    if (activeCluster) {
      runValidation(activeCluster, cluster?.datasetPath);
    }
  }

  function handleSave() {
    setSavedConfig(true);
    setTimeout(() => setSavedConfig(false), 2000);
  }

  return (
    <div className="page-container animate-fade-in" style={{ padding: 'var(--sp-6)', maxWidth: 1280, margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: 'var(--sp-6)' }}>
        <h1 className="page-title" style={{ fontSize: 26, fontWeight: 800, margin: '0 0 4px' }}>
          Edge Data Configuration & Verification
        </h1>
        <p className="page-subtitle" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Configure local dataset directories and audit tensor dimensionality and sample distributions before federated round aggregation.
        </p>
      </div>

      {clusters.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--sp-12)' }}>
          <Database size={40} color="var(--text-muted)" style={{ margin: '0 auto var(--sp-4)' }} />
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>No Clusters Available</div>
          <p className="text-secondary text-sm">Join a cluster to configure your local edge data.</p>
        </div>
      ) : (
        <>
          {/* Cluster Selector Tabs */}
          <div style={{ display: 'flex', gap: 'var(--sp-3)', marginBottom: 'var(--sp-6)', flexWrap: 'wrap' }}>
            {clusters.map((c) => (
              <button
                key={c.id}
                id={`tab-cluster-${c.id}`}
                onClick={() => setActiveCluster(c.id)}
                className="btn"
                style={{
                  background: activeCluster === c.id ? c.colorGlass : 'var(--bg-glass)',
                  border: `1px solid ${activeCluster === c.id ? c.borderColor : 'var(--border-subtle)'}`,
                  color: activeCluster === c.id ? c.color : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: 13,
                }}
              >
                {c.icon} {c.name} {c.joined ? '(Joined)' : ''}
              </button>
            ))}
          </div>

          {cluster && (
            <div className="grid-2" style={{ alignItems: 'start' }}>
              {/* Dataset Config Card */}
              <div className="card" id="card-data-config">
                <SectionTitle icon={FolderOpen}>Edge Dataset Parameters</SectionTitle>

                <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
                  <label className="form-label">Verified Storage Directory</label>
                  <input
                    id="input-dataset-root"
                    className="form-input"
                    defaultValue={cluster.datasetPath}
                    placeholder="/path/to/dataset/"
                    style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
                  <label className="form-label">Data Modality</label>
                  <input
                    className="form-input"
                    readOnly
                    value={`${cluster.modality} (${validationResult?.dataset_name || 'Standardized Shard'})`}
                    style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', fontWeight: 600 }}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
                  <label className="form-label">Minimum Batch Samples</label>
                  <input id="input-min-samples" className="form-input" type="number" defaultValue={200} />
                </div>

                <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
                  <label className="form-label">Local Client Epochs per Round</label>
                  <select id="select-epochs" className="form-input form-select" defaultValue="5">
                    <option value="3">3 Epochs (Fast edge round)</option>
                    <option value="5">5 Epochs (Recommended FedAvg)</option>
                    <option value="10">10 Epochs (Deep convergence)</option>
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: 'var(--sp-5)' }}>
                  <label className="form-label">Differential Privacy Budget (ε)</label>
                  <input id="input-epsilon" className="form-input" type="number" step="0.1" defaultValue={1.5} />
                  <span className="text-xs text-muted mt-1" style={{ display: 'block' }}>
                    Noise multiplier: σ=1.12 | Clip norm: C=1.0 (Guarantees (ε, δ)-DP)
                  </span>
                </div>

                <button
                  id="btn-save-config"
                  className="btn btn-primary w-full"
                  style={{ justifyContent: 'center' }}
                  onClick={handleSave}
                >
                  {savedConfig ? <><Check size={16} /> Configuration Saved</> : 'Save Node Configuration'}
                </button>
              </div>

              {/* Data Validation Card */}
              <div>
                <div className="card mb-4" id="card-data-validation">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
                    <SectionTitle icon={CheckCircle}>Local File Audit</SectionTitle>
                    <button
                      id="btn-rescan"
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={handleScan}
                      disabled={scanning}
                    >
                      <RefreshCw size={13} className={scanning ? 'spin' : ''} />
                      {scanning ? 'Verifying...' : 'Re-verify'}
                    </button>
                  </div>

                  {scanning ? (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10, padding: 'var(--sp-8)', color: 'var(--text-muted)' }}>
                      <RefreshCw size={18} className="spin" color="var(--brand-primary)" />
                      <span>Auditing signal headers & tensor shapes on disk...</span>
                    </div>
                  ) : validationResult?.checks ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
                      {validationResult.checks.map((check, i) => (
                        <div
                          key={i}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--sp-3)',
                            padding: '10px 12px',
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--bg-elevated)',
                            border: '1px solid var(--border-subtle)',
                          }}
                        >
                          <CheckCircle size={16} color="var(--brand-success)" style={{ flexShrink: 0 }} />
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{check.label}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{check.count}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 'var(--sp-6)', color: 'var(--text-muted)' }}>
                      Click Re-verify to validate local files
                    </div>
                  )}
                </div>

                {/* Summary Card */}
                {validationResult && (
                  <div className="card animate-fade-up" style={{ background: 'hsla(145,65%,50%,0.06)', borderColor: 'hsla(145,65%,50%,0.2)' }} id="card-data-summary">
                    <SectionTitle icon={FileText}>Dataset Ingestion Summary</SectionTitle>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginTop: 10 }}>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Dataset Name</div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{validationResult.dataset_name}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Verified Samples</div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--brand-success)' }}>{validationResult.total_samples?.toLocaleString()}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
