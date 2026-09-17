-- ============================================================================
-- SupplyGuard: PostgreSQL Star-Schema Warehouse DDL
-- Manufacturing Supply-Chain & Inventory Risk Platform
-- Includes Partitioning, Star Schema, Indexes, Audit, Alerts & Materialized Views
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create staging schema for ETL ingestion
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS audit_log;

-- ============================================================================
-- 1. DIMENSION TABLES
-- ============================================================================

DROP TABLE IF EXISTS dim_defect_type CASCADE;
CREATE TABLE dim_defect_type (
    defect_type_code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT
);

DROP TABLE IF EXISTS dim_factory CASCADE;
CREATE TABLE dim_factory (
    factory_id VARCHAR(30) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS dim_warehouse CASCADE;
CREATE TABLE dim_warehouse (
    warehouse_id VARCHAR(30) PRIMARY KEY,
    factory_id VARCHAR(30) NOT NULL REFERENCES dim_factory(factory_id),
    name VARCHAR(150) NOT NULL,
    warehouse_type VARCHAR(50) NOT NULL, -- RAW_MATERIALS, FINISHED_GOODS, IN_TRANSIT, QUARANTINE
    capacity_sqm NUMERIC(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS dim_supplier CASCADE;
CREATE TABLE dim_supplier (
    supplier_id VARCHAR(30) PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL, -- TIER_1, TIER_2, TIER_3
    reliability_rating NUMERIC(5, 2) NOT NULL, -- 0.0 to 100.0
    financial_health_score NUMERIC(5, 2) NOT NULL, -- 0.0 to 100.0
    baseline_lead_time_days INT NOT NULL,
    payment_terms VARCHAR(50) DEFAULT 'NET30',
    iso_certified BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS dim_material CASCADE;
CREATE TABLE dim_material (
    material_id VARCHAR(30) PRIMARY KEY,
    sku VARCHAR(60) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    standard_cost NUMERIC(12, 2) NOT NULL,
    current_unit_price NUMERIC(12, 2) NOT NULL,
    safety_stock_level INT NOT NULL,
    reorder_point INT NOT NULL,
    target_stock_level INT NOT NULL,
    min_order_qty INT NOT NULL,
    lead_time_days INT NOT NULL,
    is_critical BOOLEAN DEFAULT FALSE,
    primary_supplier_id VARCHAR(30) REFERENCES dim_supplier(supplier_id),
    secondary_supplier_id VARCHAR(30) REFERENCES dim_supplier(supplier_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS dim_date CASCADE;
CREATE TABLE dim_date (
    date_key DATE PRIMARY KEY,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INT NOT NULL,
    day INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- ============================================================================
-- 2. FACT TABLES
-- ============================================================================

DROP TABLE IF EXISTS fact_purchase_orders CASCADE;
CREATE TABLE fact_purchase_orders (
    po_id VARCHAR(50) PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id VARCHAR(30) NOT NULL REFERENCES dim_supplier(supplier_id),
    factory_id VARCHAR(30) NOT NULL REFERENCES dim_factory(factory_id),
    warehouse_id VARCHAR(30) NOT NULL REFERENCES dim_warehouse(warehouse_id),
    order_date DATE NOT NULL REFERENCES dim_date(date_key),
    promised_delivery_date DATE NOT NULL REFERENCES dim_date(date_key),
    status VARCHAR(30) NOT NULL, -- PENDING, IN_TRANSIT, DELIVERED, OVERDUE, CANCELLED
    total_amount NUMERIC(14, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS fact_purchase_order_lines CASCADE;
CREATE TABLE fact_purchase_order_lines (
    po_line_id VARCHAR(50) PRIMARY KEY,
    po_id VARCHAR(50) NOT NULL REFERENCES fact_purchase_orders(po_id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    quantity_ordered INT NOT NULL CHECK (quantity_ordered > 0),
    unit_price NUMERIC(12, 2) NOT NULL,
    line_total NUMERIC(14, 2) NOT NULL,
    line_status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS fact_goods_receipts CASCADE;
CREATE TABLE fact_goods_receipts (
    receipt_id VARCHAR(50) PRIMARY KEY,
    po_id VARCHAR(50) NOT NULL REFERENCES fact_purchase_orders(po_id),
    po_line_id VARCHAR(50) NOT NULL REFERENCES fact_purchase_order_lines(po_line_id),
    supplier_id VARCHAR(30) NOT NULL REFERENCES dim_supplier(supplier_id),
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    warehouse_id VARCHAR(30) NOT NULL REFERENCES dim_warehouse(warehouse_id),
    factory_id VARCHAR(30) NOT NULL REFERENCES dim_factory(factory_id),
    receipt_date DATE NOT NULL REFERENCES dim_date(date_key),
    quantity_delivered INT NOT NULL CHECK (quantity_delivered >= 0),
    quantity_accepted INT NOT NULL CHECK (quantity_accepted >= 0),
    quantity_rejected INT NOT NULL DEFAULT 0 CHECK (quantity_rejected >= 0),
    delivery_variance_days INT NOT NULL, -- actual - promised
    damage_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS fact_quality_inspections CASCADE;
CREATE TABLE fact_quality_inspections (
    inspection_id VARCHAR(50) PRIMARY KEY,
    receipt_id VARCHAR(50) NOT NULL REFERENCES fact_goods_receipts(receipt_id),
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    supplier_id VARCHAR(30) NOT NULL REFERENCES dim_supplier(supplier_id),
    inspection_date DATE NOT NULL REFERENCES dim_date(date_key),
    sample_size INT NOT NULL CHECK (sample_size > 0),
    defect_count INT NOT NULL DEFAULT 0 CHECK (defect_count >= 0),
    defect_ppm INT NOT NULL DEFAULT 0 CHECK (defect_ppm >= 0),
    defect_type_code VARCHAR(50) REFERENCES dim_defect_type(defect_type_code),
    disposition VARCHAR(30) NOT NULL, -- ACCEPTED, CONCESSION, REJECTED
    inspector_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Partitioned Fact Table: fact_inventory_movements (Quarterly Range Partitioning)
DROP TABLE IF EXISTS fact_inventory_movements CASCADE;
CREATE TABLE fact_inventory_movements (
    movement_id VARCHAR(50) NOT NULL,
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    warehouse_id VARCHAR(30) NOT NULL REFERENCES dim_warehouse(warehouse_id),
    factory_id VARCHAR(30) NOT NULL REFERENCES dim_factory(factory_id),
    movement_date DATE NOT NULL,
    movement_type VARCHAR(50) NOT NULL, -- GOODS_RECEIPT, PRODUCTION_ISSUE, SCRAP, TRANSFER_IN, TRANSFER_OUT, CYCLE_ADJUSTMENT
    quantity INT NOT NULL,
    reference_doc_type VARCHAR(50),
    reference_doc_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fact_inventory_movements PRIMARY KEY (movement_id, movement_date)
) PARTITION BY RANGE (movement_date);

-- Quarterly Partitions for 2025 and 2026
CREATE TABLE fact_inventory_movements_2025_q1 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE fact_inventory_movements_2025_q2 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

CREATE TABLE fact_inventory_movements_2025_q3 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE fact_inventory_movements_2025_q4 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');

CREATE TABLE fact_inventory_movements_2026_q1 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');

CREATE TABLE fact_inventory_movements_2026_q2 PARTITION OF fact_inventory_movements
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

CREATE TABLE fact_inventory_movements_default PARTITION OF fact_inventory_movements
    DEFAULT;

DROP TABLE IF EXISTS fact_production_schedules CASCADE;
CREATE TABLE fact_production_schedules (
    work_order_id VARCHAR(50) PRIMARY KEY,
    product_sku VARCHAR(60) NOT NULL,
    factory_id VARCHAR(30) NOT NULL REFERENCES dim_factory(factory_id),
    planned_quantity INT NOT NULL CHECK (planned_quantity > 0),
    completed_quantity INT NOT NULL DEFAULT 0,
    start_date DATE NOT NULL REFERENCES dim_date(date_key),
    end_date DATE NOT NULL REFERENCES dim_date(date_key),
    status VARCHAR(30) NOT NULL, -- PLANNED, IN_PROGRESS, COMPLETED, BLOCKED_SHORTAGE
    priority VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS fact_bom_allocations CASCADE;
CREATE TABLE fact_bom_allocations (
    allocation_id VARCHAR(50) PRIMARY KEY,
    work_order_id VARCHAR(50) NOT NULL REFERENCES fact_production_schedules(work_order_id) ON DELETE CASCADE,
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    required_quantity INT NOT NULL CHECK (required_quantity > 0),
    allocated_quantity INT NOT NULL DEFAULT 0,
    shortage_quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. ETL AUDIT, REJECTED RECORDS & DATA QUALITY
-- ============================================================================

DROP TABLE IF EXISTS etl_pipeline_audit CASCADE;
CREATE TABLE etl_pipeline_audit (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name VARCHAR(100) NOT NULL,
    batch_id VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2),
    rows_extracted INT DEFAULT 0,
    rows_loaded INT DEFAULT 0,
    rows_rejected INT DEFAULT 0,
    status VARCHAR(30) NOT NULL, -- RUNNING, SUCCESS, FAILED, WARNING
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS etl_rejected_records CASCADE;
CREATE TABLE etl_rejected_records (
    rejection_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    batch_id VARCHAR(100),
    source_table VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    error_code VARCHAR(50) NOT NULL,
    error_reason TEXT NOT NULL,
    rejected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS data_quality_test_results CASCADE;
CREATE TABLE data_quality_test_results (
    test_id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES etl_pipeline_audit(run_id),
    test_name VARCHAR(150) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    assertion_type VARCHAR(50) NOT NULL, -- NOT_NULL, RANGE, POSITIVE_VALUE, REFERENTIAL, UNIQUE
    metric_value NUMERIC(14, 4),
    threshold NUMERIC(14, 4),
    status VARCHAR(20) NOT NULL, -- PASS, FAIL, WARNING
    severity VARCHAR(20) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    details TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. ML RISK ENGINE SCORES, ALERTS & CORRECTIVE ACTIONS
-- ============================================================================

DROP TABLE IF EXISTS fact_supplier_risk_scores CASCADE;
CREATE TABLE fact_supplier_risk_scores (
    score_id BIGSERIAL PRIMARY KEY,
    supplier_id VARCHAR(30) NOT NULL REFERENCES dim_supplier(supplier_id),
    score_date DATE NOT NULL,
    risk_score NUMERIC(5, 2) NOT NULL, -- 0.0 to 100.0
    risk_tier VARCHAR(20) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    otd_rate_90d NUMERIC(5, 2),
    defect_ppm_90d INT,
    lead_time_variance_avg NUMERIC(6, 2),
    financial_risk_score NUMERIC(5, 2),
    single_source_material_count INT,
    top_contributing_factors JSONB NOT NULL,
    explanation_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_supplier_score_date UNIQUE (supplier_id, score_date)
);

DROP TABLE IF EXISTS fact_stockout_risk_scores CASCADE;
CREATE TABLE fact_stockout_risk_scores (
    score_id BIGSERIAL PRIMARY KEY,
    material_id VARCHAR(30) NOT NULL REFERENCES dim_material(material_id),
    score_date DATE NOT NULL,
    stockout_risk_score NUMERIC(5, 2) NOT NULL, -- 0.0 to 100.0
    risk_tier VARCHAR(20) NOT NULL,
    current_stock INT NOT NULL,
    days_of_inventory NUMERIC(8, 2),
    safety_stock_ratio NUMERIC(6, 2),
    consumption_trend_factor NUMERIC(6, 2),
    open_po_count INT,
    top_contributing_factors JSONB NOT NULL,
    explanation_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_material_score_date UNIQUE (material_id, score_date)
);

DROP TABLE IF EXISTS supply_alerts CASCADE;
CREATE TABLE supply_alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- STOCKOUT, SAFETY_STOCK_BREACH, DELAYED_ORDER, QUALITY_DROP, HIGH_RISK_SUPPLIER
    severity VARCHAR(20) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    entity_type VARCHAR(30) NOT NULL, -- SUPPLIER, MATERIAL, PURCHASE_ORDER, WORK_ORDER
    entity_id VARCHAR(50) NOT NULL,
    impact_valuation NUMERIC(14, 2) DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

DROP TABLE IF EXISTS corrective_actions CASCADE;
CREATE TABLE corrective_actions (
    action_id VARCHAR(50) PRIMARY KEY,
    alert_id VARCHAR(50) REFERENCES supply_alerts(alert_id),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    assigned_to VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'HIGH', -- CRITICAL, HIGH, MEDIUM, LOW
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN', -- OPEN, IN_PROGRESS, REVIEW, RESOLVED
    root_cause TEXT,
    mitigation_plan TEXT,
    resolution_notes TEXT,
    target_completion_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

DROP TABLE IF EXISTS user_accounts CASCADE;
CREATE TABLE user_accounts (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'ANALYST', -- ADMIN, SUPPLY_CHAIN_DIRECTOR, PROCUREMENT_LEAD, QUALITY_ENGINEER, ANALYST
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. INDEXES (B-Tree Composite & BRIN)
-- ============================================================================

-- B-Tree Composite Indexes for Filter/Join Acceleration
CREATE INDEX idx_po_supplier_order_date ON fact_purchase_orders (supplier_id, order_date);
CREATE INDEX idx_po_status_date ON fact_purchase_orders (status, promised_delivery_date);
CREATE INDEX idx_pol_material ON fact_purchase_order_lines (material_id, po_id);
CREATE INDEX idx_gr_supplier_receipt_date ON fact_goods_receipts (supplier_id, receipt_date);
CREATE INDEX idx_gr_po_line ON fact_goods_receipts (po_id, po_line_id);
CREATE INDEX idx_qc_supplier_inspection ON fact_quality_inspections (supplier_id, inspection_date);
CREATE INDEX idx_qc_material_disposition ON fact_quality_inspections (material_id, disposition);

-- Composite Indexes on Movement Partitioned Tables
CREATE INDEX idx_mov_mat_wh_date ON fact_inventory_movements (material_id, warehouse_id, movement_date);
CREATE INDEX idx_mov_date_type ON fact_inventory_movements (movement_date, movement_type);

-- BRIN (Block Range Index) for append-only timestamp ranges
CREATE INDEX idx_mov_date_brin ON fact_inventory_movements USING BRIN (movement_date);
CREATE INDEX idx_gr_date_brin ON fact_goods_receipts USING BRIN (receipt_date);
CREATE INDEX idx_qc_date_brin ON fact_quality_inspections USING BRIN (inspection_date);

-- Alerts & Action Indexes
CREATE INDEX idx_alerts_status_severity ON supply_alerts (status, severity);
CREATE INDEX idx_alerts_entity ON supply_alerts (entity_type, entity_id);
CREATE INDEX idx_corrective_status_assigned ON corrective_actions (status, assigned_to);

-- ============================================================================
-- 6. MATERIALIZED VIEWS
-- ============================================================================

-- Materialized View 1: Supplier Performance Scorecard (OTD %, PPM, Lead Time Variance)
DROP MATERIALIZED VIEW IF EXISTS mv_supplier_performance CASCADE;
CREATE MATERIALIZED VIEW mv_supplier_performance AS
WITH receipt_metrics AS (
    SELECT 
        gr.supplier_id,
        COUNT(gr.receipt_id) AS total_deliveries,
        COUNT(CASE WHEN gr.delivery_variance_days <= 0 THEN 1 END) AS on_time_deliveries,
        AVG(gr.delivery_variance_days)::NUMERIC(6, 2) AS avg_lead_time_variance_days,
        STDDEV(gr.delivery_variance_days)::NUMERIC(6, 2) AS lead_time_variance_std,
        SUM(gr.quantity_delivered) AS total_qty_delivered,
        SUM(gr.quantity_accepted) AS total_qty_accepted,
        SUM(gr.quantity_rejected) AS total_qty_rejected
    FROM fact_goods_receipts gr
    GROUP BY gr.supplier_id
),
quality_metrics AS (
    SELECT 
        qc.supplier_id,
        COUNT(qc.inspection_id) AS total_inspections,
        SUM(qc.defect_count) AS total_defect_count,
        SUM(qc.sample_size) AS total_sample_size,
        CASE 
            WHEN SUM(qc.sample_size) > 0 
            THEN ROUND((SUM(qc.defect_count)::NUMERIC / SUM(qc.sample_size)::NUMERIC) * 1000000)
            ELSE 0 
        END AS overall_defect_ppm
    FROM fact_quality_inspections qc
    GROUP BY qc.supplier_id
),
spend_metrics AS (
    SELECT 
        po.supplier_id,
        COUNT(po.po_id) AS total_pos_issued,
        SUM(po.total_amount) AS total_spend_amount,
        SUM(CASE WHEN po.status = 'OVERDUE' THEN po.total_amount ELSE 0 END) AS overdue_spend_amount
    FROM fact_purchase_orders po
    GROUP BY po.supplier_id
)
SELECT 
    s.supplier_id,
    s.code AS supplier_code,
    s.name AS supplier_name,
    s.category AS supplier_category,
    s.country,
    s.tier,
    s.reliability_rating AS baseline_reliability,
    s.financial_health_score,
    COALESCE(rm.total_deliveries, 0) AS total_deliveries,
    CASE 
        WHEN COALESCE(rm.total_deliveries, 0) > 0 
        THEN ROUND((rm.on_time_deliveries::NUMERIC / rm.total_deliveries::NUMERIC) * 100.0, 2)
        ELSE 100.0 
    END AS otd_percentage,
    COALESCE(rm.avg_lead_time_variance_days, 0) AS avg_lead_time_variance_days,
    COALESCE(rm.lead_time_variance_std, 0) AS lead_time_variance_std,
    COALESCE(qm.overall_defect_ppm, 0) AS overall_defect_ppm,
    COALESCE(sm.total_spend_amount, 0) AS total_spend,
    COALESCE(sm.overdue_spend_amount, 0) AS overdue_spend,
    DENSE_RANK() OVER (PARTITION BY s.category ORDER BY 
        (CASE WHEN COALESCE(rm.total_deliveries, 0) > 0 
              THEN (rm.on_time_deliveries::NUMERIC / rm.total_deliveries::NUMERIC) 
              ELSE 1.0 END) DESC,
        COALESCE(qm.overall_defect_ppm, 0) ASC
    ) AS category_rank
FROM dim_supplier s
LEFT JOIN receipt_metrics rm ON s.supplier_id = rm.supplier_id
LEFT JOIN quality_metrics qm ON s.supplier_id = qm.supplier_id
LEFT JOIN spend_metrics sm ON s.supplier_id = sm.supplier_id;

CREATE UNIQUE INDEX idx_mv_supplier_perf_id ON mv_supplier_performance (supplier_id);
CREATE INDEX idx_mv_supplier_perf_otd ON mv_supplier_performance (otd_percentage);


-- Materialized View 2: Inventory Health Daily (DOI, Turnover, Safety Stock Status)
DROP MATERIALIZED VIEW IF EXISTS mv_inventory_health_daily CASCADE;
CREATE MATERIALIZED VIEW mv_inventory_health_daily AS
WITH stock_on_hand AS (
    SELECT 
        m.material_id,
        m.warehouse_id,
        SUM(m.quantity) AS current_stock
    FROM fact_inventory_movements m
    GROUP BY m.material_id, m.warehouse_id
),
consumption_30d AS (
    SELECT 
        m.material_id,
        m.warehouse_id,
        ABS(SUM(CASE WHEN m.quantity < 0 THEN m.quantity ELSE 0 END)) AS total_consumption_30d
    FROM fact_inventory_movements m
    WHERE m.movement_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY m.material_id, m.warehouse_id
),
open_pipeline AS (
    SELECT 
        pol.material_id,
        po.warehouse_id,
        SUM(pol.quantity_ordered) AS quantity_on_order
    FROM fact_purchase_order_lines pol
    JOIN fact_purchase_orders po ON pol.po_id = po.po_id
    WHERE po.status IN ('PENDING', 'IN_TRANSIT')
    GROUP BY pol.material_id, po.warehouse_id
)
SELECT 
    mat.material_id,
    mat.sku,
    mat.name AS material_name,
    mat.category,
    mat.is_critical,
    mat.standard_cost,
    mat.safety_stock_level,
    mat.reorder_point,
    wh.warehouse_id,
    wh.name AS warehouse_name,
    wh.factory_id,
    COALESCE(soh.current_stock, 0) AS current_stock,
    COALESCE(soh.current_stock, 0) * mat.standard_cost AS current_stock_valuation,
    COALESCE(c30.total_consumption_30d, 0) AS consumption_last_30d,
    ROUND(COALESCE(c30.total_consumption_30d, 0)::NUMERIC / 30.0, 2) AS daily_burn_rate,
    CASE 
        WHEN COALESCE(c30.total_consumption_30d, 0) > 0 
        THEN ROUND(COALESCE(soh.current_stock, 0)::NUMERIC / (c30.total_consumption_30d::NUMERIC / 30.0), 1)
        ELSE 999.0 
    END AS days_of_inventory,
    COALESCE(op.quantity_on_order, 0) AS quantity_on_order,
    CASE 
        WHEN COALESCE(soh.current_stock, 0) <= 0 THEN 'STOCKOUT'
        WHEN COALESCE(soh.current_stock, 0) < mat.safety_stock_level THEN 'SAFETY_STOCK_BREACH'
        WHEN COALESCE(soh.current_stock, 0) < mat.reorder_point THEN 'REORDER_TRIGGER'
        WHEN COALESCE(c30.total_consumption_30d, 0) > 0 AND (COALESCE(soh.current_stock, 0)::NUMERIC / (c30.total_consumption_30d::NUMERIC / 30.0)) > 90.0 THEN 'OVERSTOCK'
        ELSE 'HEALTHY'
    END AS stock_health_status
FROM dim_material mat
CROSS JOIN dim_warehouse wh
LEFT JOIN stock_on_hand soh ON mat.material_id = soh.material_id AND wh.warehouse_id = soh.warehouse_id
LEFT JOIN consumption_30d c30 ON mat.material_id = c30.material_id AND wh.warehouse_id = c30.warehouse_id
LEFT JOIN open_pipeline op ON mat.material_id = op.material_id AND wh.warehouse_id = op.warehouse_id
WHERE wh.warehouse_type = 'RAW_MATERIALS';

CREATE UNIQUE INDEX idx_mv_inv_mat_wh ON mv_inventory_health_daily (material_id, warehouse_id);
CREATE INDEX idx_mv_inv_status ON mv_inventory_health_daily (stock_health_status);
CREATE INDEX idx_mv_inv_doi ON mv_inventory_health_daily (days_of_inventory);


-- Materialized View 3: Production at Risk (BOM Component Shortages Impacting Work Orders)
DROP MATERIALIZED VIEW IF EXISTS mv_production_at_risk CASCADE;
CREATE MATERIALIZED VIEW mv_production_at_risk AS
WITH material_stock_summary AS (
    SELECT 
        material_id,
        SUM(current_stock) AS total_network_stock,
        SUM(consumption_last_30d) AS network_consumption_30d
    FROM mv_inventory_health_daily
    GROUP BY material_id
)
SELECT 
    wo.work_order_id,
    wo.product_sku,
    wo.factory_id,
    f.name AS factory_name,
    wo.planned_quantity,
    wo.start_date,
    wo.end_date,
    wo.status AS wo_status,
    wo.priority,
    bom.material_id,
    m.sku AS component_sku,
    m.name AS component_name,
    m.is_critical AS is_component_critical,
    bom.required_quantity,
    bom.allocated_quantity,
    bom.shortage_quantity,
    COALESCE(mss.total_network_stock, 0) AS total_network_stock,
    ROUND(bom.required_quantity * m.standard_cost, 2) AS component_cost_at_risk,
    CASE 
        WHEN bom.shortage_quantity > 0 THEN 'CRITICAL_SHORTAGE'
        WHEN COALESCE(mss.total_network_stock, 0) < bom.required_quantity THEN 'PROJECTED_SHORTAGE'
        ELSE 'ALLOCATED'
    END AS risk_classification
FROM fact_production_schedules wo
JOIN dim_factory f ON wo.factory_id = f.factory_id
JOIN fact_bom_allocations bom ON wo.work_order_id = bom.work_order_id
JOIN dim_material m ON bom.material_id = m.material_id
LEFT JOIN material_stock_summary mss ON bom.material_id = mss.material_id
WHERE wo.status IN ('PLANNED', 'IN_PROGRESS', 'BLOCKED_SHORTAGE');

CREATE UNIQUE INDEX idx_mv_prod_wo_mat ON mv_production_at_risk (work_order_id, material_id);
CREATE INDEX idx_mv_prod_risk_class ON mv_production_at_risk (risk_classification);
