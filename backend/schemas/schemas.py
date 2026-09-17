from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    role: str

class ContributingFactor(BaseModel):
    feature: str
    impact_percentage: float
    raw_value: float

class SupplierScorecard(BaseModel):
    supplier_id: str
    code: str
    name: str
    category: str
    country: str
    city: str
    tier: str
    reliability_rating: float
    financial_health_score: float
    otd_percentage: float
    avg_lead_time_variance_days: float
    lead_time_variance_std: float
    overall_defect_ppm: int
    total_spend: float
    overdue_spend: float
    risk_score: float
    risk_tier: str
    top_contributing_factors: List[ContributingFactor] = []
    explanation_text: str = ""

class MaterialOut(BaseModel):
    material_id: str
    sku: str
    name: str
    category: str
    unit_of_measure: str
    standard_cost: float
    safety_stock_level: int
    reorder_point: int
    current_stock: int = 0
    days_of_inventory: float = 0.0
    stock_health_status: str = "HEALTHY"
    is_critical: bool = False
    stockout_risk_score: float = 0.0
    risk_tier: str = "LOW"
    explanation_text: str = ""

class PurchaseOrderOut(BaseModel):
    po_id: str
    po_number: str
    supplier_id: str
    supplier_name: str = ""
    order_date: str
    promised_delivery_date: str
    status: str
    total_amount: float
    currency: str = "USD"
    days_overdue: int = 0

class ExecutiveKPIs(BaseModel):
    on_time_delivery_rate: float
    total_spend_at_risk_usd: float
    active_stockouts_count: int
    total_inventory_valuation_usd: float
    average_days_of_inventory: float
    high_risk_suppliers_count: int
    active_alerts_count: int
    open_corrective_actions_count: int

class AlertOut(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    entity_type: str
    entity_id: str
    impact_valuation: float
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

class AlertUpdate(BaseModel):
    status: str # ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED

class CorrectiveActionCreate(BaseModel):
    alert_id: Optional[str] = None
    title: str
    description: str
    assigned_to: str
    priority: str = "HIGH"
    root_cause: Optional[str] = None
    mitigation_plan: Optional[str] = None
    target_completion_date: Optional[date] = None

class CorrectiveActionUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    root_cause: Optional[str] = None
    mitigation_plan: Optional[str] = None
    resolution_notes: Optional[str] = None

class CorrectiveActionOut(BaseModel):
    action_id: str
    alert_id: Optional[str] = None
    title: str
    description: str
    assigned_to: str
    priority: str
    status: str
    root_cause: Optional[str] = None
    mitigation_plan: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

class ETLAuditLogOut(BaseModel):
    run_id: str
    pipeline_name: str
    batch_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float
    rows_extracted: int
    rows_loaded: int
    rows_rejected: int
    status: str
    error_message: Optional[str] = None

class ETLRejectedRecordOut(BaseModel):
    rejection_id: int
    pipeline_name: str
    source_table: str
    payload: str
    error_code: str
    error_reason: str
    rejected_at: datetime

class DataQualityTestOut(BaseModel):
    test_id: int
    test_name: str
    target_table: str
    assertion_type: str
    metric_value: float
    threshold: float
    status: str
    severity: str
    details: Optional[str] = None
    executed_at: datetime
