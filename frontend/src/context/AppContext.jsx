import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const AppContext = createContext(null);

const STORAGE_KEY = 'fedmed_auth_user_session';

export function AppProvider({ children }) {
  // ── Authentication state ───────────────────────────────────────────────────
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // ── Hospital & Clusters state ──────────────────────────────────────────────
  const [hospital, setHospital] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const hospitalId = currentUser?.role === 'hospital' ? currentUser.hospital_id : (currentUser?.hospital_id || '');

  // ── Fetch hospital details & clusters ──────────────────────────────────────
  const refreshHospitalData = useCallback(async () => {
    if (!currentUser) return;
    setIsLoading(true);
    try {
      if (currentUser.role === 'hospital') {
        const hData = await api.hospital(hospitalId);
        setHospital(hData);
        const cData = await api.clusters(hospitalId);
        setClusters(cData || []);
      } else if (currentUser.role === 'technician') {
        const hData = await api.hospital(currentUser.hospital_id);
        setHospital(hData);
      }
      const nData = await api.notifications();
      setNotifications(nData || []);
    } catch (e) {
      console.error('Failed refreshing data:', e);
    } finally {
      setIsLoading(false);
    }
  }, [currentUser, hospitalId]);

  useEffect(() => {
    refreshHospitalData();
  }, [refreshHospitalData]);

  // Periodic poll for cluster status if hospital user
  useEffect(() => {
    if (!currentUser || currentUser.role !== 'hospital') return;
    const interval = setInterval(async () => {
      try {
        const cData = await api.clusters(hospitalId);
        setClusters(cData || []);
        const nData = await api.notifications();
        setNotifications(nData || []);
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 6000);
    return () => clearInterval(interval);
  }, [currentUser, hospitalId]);

  // ── Auth Actions ───────────────────────────────────────────────────────────
  function login(userData) {
    setCurrentUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
  }

  function logout() {
    setCurrentUser(null);
    setHospital(null);
    setClusters([]);
    localStorage.removeItem(STORAGE_KEY);
  }

  // ── Cluster Actions (Authenticated with current Hospital ID) ───────────────
  async function joinCluster(clusterId, datasetPath) {
    try {
      await api.joinCluster(clusterId, datasetPath, hospitalId);
      await refreshHospitalData();
    } catch (e) {
      console.error('joinCluster failed:', e);
      throw e;
    }
  }

  async function leaveCluster(clusterId) {
    try {
      await api.leaveCluster(clusterId, hospitalId);
      await refreshHospitalData();
    } catch (e) {
      console.error('leaveCluster failed:', e);
      throw e;
    }
  }

  // Safe defaults
  const safeHospital = hospital ?? {
    id: currentUser?.hospital_id || 'LOCAL',
    name: currentUser?.hospital_name || currentUser?.name || 'Local Hospital Node',
    city: currentUser?.city || 'Chennai',
    country: 'India',
    status: 'active',
    joinedDate: '2026-01-01',
    contributionScore: 88,
    patientsContributed: 1200,
    roundsParticipated: 36,
    initials: 'HN',
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        login,
        logout,
        hospital: safeHospital,
        clusters,
        notifications,
        isLoading,
        joinCluster,
        leaveCluster,
        refreshHospitalData,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
