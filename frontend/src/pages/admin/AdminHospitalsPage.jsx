import React, { useState, useEffect } from 'react';
import {
  Building2,
  Plus,
  Search,
  KeyRound,
  ShieldAlert,
  CheckCircle,
  XCircle,
  Copy,
  Check,
  Activity,
  Trash2,
  RefreshCw,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { api } from '../../api/client';
import { Modal } from '../../components/UI';

export default function AdminHospitalsPage() {
  const [hospitals, setHospitals] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // "Add Hospital" Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [formName, setFormName] = useState('');
  const [formCity, setFormCity] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formModalities, setFormModalities] = useState(['PCG', 'ECG', 'Echo']);
  const [formStatus, setFormStatus] = useState('active');
  const [formNotes, setFormNotes] = useState('');
  const [creating, setCreating] = useState(false);

  // "Credentials Created" Dialog
  const [createdCredentials, setCreatedCredentials] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const [hList, mData] = await Promise.all([
        api.adminHospitals(),
        api.adminMetrics(),
      ]);
      setHospitals(hList || []);
      setMetrics(mData);
    } catch (err) {
      console.error('Failed to load admin hospital data:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function toggleModality(mod) {
    if (formModalities.includes(mod)) {
      if (formModalities.length > 1) {
        setFormModalities(formModalities.filter((m) => m !== mod));
      }
    } else {
      setFormModalities([...formModalities, mod]);
    }
  }

  async function handleCreateHospital(e) {
    e.preventDefault();
    if (!formName.trim() || !formCity.trim() || !formEmail.trim()) return;

    setCreating(true);
    try {
      const created = await api.adminCreateHospital({
        name: formName.trim(),
        city: formCity.trim(),
        country: 'India',
        contact_email: formEmail.trim(),
        authorized_modalities: formModalities,
        status: formStatus,
        notes: formNotes.trim(),
      });

      setShowAddModal(false);
      // Reset form
      setFormName('');
      setFormCity('');
      setFormEmail('');
      setFormNotes('');
      setFormModalities(['PCG', 'ECG', 'Echo']);

      // Show credentials reveal modal
      setCreatedCredentials(created);
      await loadData();
    } catch (err) {
      alert(`Failed to create hospital: ${err.message}`);
    } finally {
      setCreating(false);
    }
  }

  async function handleStatusToggle(hosp) {
    const nextStatus = hosp.status === 'active' ? 'suspended' : 'active';
    try {
      await api.adminUpdateHospitalStatus(hosp.id, nextStatus);
      await loadData();
    } catch (err) {
      alert(`Failed updating status: ${err.message}`);
    }
  }

  async function handleRegenerateKey(hosp) {
    if (!window.confirm(`Regenerate access key for ${hosp.name}? Current key will stop working immediately.`)) {
      return;
    }
    try {
      const updated = await api.adminRegenerateKey(hosp.id);
      setCreatedCredentials(updated);
      await loadData();
    } catch (err) {
      alert(`Failed regenerating key: ${err.message}`);
    }
  }

  async function handleDeleteHospital(hosp) {
    if (!window.confirm(`Are you sure you want to remove ${hosp.name} from the network?`)) {
      return;
    }
    try {
      await api.adminDeleteHospital(hosp.id);
      await loadData();
    } catch (err) {
      alert(`Failed deleting hospital: ${err.message}`);
    }
  }

  function handleCopyCredentials() {
    if (!createdCredentials) return;
    const text = `FedMed Hospital Access Credentials:\nHospital ID: ${createdCredentials.id}\nSecret Access Key: ${createdCredentials.access_key}\nHospital Name: ${createdCredentials.name}`;
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  }

  const filtered = hospitals.filter((h) => {
    const matchesSearch =
      h.name.toLowerCase().includes(search.toLowerCase()) ||
      h.id.toLowerCase().includes(search.toLowerCase()) ||
      h.city.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || h.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page-container" style={{ padding: 'var(--sp-6)', maxWidth: 1280, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--sp-6)', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Governance & Access Control
            </span>
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em', margin: '4px 0 2px' }}>
            Hospital Node Registry
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Supervise participating medical centers, generate cluster credentials, and enforce data modalities.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadData}
            title="Refresh Registry"
          >
            <RefreshCw size={15} />
            Refresh
          </button>
          <button
            id="btn-register-hospital-modal"
            type="button"
            className="btn btn-primary"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={16} />
            Register New Hospital
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--sp-4)', marginBottom: 'var(--sp-6)' }}>
          <div className="card" style={{ padding: 'var(--sp-4)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Registered Hospitals</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 4 }}>{metrics.total_hospitals}</div>
            <div style={{ fontSize: 11, color: 'var(--brand-success)', marginTop: 2 }}>{metrics.active_hospitals} active nodes</div>
          </div>

          <div className="card" style={{ padding: 'var(--sp-4)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Active Cluster Memberships</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 4, color: 'var(--brand-primary)' }}>{metrics.total_cluster_nodes}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Across PCG, ECG, Echo</div>
          </div>

          <div className="card" style={{ padding: 'var(--sp-4)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Pediatric Patients Contributed</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 4, color: 'var(--brand-secondary)' }}>
              {metrics.total_patients_contributed?.toLocaleString()}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>De-identified local samples</div>
          </div>

          <div className="card" style={{ padding: 'var(--sp-4)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Avg Contribution Score</div>
            <div style={{ fontSize: 26, fontWeight: 800, marginTop: 4, color: 'var(--brand-accent)' }}>
              {metrics.average_contribution_score}%
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Federated reputation index</div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: 'var(--sp-4)', marginBottom: 'var(--sp-6)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ position: 'relative', flex: '1 1 300px', maxWidth: 420 }}>
          <input
            type="text"
            className="form-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by hospital name, ID, or city..."
            style={{ paddingLeft: 36 }}
          />
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 4 }}>Filter Status:</span>
          {['all', 'active', 'pending', 'suspended'].map((st) => (
            <button
              key={st}
              type="button"
              className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setStatusFilter(st)}
              style={{ textTransform: 'capitalize' }}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Hospitals Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Hospital Node</th>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Credentials</th>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Authorized Modalities</th>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Joined Clusters</th>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Status</th>
              <th style={{ padding: '14px 16px', fontWeight: 600 }}>Score</th>
              <th style={{ padding: '14px 16px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                  Loading hospital directory...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                  No hospitals found matching criteria.
                </td>
              </tr>
            ) : (
              filtered.map((hosp) => (
                <tr key={hosp.id} style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s' }}>
                  {/* Name & Location */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div className="avatar" style={{ width: 34, height: 34, fontSize: 13, background: 'var(--brand-primary-glow)', color: 'var(--brand-primary)', fontWeight: 700 }}>
                        {hosp.initials}
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{hosp.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          {hosp.city}, {hosp.country} • {hosp.contact_email}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Credentials */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--brand-primary)' }}>
                      {hosp.id}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      <KeyRound size={12} />
                      <span style={{ fontFamily: 'var(--font-mono)' }}>••••••••••••</span>
                    </div>
                  </td>

                  {/* Modalities */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {hosp.authorized_modalities?.map((m) => (
                        <span
                          key={m}
                          style={{
                            padding: '2px 6px',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 10,
                            fontWeight: 700,
                            background: m === 'PCG' ? 'hsla(173,85%,40%,0.1)' : m === 'ECG' ? 'hsla(221,100%,55%,0.1)' : 'hsla(262,80%,58%,0.1)',
                            color: m === 'PCG' ? 'var(--brand-secondary)' : m === 'ECG' ? 'var(--brand-primary)' : 'var(--brand-accent)',
                          }}
                        >
                          {m}
                        </span>
                      ))}
                    </div>
                  </td>

                  {/* Joined Clusters */}
                  <td style={{ padding: '14px 16px' }}>
                    {hosp.joined_clusters?.length > 0 ? (
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--brand-success)' }}>
                        {hosp.joined_clusters.length} Cluster{hosp.joined_clusters.length > 1 ? 's' : ''} Active
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>None joined</span>
                    )}
                  </td>

                  {/* Status */}
                  <td style={{ padding: '14px 16px' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '3px 8px',
                        borderRadius: 999,
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        background:
                          hosp.status === 'active'
                            ? 'hsla(142, 70%, 42%, 0.12)'
                            : hosp.status === 'pending'
                            ? 'hsla(35, 95%, 52%, 0.12)'
                            : 'hsla(0, 82%, 55%, 0.12)',
                        color:
                          hosp.status === 'active'
                            ? 'var(--brand-success)'
                            : hosp.status === 'pending'
                            ? 'var(--brand-warning)'
                            : 'var(--brand-danger)',
                      }}
                    >
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
                      {hosp.status}
                    </span>
                  </td>

                  {/* Contribution Score */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{hosp.contribution_score}%</div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{hosp.patients_contributed} samples</div>
                  </td>

                  {/* Action buttons */}
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: 6 }}>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleStatusToggle(hosp)}
                        title={hosp.status === 'active' ? 'Suspend Hospital' : 'Activate Hospital'}
                      >
                        {hosp.status === 'active' ? 'Suspend' : 'Activate'}
                      </button>

                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleRegenerateKey(hosp)}
                        title="Regenerate Credentials"
                      >
                        <KeyRound size={13} />
                      </button>

                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--brand-danger)' }}
                        onClick={() => handleDeleteHospital(hosp)}
                        title="Delete Hospital"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Modal: Register New Hospital ─────────────────────────────────────── */}
      {showAddModal && (
        <Modal
          open
          title="Register New Partner Hospital"
          onClose={() => setShowAddModal(false)}
          id="modal-add-hospital"
        >
          <form onSubmit={handleCreateHospital}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 'var(--sp-4)' }}>
              Provide the hospital facility details. The system will auto-generate unique credentials (Hospital ID and Secret Access Key) for them to join the federated network.
            </p>

            <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
              <label className="form-label" htmlFor="hosp-name-input">Hospital Facility Name *</label>
              <input
                id="hosp-name-input"
                type="text"
                className="form-input"
                placeholder="e.g. Manipal Children's Hospital"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="hosp-city-input">City *</label>
                <input
                  id="hosp-city-input"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Bangalore"
                  value={formCity}
                  onChange={(e) => setFormCity(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="hosp-email-input">Official Contact Email *</label>
                <input
                  id="hosp-email-input"
                  type="email"
                  className="form-input"
                  placeholder="cardiology@manipal.edu"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
              <label className="form-label">Authorized Modalities</label>
              <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
                {['PCG', 'ECG', 'Echo'].map((mod) => (
                  <label key={mod} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={formModalities.includes(mod)}
                      onChange={() => toggleModality(mod)}
                    />
                    <span>{mod} {mod === 'PCG' ? '(Phonocardiogram)' : mod === 'ECG' ? '(12-Lead ECG)' : '(Echocardiogram)'}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 'var(--sp-4)' }}>
              <label className="form-label" htmlFor="hosp-status-select">Initial Access Status</label>
              <select
                id="hosp-status-select"
                className="form-input"
                value={formStatus}
                onChange={(e) => setFormStatus(e.target.value)}
              >
                <option value="active">Active (Immediate Cluster Access)</option>
                <option value="pending">Pending Verification / IRB</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 'var(--sp-5)' }}>
              <label className="form-label" htmlFor="hosp-notes-input">Clinical Notes / Department Description</label>
              <textarea
                id="hosp-notes-input"
                className="form-input"
                rows={2}
                placeholder="e.g. Tertiary center with pediatric auscultation screening protocols..."
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowAddModal(false)}
              >
                Cancel
              </button>
              <button
                id="btn-submit-create-hospital"
                type="submit"
                className="btn btn-primary"
                disabled={creating}
              >
                {creating ? 'Registering...' : 'Register & Generate Credentials →'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* ── Modal: Generated Credentials Card ─────────────────────────────────── */}
      {createdCredentials && (
        <Modal
          open
          title="Hospital Credentials Generated"
          onClose={() => setCreatedCredentials(null)}
          id="modal-credentials-card"
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: 'hsla(142, 70%, 42%, 0.1)', border: '1px solid hsla(142, 70%, 42%, 0.25)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--sp-4)' }}>
              <CheckCircle size={20} color="var(--brand-success)" style={{ flexShrink: 0 }} />
              <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                <strong>{createdCredentials.name}</strong> has been added to the database. Provide these credentials to the hospital operator:
              </div>
            </div>

            <div className="card" style={{ padding: 'var(--sp-5)', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', marginBottom: 'var(--sp-4)' }}>
              <div style={{ marginBottom: 'var(--sp-3)' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hospital ID</div>
                <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--brand-primary)', marginTop: 2 }}>
                  {createdCredentials.id}
                </div>
              </div>

              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Secret Access Key</div>
                <div style={{ fontSize: 16, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--brand-accent)', marginTop: 2 }}>
                  {createdCredentials.access_key}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Save this key securely; it can be used on the Hospital Login page.
              </span>

              <button
                type="button"
                className="btn btn-primary"
                onClick={handleCopyCredentials}
              >
                {copiedKey ? <Check size={16} /> : <Copy size={16} />}
                {copiedKey ? 'Copied to Clipboard!' : 'Copy Credentials'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
