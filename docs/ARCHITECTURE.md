# SupplyGuard: Architecture, Data Modeling & System Design

## 1. Executive Platform Architecture

SupplyGuard is an enterprise manufacturing supply-chain and inventory risk platform engineered for high-throughput operational intelligence. The system aggregates ERP purchase orders, warehouse movements, supplier deliveries, quality inspections, and factory production work orders into an analytical star-schema warehouse, applying predictive machine learning models to detect shortages and vendor failures before production lines halt.

```mermaid
graph TB
    subgraph Data Sources & Generation Layer
        ERP[Enterprise ERP & MES Simulators]
        SCM[Global Logistics & TMS Inbound]
        QC[Shopfloor Quality Inspection Terminals]
        ERP & SCM & QC -->|CSVs / API Webhooks| RawLanding[Raw Ingestion Zone]
    end

    subgraph Orchestration & Data Integration Layer
        Airflow[Apache Airflow 2.9+ DAGs]
        Airflow -->|1. Validate Schema & Detect Duplicates| PydanticVal[Pydantic ETL Validator]
        PydanticVal -->|Failed Assertions| DLQ[etl_rejected_records DLQ]
        PydanticVal -->|Passed Rows| Staging[Staging Schema]
        Airflow -->|2. Idempotent Upserts| DWLoader[Warehouse Loader]
        Airflow -->|3. Data Quality Assertions| DQEngine[DQ Assertion Engine]
        DQEngine -->|Log Assertions| DQTable[data_quality_test_results]
        Airflow -->|4. Pipeline Metrics| AuditTable[etl_pipeline_audit]
    end

    subgraph PostgreSQL 16 Star-Schema Warehouse
        DWLoader --> Dims[Dimension Tables: dim_supplier, dim_material, dim_warehouse, dim_factory, dim_date]
        DWLoader --> PartitionedFacts[Partitioned Movements: 2025_q1, 2025_q2, 2025_q3, 2025_q4, 2026_q1, 2026_q2]
        DWLoader --> OtherFacts[fact_purchase_orders, fact_goods_receipts, fact_quality_inspections, fact_production_schedules]
        PartitionedFacts & OtherFacts --> MV1[mv_supplier_performance]
        PartitionedFacts & OtherFacts --> MV2[mv_inventory_health_daily]
        PartitionedFacts & OtherFacts --> MV3[mv_production_at_risk]
    end

    subgraph Explainable ML & Scoring Layer
        MV1 & MV2 & MV3 --> FeatureStore[Risk Feature Extractor]
        FeatureStore --> Model1[Explainable Supplier Risk: Gradient Boosting]
        FeatureStore --> Model2[Explainable Stockout Risk: Random Forest]
        Model1 & Model2 --> Explainer[Natural Language Attribution Engine]
        Explainer --> RiskScoresDB[fact_supplier_risk_scores & fact_stockout_risk_scores]
        RiskScoresDB --> AlertTrigger[supply_alerts Engine]
    end

    subgraph Application & Consumption Layer
        PostgreSQL[(PostgreSQL Warehouse)] --> Superset[Apache Superset 3.0 Dashboards]
        PostgreSQL --> Backend[FastAPI REST Microservice]
        Backend --> Portal[React + TypeScript Web Portal]
        Portal --> Triage[Corrective Actions & Incident Resolution]
    end
```

---

## 2. PostgreSQL Star-Schema Data Model (ERD)

```mermaid
erDiagram
    dim_supplier ||--o{ fact_purchase_orders : "receives"
    dim_supplier ||--o{ fact_goods_receipts : "ships"
    dim_supplier ||--o{ fact_quality_inspections : "inspected_for"
    dim_supplier ||--o{ fact_supplier_risk_scores : "scored_by"

    dim_material ||--o{ fact_purchase_order_lines : "ordered_in"
    dim_material ||--o{ fact_goods_receipts : "received_in"
    dim_material ||--o{ fact_inventory_movements : "transacted_in"
    dim_material ||--o{ fact_bom_allocations : "allocated_to"
    dim_material ||--o{ fact_stockout_risk_scores : "evaluated_for"

    dim_factory ||--o{ dim_warehouse : "contains"
    dim_factory ||--o{ fact_production_schedules : "hosts"

    dim_warehouse ||--o{ fact_inventory_movements : "stores"
    dim_warehouse ||--o{ fact_purchase_orders : "destination_for"

    fact_purchase_orders ||--|{ fact_purchase_order_lines : "consists_of"
    fact_purchase_order_lines ||--o{ fact_goods_receipts : "fulfilled_by"
    fact_goods_receipts ||--o{ fact_quality_inspections : "verified_by"

    fact_production_schedules ||--|{ fact_bom_allocations : "explodes_into"

    supply_alerts ||--o{ corrective_actions : "mitigated_by"
```

---

## 3. Data Integration & Airflow Pipeline Architecture

The ETL subsystem is engineered around four tenets of enterprise data integration:
1. **Schema Integrity & Dead-Letter Filtering**: Before reaching warehouse staging, every inbound record is strictly checked using Pydantic models. Malformed records, out-of-range parameters, or inverted timestamps are immediately isolated into `etl_rejected_records`, preserving pipeline execution while maintaining strict data governance.
2. **Idempotent Watermarking**: Incremental ingestion leverages `ON CONFLICT (...) DO UPDATE` patterns, allowing pipelines to be safely re-run without producing duplicate records or corrupted aggregations.
3. **Partition Pruning**: The high-volume `fact_inventory_movements` table ($110,000+$ rows) is partitioned by date ranges into quarterly physical sub-tables. Analytics queries filter on partition boundaries, skipping entire historical quarters and improving query latency by $>100\times$.
4. **Automated Data Quality Monitoring**: The `DataQualityEngine` runs validation assertions post-load, logging test metrics, thresholds, and severity tiers to `data_quality_test_results`. If a `CRITICAL` rule fails, an alert is automatically published to `supply_alerts`.

---

## 4. Machine Learning Risk & Attribution Pipeline

```mermaid
flowchart LR
    subgraph Feature Extraction
        A[Inbound Receipts] --> B[OTD 90d & Delay Variance]
        C[Quality Tests] --> D[Defect PPM Rate]
        E[Movements Ledger] --> F[Days of Inventory & Burn Rate]
        G[Purchase Orders] --> H[Overdue Value at Risk]
    end

    subgraph Model Inference
        B & D & H --> M1[Gradient Boosting: Supplier Risk]
        F & H --> M2[Random Forest: Stockout Risk]
    end

    subgraph Explainability & Narrative
        M1 & M2 --> TreeAttribution[Local Feature Attribution %]
        TreeAttribution --> NLEngine[Natural Language Narrative Synthesizer]
        NLEngine --> ActionPlan[Prescribed Mitigation Playbook]
    end
```

---

## 5. Security & Deployment Architecture

- **Containerization**: 5 orchestrated services (`postgres`, `backend`, `frontend`, `airflow`, `superset`) configured in `docker-compose.yml`.
- **Authentication**: Stateless HMAC-SHA256 JWT tokens with role-based access control (`ADMIN`, `PROCUREMENT_LEAD`, `ANALYST`).
- **Reverse Proxy**: Nginx container acts as frontend host and API reverse proxy, eliminating CORS concerns in production.
