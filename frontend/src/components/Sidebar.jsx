import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Network,
  Database,
  Activity,
  Settings,
  LogOut,
  HeartPulse,
  Stethoscope,
  ClipboardList,
  Building2,
  Globe,
  Shield,
  ShieldCheck,
  ExternalLink
} from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function Sidebar({ onLogout }) {
  const { currentUser, hospital, clusters, notifications } = useApp();
  const joinedCount = clusters.filter((c) => c.joined).length;

  const role = currentUser?.role || 'hospital';

  return (
    <aside className="sidebar">
      {/* Institutional Crest & Brand */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <HeartPulse size={18} color="white" strokeWidth={2.4} />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">St. Jude Pediatric Heart</span>
          <span className="sidebar-logo-tagline">
            {role === 'admin' && 'Central Admin Portal'}
            {role === 'technician' && 'Clinical Triage Station'}
            {role === 'hospital' && 'Hospital Node Gateway'}
          </span>
        </div>
      </div>

      {/* Role Navigation */}
      <nav className="sidebar-nav">
        {/* ── PUBLIC WEBSITE JUMP ─────────────── */}
        <span className="nav-section-label">
          Institutional Platform
        </span>
        <NavLink
          to="/institute"
          id="nav-institute"
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          <span className="nav-item-icon">
            <Globe size={16} />
          </span>
          <span>Hospital Public Website</span>
        </NavLink>

        {/* ── ADMIN NAV ──────────────────────── */}
        {role === 'admin' && (
          <>
            <span className="nav-section-label">
              Network Governance
            </span>
            <NavLink
              to="/admin/hospitals"
              id="nav-admin-hospitals"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Building2 size={16} />
              </span>
              <span>Hospital Registry</span>
            </NavLink>

            <NavLink
              to="/admin/clusters"
              id="nav-admin-clusters"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Network size={16} />
              </span>
              <span>Cluster Overseer</span>
            </NavLink>
          </>
        )}

        {/* ── HOSPITAL NAV ───────────────────── */}
        {role === 'hospital' && (
          <>
            <span className="nav-section-label">
              Federated Learning
            </span>
            <NavLink
              to="/hospital/dashboard"
              id="nav-dashboard"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <LayoutDashboard size={16} />
              </span>
              <span>Node Dashboard</span>
              {notifications.length > 0 && (
                <span className="nav-item-badge" style={{ background: 'var(--brand-danger)' }}>
                  {notifications.length}
                </span>
              )}
            </NavLink>

            <NavLink
              to="/hospital/clusters"
              id="nav-clusters"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Network size={16} />
              </span>
              <span>Cluster Management</span>
              {joinedCount > 0 && <span className="nav-item-badge">{joinedCount}</span>}
            </NavLink>

            <NavLink
              to="/hospital/data"
              id="nav-data"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Database size={16} />
              </span>
              <span>Data Configuration</span>
            </NavLink>

            <NavLink
              to="/hospital/training"
              id="nav-training"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Activity size={16} />
              </span>
              <span>Training Status</span>
            </NavLink>

            <NavLink
              to="/hospital/settings"
              id="nav-settings"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Settings size={16} />
              </span>
              <span>Hospital Settings</span>
            </NavLink>
          </>
        )}

        {/* ── TECHNICIAN NAV ─────────────────── */}
        {role === 'technician' && (
          <>
            <span className="nav-section-label">
              Clinical Auscultation & Echo
            </span>
            <NavLink
              to="/technician/screening"
              id="nav-screening"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <Stethoscope size={16} />
              </span>
              <span>Patient Screening</span>
            </NavLink>

            <NavLink
              to="/technician/history"
              id="nav-screening-history"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-item-icon">
                <ClipboardList size={16} />
              </span>
              <span>Screening Audit Log</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* Footer Profile */}
      <div className="sidebar-footer">
        <div className="sidebar-hospital-info" id="sidebar-hospital-info">
          <div className="avatar">
            {role === 'admin' ? 'AD' : role === 'technician' ? 'LT' : hospital.initials}
          </div>
          <div className="hospital-info-text">
            <div className="hospital-name" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 140 }}>
              {role === 'admin'
                ? 'Super Admin'
                : role === 'technician'
                ? currentUser?.name || 'Lab Specialist'
                : hospital.name}
            </div>
            <div className="hospital-id">
              {role === 'admin'
                ? 'admin@fedmed'
                : role === 'technician'
                ? currentUser?.hospital_name || hospital.name
                : hospital.id}
            </div>
          </div>
        </div>

        <button
          id="btn-logout"
          className="btn btn-ghost w-full mt-2"
          style={{ justifyContent: 'flex-start', color: '#8BA2BC', fontSize: 12.5 }}
          onClick={onLogout}
        >
          <LogOut size={15} />
          Sign Out of Node
        </button>
      </div>
    </aside>
  );
}
