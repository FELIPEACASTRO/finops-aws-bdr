/**
 * Type Definitions - FinOps AWS Dashboard
 * 
 * Tipos TypeScript para toda a aplicação.
 */

export interface CostData {
  total: number;
  byService: Record<string, number>;
  by_service?: Record<string, number>;
  period: {
    start: string;
    end: string;
  };
}

export interface Recommendation {
  id?: string;
  type: string;
  title: string;
  description?: string;
  resource_id: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  savings: number;
  service?: string;
  action?: string;
}

export interface AnalysisReport {
  account_id: string;
  timestamp?: string;
  status: string;
  details: {
    costs: CostData;
    recommendations: Recommendation[];
  };
  summary?: {
    total_cost: number;
    total_savings_potential: number;
    services_analyzed: number;
    recommendations_count: number;
  };
}

export interface AIReport {
  provider: string;
  model: string;
  content: string;
  tokens_used: number;
  latency_ms: number;
  metadata?: Record<string, unknown>;
}

export interface MultiRegionData {
  summary: {
    total_regions: number;
    regions_with_resources: number;
    total_cost: number;
    total_potential_savings: number;
    total_recommendations: number;
  };
  regions: Record<string, RegionData>;
}

export interface RegionData {
  cost: number;
  resources: number;
  recommendations: number;
  services: string[];
}

export interface ServiceCost {
  name: string;
  cost: number;
  percentage: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
}

export interface DashboardStats {
  totalCost: number;
  potentialSavings: number;
  servicesAnalyzed: number;
  recommendationsCount: number;
  lastUpdated: string;
}

export interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: number;
}

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface APIResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  report?: T;
}
