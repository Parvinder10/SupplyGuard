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
import seedData from './seedData.json';

const API_BASE = '/api/v1';

// In-memory mutable fallback store for standalone Vercel preview deployment
let fallbackStore = {
  kpis: (seedData.kpis as unknown) as ExecutiveKPIs,
  suppliers: (seedData.suppliers as unknown) as SupplierScorecard[],
  materials: (seedData.materials as unknown) as MaterialOut[],
  orders: (seedData.orders as unknown) as PurchaseOrderOut[],
  alerts: (seedData.alerts as unknown) as AlertOut[],
  actions: (seedData.actions as unknown) as CorrectiveActionOut[],
  auditLogs: (seedData.auditLogs as unknown) as ETLAuditLogOut[],
  rejectedRecords: (seedData.rejectedRecords as unknown) as ETLRejectedRecordOut[],
  dqResults: (seedData.dqResults as unknown) as DataQualityTestOut[]
};

async function fetchJson<T>(endpoint: string, fallback: () => T, options?: RequestInit): Promise<T> {
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
      return fallback();
    }
    return await res.json();
  } catch (error) {
    // Graceful fallback for standalone Vercel deployment
    return fallback();
  }
}

export const api = {
  getKPIs: () => 
    fetchJson<ExecutiveKPIs>('/kpis', () => fallbackStore.kpis),
  
  getSuppliers: (params?: { tier?: string; category?: string; risk_tier?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.tier) query.set('tier', params.tier);
    if (params?.category) query.set('category', params.category);
    if (params?.risk_tier) query.set('risk_tier', params.risk_tier);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    
    return fetchJson<SupplierScorecard[]>(`/suppliers${qs ? `?${qs}` : ''}`, () => {
      let result = [...fallbackStore.suppliers];
      if (params?.tier) result = result.filter(s => s.tier === params.tier);
      if (params?.category) result = result.filter(s => s.category === params.category);
      if (params?.risk_tier) result = result.filter(s => s.risk_tier === params.risk_tier);
      if (params?.search) {
        const q = params.search.toLowerCase();
        result = result.filter(s => s.name.toLowerCase().includes(q) || s.code.toLowerCase().includes(q));
      }
      return result;
    });
  },

  getSupplierById: (id: string) => 
    fetchJson<SupplierScorecard>(`/suppliers/${id}`, () => {
      const found = fallbackStore.suppliers.find(s => s.supplier_id === id);
      if (!found) throw new Error("Supplier not found");
      return found;
    }),

  getMaterials: (params?: { category?: string; risk_tier?: string; is_critical?: boolean; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.risk_tier) query.set('risk_tier', params.risk_tier);
    if (params?.is_critical !== undefined) query.set('is_critical', String(params.is_critical));
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();

    return fetchJson<MaterialOut[]>(`/materials${qs ? `?${qs}` : ''}`, () => {
      let result = [...fallbackStore.materials];
      if (params?.category) result = result.filter(m => m.category === params.category);
      if (params?.risk_tier) result = result.filter(m => m.risk_tier === params.risk_tier);
      if (params?.is_critical !== undefined) result = result.filter(m => m.is_critical === params.is_critical);
      if (params?.search) {
        const q = params.search.toLowerCase();
        result = result.filter(m => m.name.toLowerCase().includes(q) || m.sku.toLowerCase().includes(q));
      }
      return result;
    });
  },

  getPurchaseOrders: (params?: { status?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();

    return fetchJson<PurchaseOrderOut[]>(`/purchase-orders${qs ? `?${qs}` : ''}`, () => {
      let result = [...fallbackStore.orders];
      if (params?.status) result = result.filter(o => o.status === params.status);
      if (params?.search) {
        const q = params.search.toLowerCase();
        result = result.filter(o => o.po_number.toLowerCase().includes(q) || o.supplier_name.toLowerCase().includes(q));
      }
      return result;
    });
  },

  getAlerts: (params?: { severity?: string; alert_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.severity) query.set('severity', params.severity);
    if (params?.alert_type) query.set('alert_type', params.alert_type);
    const qs = query.toString();

    return fetchJson<AlertOut[]>(`/alerts${qs ? `?${qs}` : ''}`, () => {
      let result = [...fallbackStore.alerts];
      if (params?.severity) result = result.filter(a => a.severity === params.severity);
      if (params?.alert_type) result = result.filter(a => a.alert_type === params.alert_type);
      return result;
    });
  },

  updateAlertStatus: (alertId: string, status: string) => {
    return fetchJson<AlertOut>(
      `/alerts/${alertId}`,
      () => {
        const alt = fallbackStore.alerts.find(a => a.alert_id === alertId);
        if (alt) {
          alt.status = status as any;
          if (status === 'RESOLVED') {
            alt.resolved_at = new Date().toISOString();
          }
          return alt;
        }
        throw new Error("Alert not found");
      },
      {
        method: 'PATCH',
        body: JSON.stringify({ status })
      }
    );
  },

  getCorrectiveActions: (status?: string) => {
    return fetchJson<CorrectiveActionOut[]>(
      `/corrective-actions${status ? `?status=${status}` : ''}`,
      () => {
        if (status) return fallbackStore.actions.filter(a => a.status === status);
        return fallbackStore.actions;
      }
    );
  },

  createCorrectiveAction: (payload: CorrectiveActionCreate) => {
    return fetchJson<CorrectiveActionOut>(
      '/corrective-actions',
      () => {
        const now = new Date().toISOString();
        const newAct: CorrectiveActionOut = {
          action_id: `CA-2026-${String(fallbackStore.actions.length + 1).padStart(4, '0')}`,
          alert_id: payload.alert_id,
          title: payload.title,
          description: payload.description,
          assigned_to: payload.assigned_to,
          priority: payload.priority as any,
          status: 'OPEN',
          root_cause: payload.root_cause,
          mitigation_plan: payload.mitigation_plan,
          created_at: now,
          updated_at: now
        };
        fallbackStore.actions.unshift(newAct);
        return newAct;
      },
      {
        method: 'POST',
        body: JSON.stringify(payload)
      }
    );
  },

  updateCorrectiveAction: (actionId: string, payload: Partial<CorrectiveActionOut>) => {
    return fetchJson<CorrectiveActionOut>(
      `/corrective-actions/${actionId}`,
      () => {
        const act = fallbackStore.actions.find(a => a.action_id === actionId);
        if (act) {
          Object.assign(act, payload, { updated_at: new Date().toISOString() });
          if (payload.status === 'RESOLVED' && !act.resolved_at) {
            act.resolved_at = new Date().toISOString();
          }
          return act;
        }
        throw new Error("Action not found");
      },
      {
        method: 'PATCH',
        body: JSON.stringify(payload)
      }
    );
  },

  getETLAuditLogs: () => 
    fetchJson<ETLAuditLogOut[]>('/etl/audit-logs', () => fallbackStore.auditLogs),
  
  getETLRejectedRecords: () => 
    fetchJson<ETLRejectedRecordOut[]>('/etl/rejected-records', () => fallbackStore.rejectedRecords),
  
  getDataQualityResults: () => 
    fetchJson<DataQualityTestOut[]>('/etl/data-quality', () => fallbackStore.dqResults),
  
  triggerRiskScoring: () => 
    fetchJson<{ status: string }>('/risk/run-scoring', () => ({ status: 'COMPLETED' }), { method: 'POST' })
};
