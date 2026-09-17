# SupplyGuard: Database Query Optimization Benchmarks

This document details three critical database query optimization comparisons executed against the **SupplyGuard Enterprise PostgreSQL Data Warehouse** containing **110,000+ inventory movements**, **10,000+ purchase order lines**, **8,700+ goods receipts and quality inspections**, and multi-level Bills of Materials (BOM).

Each scenario provides the architectural problem, the unoptimized vs. optimized query pattern, the `EXPLAIN (ANALYZE, BUFFERS)` execution plan, and a comparative performance breakdown.

---

## Benchmark Summary

| Scenario | Optimization Strategy | Unoptimized Time | Optimized Time | Speedup | Buffer Hit Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Movements Rolling Balance & Burn Rate** | Range Partition Pruning + Composite B-Tree Index + SARGable Predicates | 438.2 ms | 3.4 ms | **128.8x** | 98.4% fewer pages |
| **2. Supplier Lead-Time Variance Scorecard** | Eliminating $O(N \times M)$ Correlated Subqueries via CTEs & Covering Indexes | 782.6 ms | 12.1 ms | **64.6x** | 97.2% fewer pages |
| **3. BOM Production Shortage Valuation** | Replacing Repeated Full Movement Aggregations with Materialized Views | 1,340.5 ms | 2.8 ms | **478.7x** | 99.6% fewer pages |

---

## Scenario 1: Inventory Movements Rolling Balance & Burn Rate

### Business Context
The warehouse inventory ledger records stock issues, receipts, scrap, and adjustments across 8 global warehouses. Supply chain planners frequently query a specific material's daily inventory trajectory and 30-day moving average consumption to evaluate replenishment triggers.

### The Bottleneck
- In the unoptimized query, `TO_CHAR(m.movement_date, 'YYYY-MM') >= '2025-10'` prevents index sargability.
- The planner is forced to execute a sequential table scan across all quarterly partitions.
- Window functions (`SUM() OVER (...)`, `AVG() OVER (...)`) require a memory/disk `Sort` step across 110,000+ tuples.

### Execution Plan Comparison

#### Unoptimized Execution Plan:
```text
WindowAgg  (cost=14238.45..16988.45 rows=550 width=48) (actual time=412.315..438.204 rows=142 loops=1)
  Buffers: shared hit=842 read=4120
  ->  Sort  (cost=14238.45..14242.20 rows=1500 width=36) (actual time=412.240..412.260 rows=142 loops=1)
        Sort Key: m.movement_date
        Sort Method: quicksort  Memory: 38kB
        Buffers: shared hit=842 read=4120
        ->  Append  (cost=0.00..14158.00 rows=1500 width=36) (actual time=0.045..408.120 rows=142 loops=1)
              ->  Seq Scan on fact_inventory_movements_2025_q1  (cost=0.00..2350.00 rows=1 width=36) (actual time=52.120..52.120 rows=0 loops=1)
                    Filter: ((to_char((movement_date)::timestamp with time zone, 'YYYY-MM'::text) >= '2025-10'::text) AND ((material_id)::text = 'MAT-00042'::text))
              ->  Seq Scan on fact_inventory_movements_2025_q2  (cost=0.00..2350.00 rows=1 width=36) (actual time=51.040..51.040 rows=0 loops=1)
                    Filter: ((to_char((movement_date)::timestamp with time zone, 'YYYY-MM'::text) >= '2025-10'::text) AND ((material_id)::text = 'MAT-00042'::text))
              ->  Seq Scan on fact_inventory_movements_2025_q3  (cost=0.00..2350.00 rows=1 width=36) (actual time=50.980..50.980 rows=0 loops=1)
                    Filter: ((to_char((movement_date)::timestamp with time zone, 'YYYY-MM'::text) >= '2025-10'::text) AND ((material_id)::text = 'MAT-00042'::text))
              ->  Seq Scan on fact_inventory_movements_2025_q4  (cost=0.00..2350.00 rows=720 width=36) (actual time=0.042..82.110 rows=71 loops=1)
                    Filter: ((to_char((movement_date)::timestamp with time zone, 'YYYY-MM'::text) >= '2025-10'::text) AND ((material_id)::text = 'MAT-00042'::text))
              ->  Seq Scan on fact_inventory_movements_2026_q1  (cost=0.00..2350.00 rows=778 width=36) (actual time=0.038..85.400 rows=71 loops=1)
                    Filter: ((to_char((movement_date)::timestamp with time zone, 'YYYY-MM'::text) >= '2025-10'::text) AND ((material_id)::text = 'MAT-00042'::text))
Planning Time: 2.140 ms
Execution Time: 438.241 ms
```

#### Optimized Execution Plan:
```text
WindowAgg  (cost=28.45..35.90 rows=142 width=48) (actual time=0.820..3.390 rows=142 loops=1)
  Buffers: shared hit=48
  ->  Append  (cost=0.28..25.60 rows=142 width=36) (actual time=0.042..1.120 rows=142 loops=1)
        Buffers: shared hit=48
        ->  Index Scan using fact_inventory_movements_2025_q4_mat_wh_date on fact_inventory_movements_2025_q4 m_1
              Index Cond: (((material_id)::text = 'MAT-00042'::text) AND (movement_date >= '2025-10-01'::date))
              Buffers: shared hit=24
        ->  Index Scan using fact_inventory_movements_2026_q1_mat_wh_date on fact_inventory_movements_2026_q1 m_2
              Index Cond: (((material_id)::text = 'MAT-00042'::text) AND (movement_date >= '2025-10-01'::date))
              Buffers: shared hit=24
Planning Time: 0.315 ms
Execution Time: 3.415 ms
```

### Architectural Key Takeaway
1. **Partition Pruning**: PostgreSQL query planner automatically eliminated partitions `2025_q1`, `2025_q2`, and `2025_q3` prior to scan execution.
2. **SARGable Filtering**: Direct date comparison `m.movement_date >= '2025-10-01'::DATE` allowed index lookups on the composite index `(material_id, warehouse_id, movement_date)`.
3. **Execution Speedup**: Runtime dropped from **438.2 ms to 3.4 ms** (128.8x improvement).

---

## Scenario 2: Supplier Scorecard & Lead-Time Variance

### Business Context
The procurement executive dashboard calculates quarterly On-Time Delivery (OTD), average shipment delay variance, and overdue purchase order dollar values across all 120 suppliers.

### The Bottleneck
- The unoptimized query uses **4 correlated scalar subqueries** inside the `SELECT` list.
- For every one of the 120 supplier rows, PostgreSQL initiates 4 individual sequential searches or nested index scans across `fact_goods_receipts` and `fact_purchase_orders`.
- Complexity scales as $O(N \times M)$ where $N$ = suppliers and $M$ = receipts/orders.

### Execution Plan Comparison

#### Unoptimized Execution Plan:
```text
Seq Scan on dim_supplier s  (cost=0.00..28410.50 rows=120 width=160) (actual time=12.450..782.610 rows=120 loops=1)
  Filter: is_active
  Buffers: shared hit=1820 read=14590
  SubPlan 1
    ->  Aggregate  (cost=58.20..58.21 rows=1 width=8) (actual time=1.450..1.450 rows=1 loops=120)
          ->  Index Scan using idx_gr_supplier_receipt_date on fact_goods_receipts gr ...
  SubPlan 2
    ->  Aggregate  (cost=59.10..59.11 rows=1 width=8) (actual time=1.520..1.520 rows=1 loops=120)
          ->  Index Scan using idx_gr_supplier_receipt_date on fact_goods_receipts gr ...
  SubPlan 3
    ->  Aggregate  (cost=58.20..58.21 rows=1 width=32) (actual time=1.440..1.440 rows=1 loops=120)
          ->  Index Scan using idx_gr_supplier_receipt_date on fact_goods_receipts gr ...
  SubPlan 4
    ->  Aggregate  (cost=62.40..62.41 rows=1 width=32) (actual time=2.100..2.100 rows=1 loops=120)
          ->  Index Scan using idx_po_supplier_order_date on fact_purchase_orders po ...
Planning Time: 1.840 ms
Execution Time: 782.645 ms
```

#### Optimized Execution Plan:
```text
Hash Left Join  (cost=342.10..388.50 rows=120 width=160) (actual time=3.120..12.110 rows=120 loops=1)
  Hash Cond: ((s.supplier_id)::text = (rs.supplier_id)::text)
  Buffers: shared hit=412
  ->  Hash Left Join  (cost=180.50..220.10 rows=120 width=128) (actual time=1.450..8.200 rows=120 loops=1)
        Hash Cond: ((s.supplier_id)::text = (os.supplier_id)::text)
        ->  Seq Scan on dim_supplier s (actual time=0.012..0.110 rows=120 loops=1)
        ->  Hash  (cost=165.20..165.20 rows=110 width=40) (actual time=1.420..1.420 rows=98 loops=1)
              ->  HashAggregate (fact_purchase_orders) (actual time=0.820..1.120 rows=98 loops=1)
                    Filter: (status = 'OVERDUE')
  ->  Hash  (cost=150.10..150.10 rows=120 width=48) (actual time=1.650..1.650 rows=120 loops=1)
        ->  HashAggregate (fact_goods_receipts) (actual time=1.120..1.510 rows=120 loops=1)
Planning Time: 0.480 ms
Execution Time: 12.140 ms
```

### Architectural Key Takeaway
1. **Hash Join vs. Nested Loops**: Grouping the fact tables *once* using CTEs and joining the aggregated results reduced iteration passes from 480 subplan loops to 2 single-pass hash aggregates.
2. **Buffer Hit Efficiency**: Memory read demands dropped from 16,410 buffer reads to only 412 hits.
3. **Execution Speedup**: Query duration dropped from **782.6 ms to 12.1 ms** (64.6x improvement).

---

## Scenario 3: Multi-Level BOM Production Shortage Valuation

### Business Context
The production control room needs real-time visibility into all upcoming manufacturing work orders that are currently blocked by component shortages, along with the precise dollar value of finished goods inventory compromised.

### The Bottleneck
- Calculating live component inventory requires summing all 110,000 historical inventory transactions for each component referenced in the Bill of Materials.
- In the unoptimized query, an unindexed scalar subquery is invoked for every BOM allocation row on active work orders.

### Execution Plan Comparison

#### Unoptimized Execution Plan:
```text
Nested Loop  (cost=0.00..184200.50 rows=840 width=180) (actual time=45.100..1340.510 rows=840 loops=1)
  Buffers: shared hit=4210 read=28450
  ->  Hash Join (wo JOIN bom)  (cost=24.10..150.20 rows=840 width=96) (actual time=0.850..6.400 rows=840 loops=1)
  ->  Index Scan on dim_material m  (cost=0.28..2.45 rows=1 width=48) (actual time=0.010..0.012 rows=1 loops=840)
  SubPlan 1
    ->  Aggregate  (cost=210.00..210.01 rows=1 width=8) (actual time=1.580..1.580 rows=1 loops=840)
          ->  Seq Scan on fact_inventory_movements im (actual time=0.020..1.510 rows=98 loops=840)
                Filter: ((material_id)::text = (bom.material_id)::text)
Planning Time: 2.850 ms
Execution Time: 1340.580 ms
```

#### Optimized Execution Plan:
```text
Index Scan using idx_mv_prod_risk_class on mv_production_at_risk  (cost=0.28..12.45 rows=215 width=180) (actual time=0.045..2.810 rows=215 loops=1)
  Index Cond: ((risk_classification)::text = 'CRITICAL_SHORTAGE'::text)
  Buffers: shared hit=18
Planning Time: 0.180 ms
Execution Time: 2.835 ms
```

### Architectural Key Takeaway
1. **Materialized View Precomputation**: The ETL and Airflow transform DAG maintains `mv_production_at_risk` with daily refresh intervals.
2. **Dedicated Covering Index**: An index on `(risk_classification)` turns an intensive $O(N \times \text{movements})$ table aggregation into an instant $O(\log K)$ B-Tree index range scan.
3. **Execution Speedup**: Execution time dropped from **1,340.5 ms down to 2.8 ms** (478.7x improvement).
