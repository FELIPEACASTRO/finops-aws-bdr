/**
 * API Service - FinOps AWS Dashboard
 * 
 * Camada de comunicação com o backend Flask.
 */

const API_BASE = '/api';

export class APIError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      errorData.message || `HTTP Error ${response.status}`,
      response.status
    );
  }
  return response.json();
}

export async function fetchLatestReport() {
  const response = await fetch(`${API_BASE}/v1/reports/latest`);
  return handleResponse(response);
}

export async function startAnalysis(type: 'full' | 'costs_only' | 'recommendations_only') {
  const response = await fetch(`${API_BASE}/v1/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      analysis_type: type, 
      regions: ['us-east-1', 'sa-east-1'] 
    }),
  });
  return handleResponse(response);
}

export async function generateAIReport(provider: string, persona: string) {
  const response = await fetch(`${API_BASE}/v1/ai-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, persona }),
  });
  return handleResponse(response);
}

export async function fetchMultiRegionAnalysis() {
  const response = await fetch(`${API_BASE}/v1/multi-region`);
  return handleResponse(response);
}

export async function exportReport(format: 'csv' | 'json' | 'html') {
  if (format === 'html') {
    window.open(`${API_BASE}/v1/export/html`, '_blank');
    return;
  }
  
  const response = await fetch(`${API_BASE}/v1/export/${format}`);
  const blob = await response.blob();
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `finops_report.${format}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export const api = {
  fetchLatestReport,
  startAnalysis,
  generateAIReport,
  fetchMultiRegionAnalysis,
  exportReport,
};

export default api;
