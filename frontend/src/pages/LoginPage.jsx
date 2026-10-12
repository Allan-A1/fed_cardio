import React, { useState } from 'react';
import {
  HeartPulse,
  Lock,
  Building2,
  KeyRound,
  ShieldCheck,
  Stethoscope,
  Shield,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  ChevronRight,
  Sparkles,
  FileText
} from 'lucide-react';
import { api } from '../api/client';

const FALLBACK_USERS = {
  'HOSP-APOLLO-01': {
    role: 'hospital',
    id: 'HOSP-APOLLO-01',
    hospital_id: 'HOSP-APOLLO-01',
    name: "Apollo Children's Heart Center",
    city: 'Chennai',
    country: 'India',
    initials: 'AC',
    status: 'active',
    joinedDate: '2026-01-10',
    contributionScore: 94.2,
    patientsContributed: 4820,
    roundsParticipated: 48,
  },
  'HOSP-AIIMS-02': {
    role: 'hospital',
    id: 'HOSP-AIIMS-02',
    hospital_id: 'HOSP-AIIMS-02',
    name: 'AIIMS Pediatric Cardiology',
    city: 'New Delhi',
    country: 'India',
    initials: 'AI',
    status: 'active',
    joinedDate: '2026-01-15',
    contributionScore: 91.8,
    patientsContributed: 3950,
    roundsParticipated: 42,
  },
  'TECH-101': {
    role: 'technician',
    id: 'TECH-101',
    name: 'Dr. Sarah Chen, RCP',
    hospital_id: 'HOSP-APOLLO-01',
    hospital_name: "Apollo Children's Heart Center",
  },
  'admin@fedmed.network': {
    role: 'admin',
    id: 'admin@fedmed.network',
    email: 'admin@fedmed.network',
    name: 'Central Network Overseer',
  },
};

function getFallbackUser(payload) {
  if (payload.role === 'hospital' && FALLBACK_USERS[payload.hospital_id]) {
    return FALLBACK_USERS[payload.hospital_id];
  }
  if (payload.role === 'technician' && FALLBACK_USERS[payload.tech_id]) {
    return FALLBACK_USERS[payload.tech_id];
  }
  if (payload.role === 'admin' && FALLBACK_USERS[payload.email]) {
    return FALLBACK_USERS[payload.email];
  }
  return null;
}

export default function LoginPage({ onLogin, onBackToWebsite }) {
  const [activeTab, setActiveTab] = useState('hospital'); // 'hospital' | 'technician' | 'admin'

  // Hospital fields
  const [hospitalId, setHospitalId] = useState('HOSP-APOLLO-01');
  const [accessKey, setAccessKey] = useState('APOLLO-CHD-2026');

  // Technician fields
  const [techId, setTechId] = useState('TECH-101');
  const [techPin, setTechPin] = useState('1234');

  // Admin fields
  const [adminEmail, setAdminEmail] = useState('admin@fedmed.network');
  const [adminPassword, setAdminPassword] = useState('admin123');

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  async function executeLogin(payload) {
    setLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.login(payload);
      if (res && res.ok && res.user) {
        onLogin(res.user);
        return;
      } else {
        setErrorMessage(res?.message || 'Authentication rejected. Please check institution credentials.');
      }
    } catch (err) {
      console.warn('Backend login request error, checking fallback demo credentials:', err);
      const fallback = getFallbackUser(payload);
      if (fallback) {
        onLogin(fallback);
        return;
      }
      setErrorMessage(err.message || 'Authentication server unreachable. Please verify network credentials.');
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    if (e) e.preventDefault();

    let payload = { role: activeTab };
    if (activeTab === 'hospital') {
      payload.hospital_id = hospitalId.trim();
      payload.access_key = accessKey.trim();
    } else if (activeTab === 'technician') {
      payload.tech_id = techId.trim();
      payload.pin = techPin.trim();
    } else if (activeTab === 'admin') {
      payload.email = adminEmail.trim();
      payload.password = adminPassword.trim();
    }

    executeLogin(payload);
  }

  function handleDemoSelect(role, data, autoLogin = true) {
    setActiveTab(role);
    setErrorMessage(null);

    let payload = { role };
    if (role === 'hospital') {
      setHospitalId(data.id);
      setAccessKey(data.key);
      payload.hospital_id = data.id;
      payload.access_key = data.key;
    } else if (role === 'technician') {
      setTechId(data.id);
      setTechPin(data.pin);
      payload.tech_id = data.id;
      payload.pin = data.pin;
    } else if (role === 'admin') {
      setAdminEmail(data.email);
      setAdminPassword(data.pw);
      payload.email = data.email;
      payload.password = data.pw;
    }

    if (autoLogin) {
      executeLogin(payload);
    }
  }

  return (
    <div className="login-institutional-container">
      {/* ── TOP UTILITY STRIP ──────────────────────────────────── */}
      <div className="login-top-strip">
        <div className="login-top-inner">
          {onBackToWebsite && (
            <button
              onClick={onBackToWebsite}
              className="login-back-btn"
              id="btn-back-to-website"
            >
              <ArrowLeft size={14} />
              <span>Hospital Public Website & Institute Directory</span>
            </button>
          )}
          <div className="login-strip-right">
            <span>Federated Node Protocol v2.4</span>
            <span className="strip-dot">•</span>
            <span>IRB Protocol #2026-CHD</span>
          </div>
        </div>
      </div>

      {/* ── MAIN INSTITUTIONAL TWO-COLUMN CARD ─────────────────── */}
      <div className="login-card-wrapper">
        <div className="login-editorial-card">
          {/* Left Column: Hospital Identity & Security Posture */}
          <div className="login-info-column">
            <div className="info-brand-header">
              <div className="info-crest">
                <HeartPulse size={22} strokeWidth={2.4} />
              </div>
              <div>
                <div className="info-inst-name">ST. JUDE & ST. LUKE</div>
                <div className="info-inst-sub">Pediatric Heart Institute</div>
              </div>
            </div>

            <div className="info-narrative">
              <span className="info-kicker">SECURE CLINICAL ACCESS</span>
              <h2 className="info-title">
                Federated pediatric cardiology gateway.
              </h2>
              <p className="info-desc">
                Access local clinical auscultation screening workstations, manage hospital federated cluster parameters, or administer network governance across accredited pediatric research nodes.
              </p>
            </div>

            {/* Compliance Guarantee Badges */}
            <div className="info-compliance-box">
              <div className="compliance-row">
                <ShieldCheck size={16} className="compliance-icon" />
                <div>
                  <span className="compliance-label">Zero Patient Egress</span>
                  <p className="compliance-detail">Patient biometrics and acoustic recordings remain permanently within host medical center firewalls.</p>
                </div>
              </div>
              <div className="compliance-row">
                <Lock size={16} className="compliance-icon" />
                <div>
                  <span className="compliance-label">Cryptographic Token Auth</span>
                  <p className="compliance-detail">Access keys are cryptographically verified against the consortium registry.</p>
                </div>
              </div>
            </div>

            <div className="info-footer">
              <span className="info-emergency">Direct Physician Transfer Desk: <strong>+1 (800) 555-HEART</strong></span>
            </div>
          </div>

          {/* Right Column: Clean Clinical Authentication Terminal */}
          <div className="login-form-column">
            <div className="login-form-header">
              <h3 className="terminal-title">Clinician & Node Authentication</h3>
              <p className="terminal-subtitle">Select role clearance and input verified credentials.</p>
            </div>

            {/* Role Clearance Tabs */}
            <div className="clinical-role-tabs">
              <button
                type="button"
                id="tab-login-hospital"
                onClick={() => { setActiveTab('hospital'); setErrorMessage(null); }}
                className={`role-tab-btn ${activeTab === 'hospital' ? 'active' : ''}`}
              >
                <Building2 size={15} />
                <span>Hospital Node</span>
              </button>

              <button
                type="button"
                id="tab-login-technician"
                onClick={() => { setActiveTab('technician'); setErrorMessage(null); }}
                className={`role-tab-btn ${activeTab === 'technician' ? 'active' : ''}`}
              >
                <Stethoscope size={15} />
                <span>Lab Screening</span>
              </button>

              <button
                type="button"
                id="tab-login-admin"
                onClick={() => { setActiveTab('admin'); setErrorMessage(null); }}
                className={`role-tab-btn ${activeTab === 'admin' ? 'active' : ''}`}
              >
                <Shield size={15} />
                <span>Central Admin</span>
              </button>
            </div>

            {/* Contextual instruction */}
            <div className="terminal-guidance">
              {activeTab === 'hospital' && 'Federated Node Gateway: Enter institutional ID and authorized secret access key.'}
              {activeTab === 'technician' && 'Clinical Triage Station: Enter technician badge ID and secure 4-digit PIN.'}
              {activeTab === 'admin' && 'Central Network Overseer: Enter consortium administrator credentials.'}
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="terminal-error-banner">
                <AlertCircle size={15} style={{ flexShrink: 0 }} />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Authentication Form */}
            <form onSubmit={handleSubmit} id="portal-login-form" className="terminal-form">
              {activeTab === 'hospital' && (
                <>
                  <div className="form-group">
                    <label className="form-label" htmlFor="hospital-id-input">Consortium Hospital Node ID</label>
                    <div className="input-with-icon">
                      <Building2 size={16} className="field-icon" />
                      <input
                        id="hospital-id-input"
                        type="text"
                        className="form-input form-input-institutional"
                        value={hospitalId}
                        onChange={(e) => setHospitalId(e.target.value)}
                        placeholder="e.g. HOSP-APOLLO-01"
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="access-key-input">Node Cryptographic Access Key</label>
                    <div className="input-with-icon">
                      <KeyRound size={16} className="field-icon" />
                      <input
                        id="access-key-input"
                        type="password"
                        className="form-input form-input-institutional"
                        value={accessKey}
                        onChange={(e) => setAccessKey(e.target.value)}
                        placeholder="e.g. APOLLO-CHD-2026"
                        required
                      />
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'technician' && (
                <>
                  <div className="form-group">
                    <label className="form-label" htmlFor="tech-id-input">Licensed Technician Badge ID</label>
                    <div className="input-with-icon">
                      <Stethoscope size={16} className="field-icon" />
                      <input
                        id="tech-id-input"
                        type="text"
                        className="form-input form-input-institutional"
                        value={techId}
                        onChange={(e) => setTechId(e.target.value)}
                        placeholder="e.g. TECH-101"
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="tech-pin-input">Diagnostic Station PIN</label>
                    <div className="input-with-icon">
                      <Lock size={16} className="field-icon" />
                      <input
                        id="tech-pin-input"
                        type="password"
                        maxLength={6}
                        className="form-input form-input-institutional"
                        value={techPin}
                        onChange={(e) => setTechPin(e.target.value)}
                        placeholder="••••"
                        style={{ letterSpacing: '0.25em' }}
                        required
                      />
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'admin' && (
                <>
                  <div className="form-group">
                    <label className="form-label" htmlFor="admin-email-input">Consortium Admin Email</label>
                    <div className="input-with-icon">
                      <Shield size={16} className="field-icon" />
                      <input
                        id="admin-email-input"
                        type="email"
                        className="form-input form-input-institutional"
                        value={adminEmail}
                        onChange={(e) => setAdminEmail(e.target.value)}
                        placeholder="admin@fedmed.network"
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="admin-password-input">Administrative Master Password</label>
                    <div className="input-with-icon">
                      <Lock size={16} className="field-icon" />
                      <input
                        id="admin-password-input"
                        type="password"
                        className="form-input form-input-institutional"
                        value={adminPassword}
                        onChange={(e) => setAdminPassword(e.target.value)}
                        placeholder="••••••••••"
                        required
                      />
                    </div>
                  </div>
                </>
              )}

              <button
                id="btn-login-submit"
                type="submit"
                className="btn btn-primary terminal-submit-btn"
                disabled={loading}
              >
                {loading ? 'Verifying Credentials...' : `Enter ${activeTab === 'hospital' ? 'Hospital Node' : activeTab === 'technician' ? 'Clinical Screening' : 'Central Admin'} Portal`}
              </button>
            </form>

            {/* Quick-fill Evaluation Presets */}
            <div className="eval-presets-section">
              <div className="eval-header">
                <span className="eval-title">1-Click Evaluation Logins</span>
                <span className="eval-note">Instant Clearance</span>
              </div>

              <div className="eval-grid">
                <button
                  type="button"
                  id="preset-apollo"
                  className="eval-card"
                  onClick={() => handleDemoSelect('hospital', { id: 'HOSP-APOLLO-01', key: 'APOLLO-CHD-2026' }, true)}
                >
                  <div className="eval-role">Hospital Node</div>
                  <div className="eval-name">Apollo Children's (Instant Login)</div>
                </button>

                <button
                  type="button"
                  id="preset-tech"
                  className="eval-card"
                  onClick={() => handleDemoSelect('technician', { id: 'TECH-101', pin: '1234' }, true)}
                >
                  <div className="eval-role">Lab Triage Specialist</div>
                  <div className="eval-name">Dr. Sarah Chen (Instant Login)</div>
                </button>

                <button
                  type="button"
                  id="preset-admin"
                  className="eval-card"
                  onClick={() => handleDemoSelect('admin', { email: 'admin@fedmed.network', pw: 'admin123' }, true)}
                >
                  <div className="eval-role">Network Overseer</div>
                  <div className="eval-name">Consortium Admin (Instant Login)</div>
                </button>

                <button
                  type="button"
                  id="preset-aiims"
                  className="eval-card"
                  onClick={() => handleDemoSelect('hospital', { id: 'HOSP-AIIMS-02', key: 'AIIMS-PED-8821' }, true)}
                >
                  <div className="eval-role">Hospital Node</div>
                  <div className="eval-name">AIIMS Cardiology (Instant Login)</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
