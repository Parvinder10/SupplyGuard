import {
  ExecutiveKPIs,
  SupplierScorecard,
  MaterialOut,
  PurchaseOrderOut,
  AlertOut,
  CorrectiveActionOut,
  CorrectiveActionCreate,
  ETLAuditLogOut,
  ETLRejectedRecordOut,
  DataQualityTestOut
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  getKPIs: () => fetchJson<ExecutiveKPIs>('/kpis'),
  
  getSuppliers: (params?: { tier?: string; category?: string; risk_tier?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.tier) query.set('tier', params.tier);
    if (params?.category) query.set('category', params.category);
    if (params?.risk_tier) query.set('risk_tier', params.risk_tier);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return fetchJson<SupplierScorecard[]>(`/suppliers${qs ? `?${qs}` : ''}`);
  },

  getSupplierById: (id: string) => fetchJson<SupplierScorecard>(`/suppliers/${id}`),

  getMaterials: (params?: { category?: string; risk_tier?: string; is_critical?: boolean; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.risk_tier) query.set('risk_tier', params.risk_tier);
    if (params?.is_critical !== undefined) query.set('is_critical', String(params.is_critical));
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return fetchJson<MaterialOut[]>(`/materials${qs ? `?${qs}` : ''}`);
  },

  getPurchaseOrders: (params?: { status?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return fetchJson<PurchaseOrderOut[]>(`/purchase-orders${qs ? `?${qs}` : ''}`);
  },

  getAlerts: (params?: { severity?: string; alert_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.severity) query.set('severity', params.severity);
    if (params?.alert_type) query.set('alert_type', params.alert_type);
    const qs = query.toString();
    return fetchJson<AlertOut[]>(`/alerts${qs ? `?${qs}` : ''}`);
  },

  updateAlertStatus: (alertId: string, status: string) => {
    return fetchJson<AlertOut>(`/alerts/${alertId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  },

  getCorrectiveActions: (status?: string) => {
    return fetchJson<CorrectiveActionOut[]>(`/corrective-actions${status ? `?status=${status}` : ''}`);
  },

  createCorrectiveAction: (payload: CorrectiveActionCreate) => {
    return fetchJson<CorrectiveActionOut>('/corrective-actions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  updateCorrectiveAction: (actionId: string, payload: Partial<CorrectiveActionOut>) => {
    return fetchJson<CorrectiveActionOut>(`/corrective-actions/${actionId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
  },

  getETLAuditLogs: () => fetchJson<ETLAuditLogOut[]>('/etl/audit-logs'),
  getETLRejectedRecords: () => fetchJson<ETLRejectedRecordOut[]>('/etl/rejected-records'),
  getDataQualityResults: () => fetchJson<DataQualityTestOut[]>('/etl/data-quality'),
  
  triggerRiskScoring: () => fetchJson<{ status: string }>('/risk/run-scoring', { method: 'POST' })
};
