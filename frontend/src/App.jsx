import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import LoginPage from './pages/LoginPage';
import HospitalWebsitePage from './pages/HospitalWebsitePage';

// Hospital Pages
import DashboardPage from './pages/DashboardPage';
import ClustersPage from './pages/ClustersPage';
import DataPage from './pages/DataPage';
import TrainingPage from './pages/TrainingPage';
import SettingsPage from './pages/SettingsPage';

// Clinical / Lab Technician Pages
import ScreeningPage from './pages/ScreeningPage';
import ReportPage from './pages/ReportPage';
import HistoryPage from './pages/HistoryPage';

// Admin Pages
import AdminHospitalsPage from './pages/admin/AdminHospitalsPage';
import AdminClustersPage from './pages/admin/AdminClustersPage';

function AppShell({ onLogout, role }) {
  return (
    <div className="app-layout">
      <Sidebar onLogout={onLogout} />
      <div className="main-content">
        <Topbar />
        <Routes>
          {/* ── PUBLIC INSTITUTIONAL OVERVIEW (Available to all logged-in roles) ── */}
          <Route path="/institute" element={<HospitalWebsitePage onGoToPortal={() => {}} />} />

          {/* ── ADMIN ROUTES ────────────────────────────────────────── */}
          {role === 'admin' && (
            <>
              <Route path="/" element={<Navigate to="/admin/hospitals" replace />} />
              <Route path="/admin" element={<Navigate to="/admin/hospitals" replace />} />
              <Route path="/admin/hospitals" element={<AdminHospitalsPage />} />
              <Route path="/admin/clusters" element={<AdminClustersPage />} />
              <Route path="*" element={<Navigate to="/admin/hospitals" replace />} />
            </>
          )}

          {/* ── HOSPITAL NODE ROUTES ────────────────────────────────── */}
          {role === 'hospital' && (
            <>
              <Route path="/" element={<Navigate to="/hospital/dashboard" replace />} />
              <Route path="/hospital" element={<Navigate to="/hospital/dashboard" replace />} />
              <Route path="/hospital/dashboard" element={<DashboardPage />} />
              <Route path="/hospital/clusters" element={<ClustersPage />} />
              <Route path="/hospital/data" element={<DataPage />} />
              <Route path="/hospital/training" element={<TrainingPage />} />
              <Route path="/hospital/settings" element={<SettingsPage />} />

              {/* Legacy Aliases */}
              <Route path="/dashboard" element={<Navigate to="/hospital/dashboard" replace />} />
              <Route path="/clusters" element={<Navigate to="/hospital/clusters" replace />} />
              <Route path="/data" element={<Navigate to="/hospital/data" replace />} />
              <Route path="/training" element={<Navigate to="/hospital/training" replace />} />
              <Route path="/settings" element={<Navigate to="/hospital/settings" replace />} />

              <Route path="*" element={<Navigate to="/hospital/dashboard" replace />} />
            </>
          )}

          {/* ── LAB TECHNICIAN CLINICAL ROUTES ─────────────────────── */}
          {role === 'technician' && (
            <>
              <Route path="/" element={<Navigate to="/technician/screening" replace />} />
              <Route path="/technician" element={<Navigate to="/technician/screening" replace />} />
              <Route path="/technician/screening" element={<ScreeningPage />} />
              <Route path="/technician/report/:id" element={<ReportPage />} />
              <Route path="/technician/history" element={<HistoryPage />} />

              {/* Legacy Aliases */}
              <Route path="/screening" element={<Navigate to="/technician/screening" replace />} />
              <Route path="/screening/report/:id" element={<ReportPage />} />
              <Route path="/screening/history" element={<Navigate to="/technician/history" replace />} />

              <Route path="*" element={<Navigate to="/technician/screening" replace />} />
            </>
          )}

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}

function MainContent() {
  const { currentUser, login, logout } = useApp();
  const [unauthView, setUnauthView] = useState('website'); // 'website' | 'login'

  if (!currentUser) {
    if (unauthView === 'login') {
      return (
        <LoginPage
          onLogin={login}
          onBackToWebsite={() => setUnauthView('website')}
        />
      );
    }
    return (
      <HospitalWebsitePage
        onGoToPortal={() => setUnauthView('login')}
      />
    );
  }

  return <AppShell onLogout={logout} role={currentUser.role} />;
}

export default function App() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
}
