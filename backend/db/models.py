from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.db.database import Base

class UserAccount(Base):
    __tablename__ = "user_accounts"
    user_id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), default="ANALYST")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Supplier(Base):
    __tablename__ = "dim_supplier"
    supplier_id = Column(String(30), primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    tier = Column(String(20), nullable=False)
    reliability_rating = Column(Float, nullable=False)
    financial_health_score = Column(Float, nullable=False)
    baseline_lead_time_days = Column(Integer, nullable=False)
    payment_terms = Column(String(50), default="NET30")
    iso_certified = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Material(Base):
    __tablename__ = "dim_material"
    material_id = Column(String(30), primary_key=True)
    sku = Column(String(60), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    standard_cost = Column(Float, nullable=False)
    current_unit_price = Column(Float, nullable=False)
    safety_stock_level = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=False)
    target_stock_level = Column(Integer, nullable=False)
    min_order_qty = Column(Integer, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    is_critical = Column(Boolean, default=False)
    primary_supplier_id = Column(String(30))
    secondary_supplier_id = Column(String(30), nullable=True)

class PurchaseOrder(Base):
    __tablename__ = "fact_purchase_orders"
    po_id = Column(String(50), primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(String(30), nullable=False)
    factory_id = Column(String(30), nullable=False)
    warehouse_id = Column(String(30), nullable=False)
    order_date = Column(Date, nullable=False)
    promised_delivery_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")

class SupplyAlert(Base):
    __tablename__ = "supply_alerts"
    alert_id = Column(String(50), primary_key=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(50), nullable=False)
    impact_valuation = Column(Float, default=0.0)
    status = Column(String(30), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"
    action_id = Column(String(50), primary_key=True)
    alert_id = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    assigned_to = Column(String(100), nullable=False)
    priority = Column(String(20), default="HIGH")
    status = Column(String(30), default="OPEN")
    root_cause = Column(Text, nullable=True)
    mitigation_plan = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    target_completion_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class ETLPipelineAudit(Base):
    __tablename__ = "etl_pipeline_audit"
    run_id = Column(String(50), primary_key=True)
    pipeline_name = Column(String(100), nullable=False)
    batch_id = Column(String(100), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    rows_extracted = Column(Integer, default=0)
    rows_loaded = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    status = Column(String(30), default="SUCCESS")
    error_message = Column(Text, nullable=True)

class ETLRejectedRecord(Base):
    __tablename__ = "etl_rejected_records"
    rejection_id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_name = Column(String(100), nullable=False)
    batch_id = Column(String(100), nullable=True)
    source_table = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    error_code = Column(String(50), nullable=False)
    error_reason = Column(Text, nullable=False)
    rejected_at = Column(DateTime, default=datetime.utcnow)

class DataQualityTestResult(Base):
    __tablename__ = "data_quality_test_results"
    test_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), nullable=True)
    test_name = Column(String(150), nullable=False)
    target_table = Column(String(100), nullable=False)
    assertion_type = Column(String(50), nullable=False)
    metric_value = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
    status = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    details = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
