/**
 * React hooks for fetching and polling API data.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from './client';

// ── Generic one-shot fetch ────────────────────────────────────────────────────

/**
 * Fetch once on mount (or when `deps` change).
 * Returns { data, loading, error, refetch }.
 */
export function useApiFetch(fetchFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (e) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetch_();
  }, [fetch_]);

  return { data, loading, error, refetch: fetch_ };
}

// ── Generic polling hook ──────────────────────────────────────────────────────

/**
 * Poll `fetchFn` every `intervalMs` milliseconds.
 * Returns { data, loading, error }.
 */
export function useApiPolling(fetchFn, intervalMs = 3000, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetch_ = useCallback(async () => {
    try {
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetch_(); // immediate first call
    timerRef.current = setInterval(fetch_, intervalMs);
    return () => clearInterval(timerRef.current);
  }, [fetch_, intervalMs]);

  return { data, loading, error };
}

// ── Domain-specific hooks ─────────────────────────────────────────────────────

/** Fetch hospital info once. */
export function useHospital() {
  return useApiFetch(() => api.hospital());
}

/** Fetch cluster list + poll every 5 s for status updates. */
export function useClusters() {
  return useApiPolling(() => api.clusters(), 5000);
}

/** Poll training status every 2 s. */
export function useTrainingStatus() {
  return useApiPolling(() => api.trainingStatus(), 2000);
}

/** Poll training logs every 2 s. */
export function useTrainingLogs() {
  return useApiPolling(() => api.trainingLogs(150), 2000);
}

/** Poll notifications every 5 s. */
export function useNotifications() {
  return useApiPolling(() => api.notifications(), 5000);
}

/** Fetch saved results once. */
export function useResults() {
  return useApiFetch(() => api.results());
}
