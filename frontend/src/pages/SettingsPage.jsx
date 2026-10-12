import React, { useState } from 'react';
import { Settings, Building2, Shield, Bell, Key, Save, Globe } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SectionTitle } from '../components/UI';

export default function SettingsPage() {
  const { hospital } = useApp();
  const [saved, setSaved] = useState(false);
  const [notifEmail, setNotifEmail] = useState(true);
  const [notifRound, setNotifRound] = useState(true);
  const [notifModel, setNotifModel] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  const Toggle = ({ id, value, onChange }) => (
    <div
      id={id}
      onClick={() => onChange(!value)}
      style={{
        width: 42, height: 24, borderRadius: 12,
        background: value ? 'var(--brand-primary)' : 'var(--bg-elevated)',
        border: `1px solid ${value ? 'var(--brand-primary)' : 'var(--border-default)'}`,
        cursor: 'pointer', position: 'relative', transition: 'all 0.2s', flexShrink: 0,
      }}
    >
      <div style={{
        width: 18, height: 18, borderRadius: '50%', background: 'white',
        position: 'absolute', top: 2, left: value ? 20 : 2,
        transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
      }} />
    </div>
  );

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your hospital profile, security settings, and notification preferences.</p>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
          {/* Hospital Profile */}
          <div className="card" id="card-hospital-profile">
            <SectionTitle icon={Building2}>Hospital Profile</SectionTitle>
            <div style={{ display: 'flex', align: 'center', gap: 'var(--sp-4)', marginBottom: 'var(--sp-5)' }}>
              <div className="avatar" style={{ width: 56, height: 56, fontSize: 18, flexShrink: 0 }}>{hospital.initials}</div>
              <div>
                <div style={{ fontWeight: 700 }}>{hospital.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{hospital.id}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Joined {new Date(hospital.joinedDate).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Hospital Name</label>
              <input id="input-hospital-name" className="form-input" defaultValue={hospital.name} />
            </div>
            <div className="form-group">
              <label className="form-label">City</label>
              <input id="input-hospital-city" className="form-input" defaultValue={hospital.city} />
            </div>
            <div className="form-group">
              <label className="form-label">Country</label>
              <select id="select-country" className="form-input form-select">
                <option>India</option>
                <option>United States</option>
                <option>United Kingdom</option>
                <option>Germany</option>
                <option>Australia</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Primary Contact Email</label>
              <input id="input-contact-email" className="form-input" type="email" placeholder="admin@yourhospital.org" />
            </div>
          </div>

          {/* FL Client Config */}
          <div className="card" id="card-fl-config">
            <SectionTitle icon={Globe}>FL Client Configuration</SectionTitle>
            <div className="form-group">
              <label className="form-label">Aggregation Server URL</label>
              <input id="input-server-url" className="form-input" defaultValue="http://localhost:8000" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }} />
            </div>
            <div className="form-group">
              <label className="form-label">Client Communication Port</label>
              <input id="input-port" className="form-input" type="number" defaultValue={9000} />
            </div>
            <div className="form-group">
              <label className="form-label">Aggregation Strategy</label>
              <select id="select-strategy" className="form-input form-select">
                <option>FedAvg</option>
                <option>FedProx</option>
                <option>FedNova</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
          {/* Security */}
          <div className="card" id="card-security">
            <SectionTitle icon={Shield}>Security & Privacy</SectionTitle>
            {[
              { label: 'Differential Privacy', desc: 'Apply DP noise to model updates before sharing', on: true },
              { label: 'TLS Encryption', desc: 'Encrypt all communication with the aggregation server', on: true },
              { label: 'Secure Aggregation', desc: 'Use SecAgg protocol for anonymous model updates', on: true },
              { label: 'Audit Logging', desc: 'Log all FL interactions for institutional auditing', on: false },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: 'var(--sp-3) 0', borderBottom: i < 3 ? '1px solid var(--border-subtle)' : 'none' }}>
                <div style={{ flex: 1, paddingRight: 'var(--sp-4)' }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{item.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{item.desc}</div>
                </div>
                <div style={{ width: 42, height: 24, borderRadius: 12, background: item.on ? 'var(--brand-primary)' : 'var(--bg-elevated)', border: `1px solid ${item.on ? 'var(--brand-primary)' : 'var(--border-default)'}`, position: 'relative', flexShrink: 0 }}>
                  <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'white', position: 'absolute', top: 2, left: item.on ? 20 : 2, boxShadow: '0 1px 3px rgba(0,0,0,0.3)' }} />
                </div>
              </div>
            ))}
          </div>

          {/* Notifications */}
          <div className="card" id="card-notifications-settings">
            <SectionTitle icon={Bell}>Notification Preferences</SectionTitle>
            {[
              { id: 'toggle-notif-email', label: 'Email Notifications', desc: 'Receive email updates on training status', value: notifEmail, onChange: setNotifEmail },
              { id: 'toggle-notif-round', label: 'Round Completion Alerts', desc: 'Notify when each FL round completes', value: notifRound, onChange: setNotifRound },
              { id: 'toggle-notif-model', label: 'Global Model Updates', desc: 'Alert when a new global model is released', value: notifModel, onChange: setNotifModel },
            ].map((item, i, arr) => (
              <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: 'var(--sp-3) 0', borderBottom: i < arr.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                <div style={{ flex: 1, paddingRight: 'var(--sp-4)' }}>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{item.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{item.desc}</div>
                </div>
                <Toggle id={item.id} value={item.value} onChange={item.onChange} />
              </div>
            ))}
          </div>

          {/* API Keys */}
          <div className="card" id="card-api-keys">
            <SectionTitle icon={Key}>API Credentials</SectionTitle>
            <div className="form-group">
              <label className="form-label">Hospital API Key</label>
              <input className="form-input" readOnly type="password" placeholder="Not configured" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }} />
            </div>
            <button id="btn-regenerate-key" className="btn btn-secondary btn-sm">Regenerate Key</button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--sp-3)', marginTop: 'var(--sp-6)' }}>
        <button className="btn btn-secondary">Discard Changes</button>
        <button id="btn-save-settings" className="btn btn-primary" onClick={handleSave}>
          {saved ? <><span>✓</span> Saved!</> : <><Save size={15} /> Save Settings</>}
        </button>
      </div>
    </div>
  );
}
