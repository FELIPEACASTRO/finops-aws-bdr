import { useState, useCallback } from 'react';

const API_BASE = '/api';

interface UseFetchResult {
  loading: boolean;
  error: string | null;
  get: <T>(url: string) => Promise<T | null>;
  post: <T>(url: string, data: unknown) => Promise<T | null>;
  put: <T>(url: string, data: unknown) => Promise<T | null>;
}

export function useFetch(): UseFetchResult {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const get = useCallback(async <T>(url: string): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url.startsWith('/') ? url : `${API_BASE}${url}`);
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }
      const data = await response.json();
      return data as T;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const post = useCallback(async <T>(url: string, data: unknown): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url.startsWith('/') ? url : `${API_BASE}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }
      const result = await response.json();
      return result as T;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const put = useCallback(async <T>(url: string, data: unknown): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url.startsWith('/') ? url : `${API_BASE}${url}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }
      const result = await response.json();
      return result as T;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, get, post, put };
}

export default useFetch;
