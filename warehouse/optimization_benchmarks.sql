-- ============================================================================
-- SupplyGuard: Query Optimization Benchmarks with EXPLAIN ANALYZE
-- 3 Production Query Optimization Comparisons Demonstrating Indexing,
-- Partition Pruning, CTE/Window Restructuring, and Materialized Views
-- ============================================================================

-- ============================================================================
-- OPTIMIZATION SCENARIO 1: Inventory Movements Rolling Balance & Burn Rate
-- ============================================================================

-- UNOPTIMIZED QUERY 1:
-- Full table scan on unindexed movements, non-sargable date filter, and expensive Sort
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT 
    m.material_id,
    m.warehouse_id,
    m.movement_date,
    m.quantity,
    SUM(m.quantity) OVER (
        PARTITION BY m.material_id, m.warehouse_id 
        ORDER BY m.movement_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance,
    AVG(CASE WHEN m.quantity < 0 THEN ABS(m.quantity) ELSE NULL END) OVER (
        PARTITION BY m.material_id, m.warehouse_id 
        ORDER BY m.movement_date 
        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_burn_rate
FROM fact_inventory_movements m
WHERE TO_CHAR(m.movement_date, 'YYYY-MM') >= '2025-10'
  AND m.material_id = 'MAT-00042';

-- OPTIMIZED QUERY 1:
-- Leverages quarterly partition pruning (fact_inventory_movements_2025_q4 + 2026_q1/q2),
-- composite B-tree index (material_id, warehouse_id, movement_date),
-- and sargable date comparison.
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
WITH filtered_movements AS (
    SELECT 
        m.material_id,
        m.warehouse_id,
        m.movement_date,
        m.quantity
    FROM fact_inventory_movements m
    WHERE m.material_id = 'MAT-00042'
      AND m.movement_date >= '2025-10-01'::DATE
)
SELECT 
    material_id,
    warehouse_id,
    movement_date,
    quantity,
    SUM(quantity) OVER (
        PARTITION BY material_id, warehouse_id 
        ORDER BY movement_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance,
    AVG(CASE WHEN quantity < 0 THEN ABS(quantity) ELSE NULL END) OVER (
        PARTITION BY material_id, warehouse_id 
        ORDER BY movement_date 
        ROWS BETWEEN 30 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_burn_rate
FROM filtered_movements;


-- ============================================================================
-- OPTIMIZATION SCENARIO 2: Supplier Scorecard & Lead-Time Variance
-- ============================================================================

-- UNOPTIMIZED QUERY 2:
-- Correlated scalar subqueries executed per supplier row causing repeated scans
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT 
    s.supplier_id,
    s.name,
    s.category,
    (
        SELECT COUNT(*) 
        FROM fact_goods_receipts gr 
        WHERE gr.supplier_id = s.supplier_id 
          AND gr.receipt_date >= '2025-01-01'
    ) AS total_receipts,
    (
        SELECT COUNT(*) 
        FROM fact_goods_receipts gr 
        WHERE gr.supplier_id = s.supplier_id 
          AND gr.delivery_variance_days <= 0 
          AND gr.receipt_date >= '2025-01-01'
    ) AS on_time_receipts,
    (
        SELECT AVG(gr.delivery_variance_days) 
        FROM fact_goods_receipts gr 
        WHERE gr.supplier_id = s.supplier_id 
          AND gr.receipt_date >= '2025-01-01'
    ) AS avg_delay_days,
    (
        SELECT SUM(po.total_amount) 
        FROM fact_purchase_orders po 
        WHERE po.supplier_id = s.supplier_id 
          AND po.status = 'OVERDUE'
    ) AS overdue_po_amount
FROM dim_supplier s
WHERE s.is_active = TRUE;

-- OPTIMIZED QUERY 2:
-- Grouped CTEs with covering composite indexes (idx_gr_supplier_receipt_date, idx_po_status_date)
-- and single Hash Join pass
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
WITH receipt_summary AS (
    SELECT 
        supplier_id,
        COUNT(receipt_id) AS total_receipts,
        COUNT(CASE WHEN delivery_variance_days <= 0 THEN 1 END) AS on_time_receipts,
        ROUND(AVG(delivery_variance_days)::NUMERIC, 2) AS avg_delay_days
    FROM fact_goods_receipts
    WHERE receipt_date >= '2025-01-01'::DATE
    GROUP BY supplier_id
),
overdue_summary AS (
    SELECT 
        supplier_id,
        SUM(total_amount) AS overdue_po_amount
    FROM fact_purchase_orders
    WHERE status = 'OVERDUE'
    GROUP BY supplier_id
)
SELECT 
    s.supplier_id,
    s.name,
    s.category,
    COALESCE(rs.total_receipts, 0) AS total_receipts,
    COALESCE(rs.on_time_receipts, 0) AS on_time_receipts,
    CASE 
        WHEN COALESCE(rs.total_receipts, 0) > 0 
        THEN ROUND((rs.on_time_receipts::NUMERIC / rs.total_receipts::NUMERIC) * 100.0, 2)
        ELSE 100.0 
    END AS otd_pct,
    COALESCE(rs.avg_delay_days, 0.0) AS avg_delay_days,
    COALESCE(os.overdue_po_amount, 0.0) AS overdue_po_amount
FROM dim_supplier s
LEFT JOIN receipt_summary rs ON s.supplier_id = rs.supplier_id
LEFT JOIN overdue_summary os ON s.supplier_id = os.supplier_id
WHERE s.is_active = TRUE;


-- ============================================================================
-- OPTIMIZATION SCENARIO 3: Multi-Level BOM Production Shortage Valuation
-- ============================================================================

-- UNOPTIMIZED QUERY 3:
-- On-the-fly dynamic aggregation of 110,000 movements joined against BOM allocations
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT 
    wo.work_order_id,
    wo.product_sku,
    wo.priority,
    bom.material_id,
    m.name AS material_name,
    bom.required_quantity,
    (
        SELECT COALESCE(SUM(quantity), 0) 
        FROM fact_inventory_movements im 
        WHERE im.material_id = bom.material_id
    ) AS network_stock_on_hand,
    ROUND(bom.required_quantity * m.standard_cost, 2) AS line_value_usd
FROM fact_production_schedules wo
JOIN fact_bom_allocations bom ON wo.work_order_id = bom.work_order_id
JOIN dim_material m ON bom.material_id = m.material_id
WHERE wo.status IN ('PLANNED', 'BLOCKED_SHORTAGE')
  AND bom.shortage_quantity > 0;

-- OPTIMIZED QUERY 3:
-- Utilizes precomputed Materialized View mv_production_at_risk with unique index
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT 
    work_order_id,
    product_sku,
    priority,
    material_id,
    component_name,
    required_quantity,
    total_network_stock AS network_stock_on_hand,
    component_cost_at_risk AS line_value_usd,
    risk_classification
FROM mv_production_at_risk
WHERE risk_classification = 'CRITICAL_SHORTAGE';
