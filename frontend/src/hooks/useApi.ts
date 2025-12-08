import { useState, useCallback } from 'react';
import type { LoadingState } from '../types';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseApiResult<T, Args extends unknown[]> {
  data: T | null;
  error: Error | null;
  status: LoadingState;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T, Args extends unknown[] = []>(
  apiFunction: (...args: Args) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiResult<T, Args> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [status, setStatus] = useState<LoadingState>('idle');

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      try {
        setStatus('loading');
        setError(null);
        
        const result = await apiFunction(...args);
        
        setData(result);
        setStatus('success');
        options.onSuccess?.(result);
        
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Erro desconhecido');
        setError(error);
        setStatus('error');
        options.onError?.(error);
        
        return null;
      }
    },
    [apiFunction, options]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setStatus('idle');
  }, []);

  return {
    data,
    error,
    status,
    isLoading: status === 'loading',
    isSuccess: status === 'success',
    isError: status === 'error',
    execute,
    reset,
  };
}

export default useApi;
