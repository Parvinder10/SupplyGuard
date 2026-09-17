export interface ExecutiveKPIs {
  on_time_delivery_rate: number;
  total_spend_at_risk_usd: number;
  active_stockouts_count: number;
  total_inventory_valuation_usd: number;
  average_days_of_inventory: number;
  high_risk_suppliers_count: number;
  active_alerts_count: number;
  open_corrective_actions_count: number;
}

export interface ContributingFactor {
  feature: string;
  impact_percentage: number;
  raw_value: number;
}

export interface SupplierScorecard {
  supplier_id: string;
  code: string;
  name: string;
  category: string;
  country: string;
  city: string;
  tier: 'TIER_1' | 'TIER_2' | 'TIER_3';
  reliability_rating: number;
  financial_health_score: number;
  otd_percentage: number;
  avg_lead_time_variance_days: number;
  lead_time_variance_std: number;
  overall_defect_ppm: number;
  total_spend: number;
  overdue_spend: number;
  risk_score: number;
  risk_tier: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  top_contributing_factors: ContributingFactor[];
  explanation_text: string;
}

export interface MaterialOut {
  material_id: string;
  sku: string;
  name: string;
  category: string;
  unit_of_measure: string;
  standard_cost: number;
  safety_stock_level: number;
  reorder_point: number;
  current_stock: number;
  days_of_inventory: number;
  stock_health_status: 'STOCKOUT' | 'SAFETY_STOCK_BREACH' | 'REORDER_TRIGGER' | 'HEALTHY';
  is_critical: boolean;
  stockout_risk_score: number;
  risk_tier: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  explanation_text: string;
}

export interface PurchaseOrderOut {
  po_id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  order_date: string;
  promised_delivery_date: string;
  status: 'PENDING' | 'IN_TRANSIT' | 'DELIVERED' | 'OVERDUE' | 'CANCELLED';
  total_amount: number;
  currency: string;
  days_overdue: number;
}

export interface AlertOut {
  alert_id: string;
  alert_type: 'STOCKOUT' | 'SAFETY_STOCK_BREACH' | 'DELAYED_ORDER' | 'QUALITY_DROP' | 'HIGH_RISK_SUPPLIER';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  message: string;
  entity_type: string;
  entity_id: string;
  impact_valuation: number;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
  created_at: string;
  resolved_at: string | null;
}

export interface CorrectiveActionOut {
  action_id: string;
  alert_id?: string;
  title: string;
  description: string;
  assigned_to: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'IN_PROGRESS' | 'REVIEW' | 'RESOLVED';
  root_cause?: string;
  mitigation_plan?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
}

export interface CorrectiveActionCreate {
  alert_id?: string;
  title: string;
  description: string;
  assigned_to: string;
  priority: string;
  root_cause?: string;
  mitigation_plan?: string;
}

export interface ETLAuditLogOut {
  run_id: string;
  pipeline_name: string;
  batch_id?: string;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  rows_extracted: number;
  rows_loaded: number;
  rows_rejected: number;
  status: string;
  error_message?: string;
}

export interface ETLRejectedRecordOut {
  rejection_id: number;
  pipeline_name: string;
  source_table: string;
  payload: string;
  error_code: string;
  error_reason: string;
  rejected_at: string;
}

export interface DataQualityTestOut {
  test_id: number;
  test_name: string;
  target_table: string;
  assertion_type: string;
  metric_value: number;
  threshold: number;
  status: 'PASS' | 'FAIL' | 'WARNING';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  details?: string;
  executed_at: string;
}
