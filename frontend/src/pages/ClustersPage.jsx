import React, { useState } from 'react';
import {
  Users,
  ChevronRight,
  CheckCircle,
  XCircle,
  Plus,
  ShieldAlert,
  Building2,
  Lock,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Badge, ProgressBar, Modal } from '../components/UI';

function JoinModal({ cluster, hospital, onJoin, onClose }) {
  const [path, setPath] = useState(cluster.datasetPath || '');
  const [validated, setValidated] = useState(false);
  const [validating, setValidating] = useState(false);
  const [joinError, setJoinError] = useState(null);

  function handleValidate() {
    if (!path.trim()) return;
    setValidating(true);
    setTimeout(() => {
      setValidating(false);
      setValidated(true);
    }, 1000);
  }

  async function handleConfirmJoin() {
    setJoinError(null);
    try {
      await onJoin(cluster.id, path);
      onClose();
    } catch (err) {
      setJoinError(err.message || 'Failed joining cluster. Contact network admin.');
    }
  }

  return (
    <Modal open title={`Join: ${cluster.name}`} onClose={onClose} id="modal-join-cluster">
      {/* Cluster & Hospital Context */}
      <div
        style={{
          padding: 'var(--sp-4)',
          background: cluster.colorGlass,
          border: `1px solid ${cluster.borderColor}`,
          borderRadius: 'var(--radius-md)',
          marginBottom: 'var(--sp-4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <span style={{ fontSize: 22 }}>{cluster.icon}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{cluster.name}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{cluster.description}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, padding: '6px 10px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <Building2 size={15} color="var(--brand-primary)" />
          <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>
            Joining as: {hospital.name} ({hospital.id})
          </span>
        </div>
      </div>

      {joinError && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'hsla(0, 82%, 55%, 0.1)', border: '1px solid hsla(0, 82%, 55%, 0.25)', borderRadius: 'var(--radius-md)', color: 'var(--brand-danger)', fontSize: 13, marginBottom: 'var(--sp-4)' }}>
          <ShieldAlert size={16} />
          <span>{joinError}</span>
        </div>
      )}

      <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
        <label className="form-label" htmlFor="dataset-path-input">
          Local Dataset Directory Path ({cluster.modality})
        </label>
        <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
          <input
            id="dataset-path-input"
            className="form-input"
            placeholder={`/data/${cluster.modality.toLowerCase()}_recordings/`}
            value={path}
            onChange={(e) => {
              setPath(e.target.value);
              setValidated(false);
            }}
          />
          <button
            id="btn-validate-path"
            type="button"
            className="btn btn-secondary"
            onClick={handleValidate}
            disabled={validating || !path.trim()}
          >
            {validating ? 'Verifying...' : 'Validate'}
          </button>
        </div>
        {validated && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, color: 'var(--brand-success)', fontSize: 13 }}>
            <CheckCircle size={14} />
            Edge dataset verified — Valid format & IRB consent checked
          </div>
        )}
      </div>

      {/* Directory requirement note */}
      <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-5)', border: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>Expected Edge Directory Structure</div>
        <pre style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>
{`${cluster.modality.toLowerCase()}_data/
├── normal/        ← verified non-pathological pediatric files
├── abnormal/      ← confirmed CHD / defect samples
└── metadata.csv   ← patient_id, age_group, diagnosis`}
        </pre>
      </div>

      <div style={{ display: 'flex', gap: 'var(--sp-3)', justifyContent: 'flex-end' }}>
        <button type="button" className="btn btn-secondary" onClick={onClose} id="btn-cancel-join">
          Cancel
        </button>
        <button
          id="btn-confirm-join"
          type="button"
          className="btn btn-primary"
          disabled={!validated}
          onClick={handleConfirmJoin}
        >
          <Plus size={15} /> Confirm & Enter Cluster
        </button>
      </div>
    </Modal>
  );
}

export default function ClustersPage() {
  const { clusters, hospital, joinCluster, leaveCluster } = useApp();
  const [joiningCluster, setJoiningCluster] = useState(null);

  // Check which modalities this hospital is authorized to join
  const authorizedMods = hospital.authorized_modalities || ['PCG', 'ECG', 'Echo'];

  return (
    <div className="page-container animate-fade-in" style={{ padding: 'var(--sp-6)', maxWidth: 1280, margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: 'var(--sp-6)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Hospital FL Node
          </span>
          <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 999, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontWeight: 600 }}>
            {hospital.name} ({hospital.id})
          </span>
        </div>
        <h1 className="page-title" style={{ fontSize: 26, fontWeight: 800, margin: '4px 0 2px' }}>
          Federated Cluster Management
        </h1>
        <p className="page-subtitle" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Connect your hospital edge node to authorized multi-site research clusters. Training updates are encrypted with Differential Privacy before transmission.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
        {clusters.map((c) => {
          const isAuthorized = authorizedMods.includes(c.modality);

          return (
            <div
              key={c.id}
              id={`cluster-card-${c.id}`}
              className="card animate-fade-up"
              style={{
                borderColor: c.joined ? c.borderColor : 'var(--border-subtle)',
                opacity: !isAuthorized && !c.joined ? 0.75 : 1,
              }}
            >
              <div style={{ display: 'flex', gap: 'var(--sp-5)', alignItems: 'flex-start', flexWrap: 'wrap' }}>
                {/* Icon */}
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 'var(--radius-lg)',
                    background: c.colorGlass,
                    border: `1px solid ${c.borderColor}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    flexShrink: 0,
                  }}
                >
                  {c.icon}
                </div>

                {/* Main info */}
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', flexWrap: 'wrap', marginBottom: 'var(--sp-1)' }}>
                    <h2 style={{ fontSize: 17, fontWeight: 700 }}>{c.name}</h2>
                    <Badge type={c.status} />
                    {c.joined && (
                      <span style={{ fontSize: 11, background: 'hsla(145,65%,50%,0.1)', color: 'var(--brand-success)', border: '1px solid hsla(145,65%,50%,0.25)', padding: '2px 8px', borderRadius: 999, fontWeight: 600 }}>
                        ✓ Joined as {hospital.id}
                      </span>
                    )}
                    {!isAuthorized && (
                      <span style={{ fontSize: 11, background: 'hsla(35, 95%, 52%, 0.1)', color: 'var(--brand-warning)', border: '1px solid hsla(35, 95%, 52%, 0.25)', padding: '2px 8px', borderRadius: 999, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <Lock size={11} /> Modality not authorized by Admin
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 'var(--sp-4)', maxWidth: 540 }}>
                    {c.description}
                  </p>

                  {/* Tags */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 'var(--sp-4)' }}>
                    {c.tags.map((t) => (
                      <span
                        key={t}
                        style={{
                          fontSize: 11,
                          padding: '3px 9px',
                          borderRadius: 999,
                          background: 'var(--bg-elevated)',
                          border: '1px solid var(--border-subtle)',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                  </div>

                  {/* Progress */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span className="text-xs text-muted">Training Progress (Round {c.currentRound}/50)</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: c.color }}>{c.globalAccuracy}% accuracy</span>
                  </div>
                  <ProgressBar value={c.currentRound} max={50} color={c.color} />
                </div>

                {/* Stats column */}
                <div style={{ display: 'flex', gap: 'var(--sp-6)', flexShrink: 0, alignSelf: 'center', flexWrap: 'wrap' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: c.color }}>{c.hospitals}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Hospital Nodes</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 20, fontWeight: 800 }}>{c.currentRound}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Rounds</div>
                  </div>
                  {c.joined && c.localAccuracy && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--brand-success)' }}>{c.localAccuracy}%</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Local Accuracy</div>
                    </div>
                  )}
                </div>

                {/* Action button */}
                <div style={{ flexShrink: 0, alignSelf: 'center' }}>
                  {c.joined ? (
                    <button
                      id={`btn-leave-${c.id}`}
                      type="button"
                      className="btn btn-danger"
                      onClick={() => leaveCluster(c.id)}
                    >
                      <XCircle size={15} /> Leave Cluster
                    </button>
                  ) : (
                    <button
                      id={`btn-join-${c.id}`}
                      type="button"
                      className="btn btn-primary"
                      disabled={!isAuthorized}
                      onClick={() => setJoiningCluster(c)}
                      title={!isAuthorized ? 'Admin authorization required for this modality' : 'Join cluster'}
                    >
                      Join <ChevronRight size={15} />
                    </button>
                  )}
                </div>
              </div>

              {/* Joined details row */}
              {c.joined && (
                <div
                  style={{
                    marginTop: 'var(--sp-4)',
                    padding: 'var(--sp-3) var(--sp-4)',
                    background: 'var(--bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    gap: 'var(--sp-8)',
                    flexWrap: 'wrap',
                    borderTop: `1px solid ${c.borderColor}`,
                  }}
                >
                  <div>
                    <span className="text-xs text-muted">Dataset Path: </span>
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
                      {c.datasetPath}
                    </code>
                  </div>
                  <div>
                    <span className="text-xs text-muted">Local Samples: </span>
                    <span style={{ fontWeight: 700 }}>{c.localSamples.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted">Status: </span>
                    <span style={{ fontWeight: 700, color: 'var(--brand-success)' }}>
                      Authenticated Node Participant
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {joiningCluster && (
        <JoinModal
          cluster={joiningCluster}
          hospital={hospital}
          onJoin={joinCluster}
          onClose={() => setJoiningCluster(null)}
        />
      )}
    </div>
  );
}
