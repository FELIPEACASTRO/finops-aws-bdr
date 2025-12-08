import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { AnalysisReport, DashboardStats, ServiceCost, Recommendation } from '../types';

interface UseDashboardResult {
  stats: DashboardStats | null;
  services: ServiceCost[];
  recommendations: Recommendation[];
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  runAnalysis: (type: 'full' | 'costs_only' | 'recommendations_only') => Promise<void>;
}

export function useDashboard(): UseDashboardResult {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [services, setServices] = useState<ServiceCost[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const parseReport = useCallback((data: { report: AnalysisReport | null }) => {
    if (!data.report) {
      setStats(null);
      setServices([]);
      setRecommendations([]);
      return;
    }
    
    const report = data.report;
    const details = report.details || {};
    const costData = details.costs || { total: 0, byService: {}, period: { start: '', end: '' } };
    const recsData = details.recommendations || [];
    
    const byService = costData.by_service || costData.byService || {};
    const total = costData.total || Object.values(byService).reduce((sum: number, cost) => sum + (cost as number), 0);
    
    const savings = recsData.reduce((sum: number, rec: Recommendation) => sum + (rec.savings || 0), 0);
    
    const servicesList: ServiceCost[] = Object.entries(byService)
      .map(([name, cost]) => ({
        name,
        cost: cost as number,
        percentage: total > 0 ? ((cost as number) / total) * 100 : 0,
        trend: 'STABLE' as const,
        status: 'HEALTHY' as const,
      }))
      .sort((a, b) => b.cost - a.cost)
      .slice(0, 10);

    setStats({
      totalCost: total,
      potentialSavings: savings,
      servicesAnalyzed: Object.keys(byService).length,
      recommendationsCount: recsData.length,
      lastUpdated: new Date().toLocaleString('pt-BR'),
    });

    setServices(servicesList);
    setRecommendations(recsData);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const data = await api.fetchLatestReport();
      parseReport(data as { report: AnalysisReport });
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Erro ao carregar dados'));
    } finally {
      setIsLoading(false);
    }
  }, [parseReport]);

  const runAnalysis = useCallback(async (type: 'full' | 'costs_only' | 'recommendations_only') => {
    try {
      setIsLoading(true);
      setError(null);
      
      await api.startAnalysis(type);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Erro na análise'));
      setIsLoading(false);
    }
  }, [refresh]);

  useEffect(() => {
    let mounted = true;
    
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const data = await api.fetchLatestReport();
        
        if (mounted) {
          parseReport(data as { report: AnalysisReport });
          setIsLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err : new Error('Erro ao carregar dados'));
          setIsLoading(false);
        }
      }
    };
    
    loadData();
    
    return () => {
      mounted = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    stats,
    services,
    recommendations,
    isLoading,
    error,
    refresh,
    runAnalysis,
  };
}

export default useDashboard;
