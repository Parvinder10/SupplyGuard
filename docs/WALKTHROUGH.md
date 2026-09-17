# Walkthrough: SupplyGuard — Manufacturing Supply-Chain & Inventory Risk Platform

We have built and verified **SupplyGuard**, a production-ready, full-stack Data Integration (DI) and Supply Chain Analytics platform.

---

## 1. Accomplished Deliverables

### A. Realistic Enterprise Dataset Generation
- **Script**: [`data_generator/generate_data.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/data_generator/generate_data.py)
- **Execution & Output**: Generated deterministic, realistic manufacturing datasets exceeding all requirements:
  - **120 Suppliers** across 5 categories, 7 countries, reliability profiles, baseline lead times ($7 - 65$ days), and financial health ratings.
  - **1,200 Materials (SKUs)** with log-normal standard costs, safety stocks, reorder points, and single-source critical BOM components.
  - **6,000 Purchase Orders & 10,230 PO Lines** with order/promised dates, statuses (`DELIVERED`, `OVERDUE`, `IN_TRANSIT`, `PENDING`), and order totals.
  - **110,000 Partitioned Inventory Movements** across 4 factories and 8 warehouses (issues, receipts, scrap, transfers, cycle adjustments).
  - **8,737 Goods Receipts & Quality Inspections** with delivery variance ($actual - promised$) and defect classifications (PPM).
  - **1,500 Production Work Orders & 9,023 BOM Allocations** tracking component allocations and material shortages.

### B. PostgreSQL Star-Schema Warehouse & Advanced SQL
- **DDL & Partitioning**: [`warehouse/schema.sql`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/warehouse/schema.sql)
  - 6 Dimension tables (`dim_supplier`, `dim_material`, `dim_warehouse`, `dim_factory`, `dim_date`, `dim_defect_type`).
  - 7 Fact tables with quarterly range partitioning on `fact_inventory_movements` (`2025_q1` through `2026_q2` + `default`).
  - Operational tables for alerts (`supply_alerts`), incident mitigation (`corrective_actions`), and users (`user_accounts`).
  - 3 Materialized Views:
    1. `mv_supplier_performance` (OTD %, defect PPM, lead time variance, spend, dense category ranking).
    2. `mv_inventory_health_daily` (on-hand stock, burn rates, DOI, safety stock breach status).
    3. `mv_production_at_risk` (upcoming work orders impacted by BOM component shortages, revenue at risk).
- **Calendar Generator**: [`warehouse/dim_date_populate.sql`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/warehouse/dim_date_populate.sql).
- **Analytical Queries Library**: [`warehouse/analytics_queries.sql`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/warehouse/analytics_queries.sql) demonstrating CTEs, `LAG`/`LEAD`, rolling 30/90-day averages, `DENSE_RANK()`, and conditional aggregations.
- **3 Documented Query Optimization Benchmarks**: [`docs/QUERY_OPTIMIZATION_BENCHMARKS.md`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/docs/QUERY_OPTIMIZATION_BENCHMARKS.md) and [`warehouse/optimization_benchmarks.sql`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/warehouse/optimization_benchmarks.sql):
  - **Benchmark 1 (Movements Rolling Balance)**: Partition Pruning + Composite Indexing dropped latency from **438.2 ms $\to$ 3.4 ms** (**128.8x speedup**).
  - **Benchmark 2 (Supplier Scorecard CTEs)**: Eliminating $O(N \times M)$ correlated subqueries dropped latency from **782.6 ms $\to$ 12.1 ms** (**64.6x speedup**).
  - **Benchmark 3 (Multi-Level BOM Shortage)**: Materialized view with index scan dropped latency from **1,340.5 ms $\to$ 2.8 ms** (**478.7x speedup**).

### C. Data Integration, Dead-Letter Rejections & Airflow ETL
- **Schema Validation & Dead-Letter Queue**: [`etl/validator.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/etl/validator.py) uses Pydantic to validate schemas and duplicate keys; invalid records are routed to `etl_rejected_records` while clean records proceed.
- **Idempotent Warehouse Loader**: [`etl/warehouse_loader.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/etl/warehouse_loader.py) supports `ON CONFLICT (...) DO UPDATE` upserts, audit logging (`etl_pipeline_audit`), and concurrent materialized view refreshes.
- **Automated Data Quality Engine**: [`etl/data_quality.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/etl/data_quality.py) executes automated SQL assertions (non-negative stock, referential integrity, chronology, defect PPM bounds) and writes results to `data_quality_test_results`.
- **4 Apache Airflow DAGs**:
  1. [`airflow/dags/supply_chain_ingest_dag.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/airflow/dags/supply_chain_ingest_dag.py): Ingestion, Pydantic validation, dead-letter routing, audit metrics.
  2. [`airflow/dags/supply_chain_warehouse_transform_dag.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/airflow/dags/supply_chain_warehouse_transform_dag.py): Partitioned movement loading and materialized view refresh.
  3. [`airflow/dags/supply_chain_data_quality_dag.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/airflow/dags/supply_chain_data_quality_dag.py): Automated SQL assertion tests and failure alerts.
  4. [`airflow/dags/supply_chain_risk_scoring_dag.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/airflow/dags/supply_chain_risk_scoring_dag.py): ML risk scoring and alert generation.

### D. Explainable ML Risk Engine & Governance
- **Feature Engineering**: [`risk_engine/features.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/risk_engine/features.py) calculates OTD %, lead-time variance std dev, defect PPM, single-source dependency, DOI, and burn rates.
- **Predictive Models**: [`risk_engine/model.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/risk_engine/model.py) implements Gradient Boosting for Supplier Reliability and Random Forest for Material Stockouts, computing normalized local feature attribution percentages.
- **Narrative Explainer**: [`risk_engine/explainer.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/risk_engine/explainer.py) generates natural language explanations and mitigation actions.
- **Quantitative Evaluator & Governance**: [`risk_engine/evaluator.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/risk_engine/evaluator.py) and [`docs/MODEL_GOVERNANCE.md`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/docs/MODEL_GOVERNANCE.md):
  - Supplier Risk Model: MAE: `0.080` | RMSE: `0.102` | ROC-AUC: `1.000` | F1: `1.000`.
  - Stockout Risk Model: MAE: `0.128` | RMSE: `0.672` | ROC-AUC: `1.000` | F1: `0.995`.
  - Formal documentation of 4 operational boundaries (Cold-start threshold, demand non-stationarity, ERP signal boundaries, concession waivers).

### E. Apache Superset 3.0 Provisioning & Dashboards
- **Configuration**: [`superset/superset_config.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/superset/superset_config.py) enables native filters, cross-filtering, and iframe embedding.
- **Auto-Bootstrapper**: [`superset/bootstrap_superset.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/superset/bootstrap_superset.py) provisions database connections and 6 core enterprise dashboards:
  1. Executive Supply-Chain Performance Dashboard
  2. Supplier 360 Scorecards & Risk Matrix
  3. Inventory Intelligence & Safety-Stock Surveillance
  4. Purchase Order Delays & Procurement Velocity
  5. Manufacturing Quality & Defect Diagnostics
  6. Production-at-Risk & Schedule Shortage Analysis

### F. FastAPI REST Backend Services
- **Main Application**: [`backend/main.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/backend/main.py) with CORS and `/health`.
- **Repository Service**: [`backend/services/repository.py`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/backend/services/repository.py) manages queries, state caching, and workflow persistence.
- **Endpoints**:
  - `/api/v1/auth`: JWT login and user authentication.
  - `/api/v1/kpis`: Executive metrics (OTD %, spend at risk, stockout counts).
  - `/api/v1/suppliers`: Searchable supplier directory with scorecards and ML explanations.
  - `/api/v1/materials`: Catalog, current stock balances, and DOI.
  - `/api/v1/purchase-orders`: Status filters and overdue aging analysis.
  - `/api/v1/risk`: Real-time ML scoring and batch predictions.
  - `/api/v1/alerts`: Active alerts list and status updates (`ACKNOWLEDGED`, `RESOLVED`).
  - `/api/v1/corrective-actions`: Mitigation workflow creation, owner assignment, and status transitions.
  - `/api/v1/etl`: Airflow audit logs, dead-letter records, and data quality test results.

### G. React + TypeScript Web Portal
- Built with **Vite**, **React 18**, **TypeScript**, and **Tailwind CSS**:
  - [`ExecutiveDashboard.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/ExecutiveDashboard.tsx): Key metric cards, spend at risk, high-priority alert feed.
  - [`SupplierScorecards.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/SupplierScorecards.tsx) & [`SupplierDetailModal.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/SupplierDetailModal.tsx): Vendor data grid, risk badges, ML attribution progress bars, and natural language explanations.
  - [`InventoryRadar.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/InventoryRadar.tsx): Days of Inventory, safety stock breach indicators, critical BOM filter.
  - [`PurchaseOrders.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/PurchaseOrders.tsx): Order tracking and overdue delay calculations.
  - [`IncidentManagement.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/IncidentManagement.tsx): Incident triage board, owner assignment modal, root-cause documentation, and resolution transitions.
  - [`ETLGovernance.tsx`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/frontend/src/components/ETLGovernance.tsx): Pipeline run audit log viewer, dead-letter rejected record inspector, automated data quality assertion table.

### H. Docker & DevOps Infrastructure
- [`docker-compose.yml`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/docker-compose.yml): 5 orchestrated services (`postgres`, `backend`, `frontend`, `airflow`, `superset`).
- [`docker/Dockerfile.backend`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/docker/Dockerfile.backend) & [`docker/Dockerfile.frontend`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/docker/Dockerfile.frontend).
- [`.github/workflows/ci.yml`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/.github/workflows/ci.yml): Automated CI testing and frontend build.
- [`README.md`](file:///c:/Users/Vishe/Downloads/SUPPLY%20GUARD/README.md): Comprehensive documentation with quickstart, architecture, and API guides.

---

## 2. Verification & Validation Results

### Automated Pytest Suite (`python -m pytest -v tests/`)
```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Vishe\Downloads\SUPPLY GUARD
collected 19 items

tests/test_api.py::test_health_check PASSED                              [  5%]
tests/test_api.py::test_kpis_endpoint PASSED                             [ 10%]
tests/test_api.py::test_suppliers_list_and_filter PASSED                 [ 15%]
tests/test_api.py::test_materials_list PASSED                            [ 21%]
tests/test_api.py::test_purchase_orders PASSED                           [ 26%]
tests/test_api.py::test_alerts_and_corrective_actions_workflow PASSED    [ 31%]
tests/test_api.py::test_etl_governance_endpoints PASSED                  [ 36%]
tests/test_data_generator.py::test_data_generation_quantities PASSED     [ 42%]
tests/test_data_generator.py::test_suppliers_relational_integrity PASSED [ 47%]
tests/test_data_generator.py::test_materials_relational_integrity PASSED [ 52%]
tests/test_data_generator.py::test_goods_receipts_chronology PASSED      [ 57%]
tests/test_data_generator.py::test_inventory_movements_partitions PASSED [ 63%]
tests/test_etl_pipeline.py::test_etl_validator_valid_supplier PASSED     [ 68%]
tests/test_etl_pipeline.py::test_etl_validator_invalid_tier_rejection PASSED [ 73%]
tests/test_etl_pipeline.py::test_etl_validator_duplicate_detection PASSED [ 78%]
tests/test_etl_pipeline.py::test_etl_validator_material_safety_stock_logic PASSED [ 84%]
tests/test_risk_engine.py::test_supplier_feature_extraction PASSED       [ 89%]
tests/test_risk_engine.py::test_supplier_risk_scoring_bounds_and_attribution PASSED [ 94%]
tests/test_risk_engine.py::test_material_stockout_risk_scoring PASSED    [100%]

======================= 19 passed in 11.35s =======================
```

### Frontend TypeScript Build (`npm run build`)
```text
vite v5.4.21 building for production...
✓ 1515 modules transformed.
dist/index.html                   1.15 kB │ gzip:  0.66 kB
dist/assets/index-Np1wr6yR.css   23.04 kB │ gzip:  4.93 kB
dist/assets/index-xfguccXt.js   211.02 kB │ gzip: 59.07 kB
✓ built in 40.70s
```

All source files have been committed cleanly to the Git repository.
