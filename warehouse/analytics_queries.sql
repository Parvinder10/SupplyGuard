-- ============================================================================
-- SupplyGuard: Advanced Analytical SQL Library
-- Demonstrates CTEs, Window Functions (LAG, LEAD, Rolling Averages, Dense Rank),
-- Conditional Aggregations, Lead-Time Variance, Inventory Health, and Production Risk
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Supplier Reliability Trajectory (OTD Trend with LAG and Moving Averages)
-- Uses window functions (LAG, AVG() OVER) to detect deteriorating vendor performance
-- ----------------------------------------------------------------------------
WITH monthly_supplier_deliveries AS (
    SELECT 
        s.supplier_id,
        s.name AS supplier_name,
        s.category,
        DATE_TRUNC('month', gr.receipt_date)::DATE AS delivery_month,
        COUNT(gr.receipt_id) AS delivery_count,
        COUNT(CASE WHEN gr.delivery_variance_days <= 0 THEN 1 END) AS on_time_count,
        AVG(gr.delivery_variance_days)::NUMERIC(6, 2) AS avg_variance_days,
        SUM(gr.quantity_rejected)::NUMERIC / NULLIF(SUM(gr.quantity_delivered), 0) * 1000000 AS monthly_defect_ppm
    FROM fact_goods_receipts gr
    JOIN dim_supplier s ON gr.supplier_id = s.supplier_id
    GROUP BY s.supplier_id, s.name, s.category, DATE_TRUNC('month', gr.receipt_date)
),
supplier_windowed_metrics AS (
    SELECT 
        supplier_id,
        supplier_name,
        category,
        delivery_month,
        delivery_count,
        ROUND((on_time_count::NUMERIC / delivery_count::NUMERIC) * 100.0, 2) AS monthly_otd_pct,
        -- Prior month OTD using LAG
        LAG(ROUND((on_time_count::NUMERIC / delivery_count::NUMERIC) * 100.0, 2), 1) 
            OVER (PARTITION BY supplier_id ORDER BY delivery_month) AS prior_month_otd_pct,
        -- Next expected delivery variance using LEAD
        LEAD(avg_variance_days, 1) 
            OVER (PARTITION BY supplier_id ORDER BY delivery_month) AS next_month_variance_days,
        -- 3-Month Rolling Average OTD
        AVG(ROUND((on_time_count::NUMERIC / delivery_count::NUMERIC) * 100.0, 2)) 
            OVER (PARTITION BY supplier_id ORDER BY delivery_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3m_otd_pct,
        -- 3-Month Rolling Defect PPM
        AVG(monthly_defect_ppm) 
            OVER (PARTITION BY supplier_id ORDER BY delivery_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3m_defect_ppm,
        -- Dense rank within category by current rolling OTD
        DENSE_RANK() OVER (
            PARTITION BY category, delivery_month 
            ORDER BY AVG(ROUND((on_time_count::NUMERIC / delivery_count::NUMERIC) * 100.0, 2)) 
                OVER (PARTITION BY supplier_id ORDER BY delivery_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) DESC
        ) AS category_rank
    FROM monthly_supplier_deliveries
)
SELECT 
    supplier_id,
    supplier_name,
    category,
    delivery_month,
    monthly_otd_pct,
    prior_month_otd_pct,
    ROUND(monthly_otd_pct - prior_month_otd_pct, 2) AS otd_mom_change_pct,
    ROUND(rolling_3m_otd_pct, 2) AS rolling_3m_otd_pct,
    ROUND(rolling_3m_defect_ppm, 0) AS rolling_3m_defect_ppm,
    category_rank,
    CASE 
        WHEN (monthly_otd_pct - prior_month_otd_pct) < -10.0 THEN 'SEVERE_DEGRADATION'
        WHEN (monthly_otd_pct - prior_month_otd_pct) < -5.0 THEN 'MODERATE_DEGRADATION'
        WHEN (monthly_otd_pct - prior_month_otd_pct) > 5.0 THEN 'SIGNIFICANT_IMPROVEMENT'
        ELSE 'STABLE'
    END AS performance_trajectory
FROM supplier_windowed_metrics
ORDER BY category, delivery_month DESC, rolling_3m_otd_pct ASC;


-- ----------------------------------------------------------------------------
-- QUERY 2: Inventory Turnover, Days of Inventory (DOI), and Safety Stock Violations
-- Calculates cumulative stock, burn rates, and inventory velocity across warehouses
-- ----------------------------------------------------------------------------
WITH inventory_balances AS (
    SELECT 
        m.material_id,
        m.warehouse_id,
        SUM(m.quantity) AS on_hand_units,
        SUM(CASE WHEN m.quantity < 0 THEN ABS(m.quantity) ELSE 0 END) AS total_consumed_units,
        SUM(CASE WHEN m.quantity > 0 THEN m.quantity ELSE 0 END) AS total_replenished_units
    FROM fact_inventory_movements m
    GROUP BY m.material_id, m.warehouse_id
),
daily_burn_rates AS (
    SELECT 
        material_id,
        warehouse_id,
        ABS(SUM(CASE WHEN quantity < 0 THEN quantity ELSE 0 END))::NUMERIC / 90.0 AS avg_daily_burn_90d
    FROM fact_inventory_movements
    WHERE movement_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY material_id, warehouse_id
)
SELECT 
    mat.material_id,
    mat.sku,
    mat.name AS material_name,
    mat.category,
    mat.is_critical,
    mat.standard_cost,
    wh.name AS warehouse_name,
    wh.warehouse_type,
    COALESCE(ib.on_hand_units, 0) AS on_hand_units,
    ROUND(COALESCE(ib.on_hand_units, 0) * mat.standard_cost, 2) AS total_inventory_value_usd,
    mat.safety_stock_level,
    mat.reorder_point,
    ROUND(COALESCE(dbr.avg_daily_burn_90d, 0), 2) AS avg_daily_burn_rate,
    CASE 
        WHEN COALESCE(dbr.avg_daily_burn_90d, 0) > 0 
        THEN ROUND(COALESCE(ib.on_hand_units, 0) / dbr.avg_daily_burn_90d, 1)
        ELSE 999.0 
    END AS days_of_inventory,
    -- Inventory Turnover Ratio: Annualized Cost of Goods Used / Average Inventory Value
    CASE 
        WHEN (COALESCE(ib.on_hand_units, 0) * mat.standard_cost) > 0
        THEN ROUND(((COALESCE(dbr.avg_daily_burn_90d, 0) * 365.0 * mat.standard_cost) / 
                   (COALESCE(ib.on_hand_units, 0) * mat.standard_cost)), 2)
        ELSE 0.0
    END AS inventory_turnover_ratio,
    CASE 
        WHEN COALESCE(ib.on_hand_units, 0) <= 0 THEN 'OUT_OF_STOCK'
        WHEN COALESCE(ib.on_hand_units, 0) < mat.safety_stock_level THEN 'CRITICAL_SAFETY_BREACH'
        WHEN COALESCE(ib.on_hand_units, 0) < mat.reorder_point THEN 'REORDER_RECOMMENDED'
        WHEN COALESCE(dbr.avg_daily_burn_90d, 0) > 0 AND (COALESCE(ib.on_hand_units, 0) / dbr.avg_daily_burn_90d) > 90.0 THEN 'EXCESS_INVENTORY'
        ELSE 'OPTIMAL'
    END AS safety_stock_status
FROM dim_material mat
CROSS JOIN dim_warehouse wh
LEFT JOIN inventory_balances ib ON mat.material_id = ib.material_id AND wh.warehouse_id = ib.warehouse_id
LEFT JOIN daily_burn_rates dbr ON mat.material_id = dbr.material_id AND wh.warehouse_id = dbr.warehouse_id
WHERE wh.warehouse_type = 'RAW_MATERIALS'
ORDER BY 
    CASE WHEN COALESCE(ib.on_hand_units, 0) <= 0 THEN 1 
         WHEN COALESCE(ib.on_hand_units, 0) < mat.safety_stock_level THEN 2 
         ELSE 3 END,
    mat.is_critical DESC,
    days_of_inventory ASC;


-- ----------------------------------------------------------------------------
-- QUERY 3: Delayed Purchase Order Impact Analysis
-- Aggregates overdue PO value, aging brackets, and associated supplier defect risk
-- ----------------------------------------------------------------------------
WITH delayed_orders AS (
    SELECT 
        po.po_id,
        po.po_number,
        po.supplier_id,
        s.name AS supplier_name,
        s.category AS supplier_category,
        s.reliability_rating,
        po.factory_id,
        f.name AS factory_name,
        po.order_date,
        po.promised_delivery_date,
        CURRENT_DATE - po.promised_delivery_date AS days_overdue,
        po.total_amount,
        COUNT(pol.po_line_id) AS total_lines,
        SUM(CASE WHEN m.is_critical THEN 1 ELSE 0 END) AS critical_materials_count
    FROM fact_purchase_orders po
    JOIN dim_supplier s ON po.supplier_id = s.supplier_id
    JOIN dim_factory f ON po.factory_id = f.factory_id
    JOIN fact_purchase_order_lines pol ON po.po_id = pol.po_id
    JOIN dim_material m ON pol.material_id = m.material_id
    WHERE po.status = 'OVERDUE' OR (po.status = 'IN_TRANSIT' AND po.promised_delivery_date < CURRENT_DATE)
    GROUP BY po.po_id, po.po_number, po.supplier_id, s.name, s.category, s.reliability_rating, 
             po.factory_id, f.name, po.order_date, po.promised_delivery_date, po.total_amount
)
SELECT 
    supplier_name,
    supplier_category,
    reliability_rating,
    COUNT(po_id) AS total_delayed_pos,
    SUM(total_amount) AS total_delayed_value_usd,
    AVG(days_overdue)::NUMERIC(6, 1) AS avg_days_overdue,
    MAX(days_overdue) AS max_days_overdue,
    SUM(critical_materials_count) AS total_critical_lines_impacted,
    SUM(CASE WHEN days_overdue <= 7 THEN total_amount ELSE 0 END) AS value_overdue_1_7_days,
    SUM(CASE WHEN days_overdue BETWEEN 8 AND 14 THEN total_amount ELSE 0 END) AS value_overdue_8_14_days,
    SUM(CASE WHEN days_overdue > 14 THEN total_amount ELSE 0 END) AS value_overdue_gt_14_days,
    CASE 
        WHEN SUM(critical_materials_count) > 0 AND AVG(days_overdue) > 10 THEN 'URGENT_PRODUCTION_HALT_RISK'
        WHEN SUM(critical_materials_count) > 0 THEN 'ELEVATED_SCHEDULE_RISK'
        ELSE 'STANDARD_LOGISTICS_DELAY'
    END AS delay_severity_tier
FROM delayed_orders
GROUP BY supplier_name, supplier_category, reliability_rating
ORDER BY total_delayed_value_usd DESC;


-- ----------------------------------------------------------------------------
-- QUERY 4: Bill of Materials (BOM) Production-at-Risk Quantities & Revenue Impact
-- Cross-examines planned work orders against active shortages and supplier delays
-- ----------------------------------------------------------------------------
WITH active_shortages AS (
    SELECT 
        bom.work_order_id,
        COUNT(bom.material_id) AS shortage_component_count,
        SUM(bom.shortage_quantity) AS total_shortage_units,
        SUM(bom.shortage_quantity * m.standard_cost) AS direct_material_cost_shortfall
    FROM fact_bom_allocations bom
    JOIN dim_material m ON bom.material_id = m.material_id
    WHERE bom.shortage_quantity > 0
    GROUP BY bom.work_order_id
)
SELECT 
    wo.work_order_id,
    wo.product_sku,
    f.name AS factory_name,
    wo.start_date,
    wo.end_date,
    wo.planned_quantity,
    wo.status AS work_order_status,
    wo.priority,
    COALESCE(ash.shortage_component_count, 0) AS shortage_components_count,
    COALESCE(ash.total_shortage_units, 0) AS total_shortage_units,
    COALESCE(ash.direct_material_cost_shortfall, 0) AS material_cost_shortfall_usd,
    -- Valuation of finished goods delayed due to component starvation ($2,500 standard FG value)
    ROUND(wo.planned_quantity * 2500.0, 2) AS finished_goods_value_at_risk,
    CASE 
        WHEN wo.priority = 'CRITICAL' AND COALESCE(ash.shortage_component_count, 0) > 0 THEN 'CRITICAL_LINE_DOWN'
        WHEN COALESCE(ash.shortage_component_count, 0) > 0 THEN 'SCHEDULE_COMPROMISED'
        ELSE 'ON_SCHEDULE'
    END AS operational_impact_status
FROM fact_production_schedules wo
JOIN dim_factory f ON wo.factory_id = f.factory_id
LEFT JOIN active_shortages ash ON wo.work_order_id = ash.work_order_id
WHERE wo.status IN ('PLANNED', 'IN_PROGRESS', 'BLOCKED_SHORTAGE')
ORDER BY 
    CASE WHEN wo.priority = 'CRITICAL' THEN 1 WHEN wo.priority = 'HIGH' THEN 2 ELSE 3 END,
    operational_impact_status ASC,
    finished_goods_value_at_risk DESC;
