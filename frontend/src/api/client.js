/**
 * Central API client for the FL Pediatric CHD backend.
 * All requests go through here so the base URL is set in one place.
 *
 * In development, Vite proxies /api/* → http://localhost:8000 via vite.config.js
 * so we use a relative path here (works for both dev and prod build).
 */

const BASE = '/api';

/**
 * Fetch wrapper — returns parsed JSON or throws an Error with a readable message.
 */
export async function apiFetch(path, options = {}) {
  const url = `${BASE}${path}`;
  const isFormData = options.body instanceof FormData;
  const headers = { ...options.headers };
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status} on ${path}: ${text}`);
  }

  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    return res.json();
  }
  return res.text();
}

// ── Convenience wrappers ──────────────────────────────────────────────────────

export const api = {
  /** GET /api/status */
  status: () => apiFetch('/status'),

  // ── Authentication ──
  /** POST /api/auth/login */
  login: (credentials) =>
    apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  // ── Admin Management Endpoints ──
  /** GET /api/admin/metrics */
  adminMetrics: () => apiFetch('/admin/metrics'),

  /** GET /api/admin/hospitals */
  adminHospitals: () => apiFetch('/admin/hospitals'),

  /** POST /api/admin/hospitals */
  adminCreateHospital: (payload) =>
    apiFetch('/admin/hospitals', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** PATCH /api/admin/hospitals/:id/status */
  adminUpdateHospitalStatus: (id, status) =>
    apiFetch(`/admin/hospitals/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  /** POST /api/admin/hospitals/:id/regenerate-key */
  adminRegenerateKey: (id) =>
    apiFetch(`/admin/hospitals/${id}/regenerate-key`, {
      method: 'POST',
    }),

  /** DELETE /api/admin/hospitals/:id */
  adminDeleteHospital: (id) =>
    apiFetch(`/admin/hospitals/${id}`, {
      method: 'DELETE',
    }),

  /** GET /api/admin/technicians */
  adminTechnicians: (hospitalId = '') =>
    apiFetch(`/admin/technicians${hospitalId ? `?hospital_id=${hospitalId}` : ''}`),

  // ── Hospital & Node Endpoints ──
  /** GET /api/hospital */
  hospital: (hospitalId = '') =>
    apiFetch(`/hospital${hospitalId ? `?hospital_id=${hospitalId}` : ''}`),

  /** GET /api/hospital/profile */
  hospitalProfile: (hospitalId) =>
    apiFetch(`/hospital/profile?hospital_id=${encodeURIComponent(hospitalId)}`),

  /** GET /api/clusters */
  clusters: (hospitalId = '') =>
    apiFetch(`/clusters${hospitalId ? `?hospital_id=${hospitalId}` : ''}`),

  /** GET /api/clusters/:id/metrics */
  clusterMetrics: (id) => apiFetch(`/clusters/${id}/metrics`),

  /** POST /api/clusters/:id/join */
  joinCluster: (id, datasetPath = '', hospitalId = '') =>
    apiFetch(
      `/clusters/${id}/join?dataset_path=${encodeURIComponent(datasetPath)}${
        hospitalId ? `&hospital_id=${encodeURIComponent(hospitalId)}` : ''
      }`,
      { method: 'POST' }
    ),

  /** POST /api/data/validate */
  validateDataset: (clusterId, path = '') =>
    apiFetch(`/data/validate?cluster_id=${encodeURIComponent(clusterId)}&path=${encodeURIComponent(path)}`, {
      method: 'POST',
    }),

  /** POST /api/clusters/:id/leave */
  leaveCluster: (id, hospitalId = '') =>
    apiFetch(
      `/clusters/${id}/leave${hospitalId ? `?hospital_id=${encodeURIComponent(hospitalId)}` : ''}`,
      { method: 'POST' }
    ),

  /** GET /api/training/status */
  trainingStatus: () => apiFetch('/training/status'),

  /** GET /api/training/logs */
  trainingLogs: (limit = 100) => apiFetch(`/training/logs?limit=${limit}`),

  /** POST /api/training/start/:clusterId */
  startTraining: (clusterId) =>
    apiFetch(`/training/start/${clusterId}`, { method: 'POST' }),

  /** POST /api/training/stop */
  stopTraining: () => apiFetch('/training/stop', { method: 'POST' }),

  /** GET /api/results */
  results: () => apiFetch('/results'),

  /** GET /api/notifications */
  notifications: () => apiFetch('/notifications'),

  // ── Screening & Triage Endpoints ──
  /** GET /api/screening/demo-samples */
  demoSamples: () => apiFetch('/screening/demo-samples'),

  /** POST /api/screening/upload */
  uploadScreening: (formData) =>
    apiFetch('/screening/upload', {
      method: 'POST',
      body: formData,
    }),

  /** GET /api/screening/reports */
  screeningReports: () => apiFetch('/screening/reports'),

  /** GET /api/screening/reports/:id */
  screeningReport: (id) => apiFetch(`/screening/reports/${id}`),

  /** POST /api/screening/reports/:id/escalate */
  escalateReport: (id, payload = {}) =>
    apiFetch(`/screening/reports/${id}/escalate`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** POST /api/screening/reports/:id/dismiss */
  dismissReport: (id, payload = {}) =>
    apiFetch(`/screening/reports/${id}/dismiss`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  audioUrl: (id) => `${BASE}/screening/audio/${id}`,
  frameUrl: (id, type) => `${BASE}/screening/frames/${id}/${type}`,
};
