"""
SupplyGuard: Warehouse Loader & Idempotent Upsert Engine
Provides safe incremental upserts, dead-letter routing to etl_rejected_records,
pipeline audit tracking, and materialized view maintenance.
"""

import os
import sys
import json
import uuid
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, Json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WarehouseLoader")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB", "supplyguard_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")


class WarehouseLoader:
    def __init__(self, host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS):
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def log_pipeline_start(self, pipeline_name: str, batch_id: str = None) -> str:
        run_id = str(uuid.uuid4())
        start_time = datetime.now()
        sql = """
            INSERT INTO etl_pipeline_audit (
                run_id, pipeline_name, batch_id, start_time, status, rows_extracted, rows_loaded, rows_rejected
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (run_id, pipeline_name, batch_id, start_time, "RUNNING", 0, 0, 0))
            conn.commit()
        return run_id

    def log_pipeline_finish(
        self, 
        run_id: str, 
        status: str, 
        rows_extracted: int, 
        rows_loaded: int, 
        rows_rejected: int, 
        error_message: Optional[str] = None
    ):
        end_time = datetime.now()
        sql = """
            UPDATE etl_pipeline_audit
            SET end_time = %s,
                duration_seconds = EXTRACT(EPOCH FROM (%s - start_time)),
                status = %s,
                rows_extracted = %s,
                rows_loaded = %s,
                rows_rejected = %s,
                error_message = %s
            WHERE run_id = %s
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (end_time, end_time, status, rows_extracted, rows_loaded, rows_rejected, error_message, run_id))
            conn.commit()

    def store_rejected_records(self, rejected_records: List[Dict[str, Any]]):
        if not rejected_records:
            return
        sql = """
            INSERT INTO etl_rejected_records (
                pipeline_name, batch_id, source_table, payload, error_code, error_reason
            ) VALUES %s
        """
        tuples = [
            (
                r["pipeline_name"],
                r.get("batch_id"),
                r["source_table"],
                r["payload"],
                r["error_code"],
                r["error_reason"]
            )
            for r in rejected_records
        ]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, tuples)
            conn.commit()
        logger.warning(f"Saved {len(rejected_records)} dead-letter rejected records into etl_rejected_records.")

    def upsert_suppliers(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        sql = """
            INSERT INTO dim_supplier (
                supplier_id, code, name, category, country, city, tier,
                reliability_rating, financial_health_score, baseline_lead_time_days,
                payment_terms, iso_certified, is_active
            ) VALUES %s
            ON CONFLICT (supplier_id) DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                country = EXCLUDED.country,
                city = EXCLUDED.city,
                tier = EXCLUDED.tier,
                reliability_rating = EXCLUDED.reliability_rating,
                financial_health_score = EXCLUDED.financial_health_score,
                baseline_lead_time_days = EXCLUDED.baseline_lead_time_days,
                payment_terms = EXCLUDED.payment_terms,
                iso_certified = EXCLUDED.iso_certified,
                is_active = EXCLUDED.is_active,
                updated_at = CURRENT_TIMESTAMP
        """
        tuples = [
            (
                r["supplier_id"], r["code"], r["name"], r["category"], r["country"], r["city"],
                r["tier"], r["reliability_rating"], r["financial_health_score"], r["baseline_lead_time_days"],
                r["payment_terms"], r["iso_certified"], r.get("is_active", True)
            )
            for r in records
        ]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, tuples)
            conn.commit()
        return len(records)

    def upsert_materials(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        sql = """
            INSERT INTO dim_material (
                material_id, sku, name, category, unit_of_measure, standard_cost,
                current_unit_price, safety_stock_level, reorder_point, target_stock_level,
                min_order_qty, lead_time_days, is_critical, primary_supplier_id, secondary_supplier_id
            ) VALUES %s
            ON CONFLICT (material_id) DO UPDATE SET
                sku = EXCLUDED.sku,
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                unit_of_measure = EXCLUDED.unit_of_measure,
                standard_cost = EXCLUDED.standard_cost,
                current_unit_price = EXCLUDED.current_unit_price,
                safety_stock_level = EXCLUDED.safety_stock_level,
                reorder_point = EXCLUDED.reorder_point,
                target_stock_level = EXCLUDED.target_stock_level,
                min_order_qty = EXCLUDED.min_order_qty,
                lead_time_days = EXCLUDED.lead_time_days,
                is_critical = EXCLUDED.is_critical,
                primary_supplier_id = EXCLUDED.primary_supplier_id,
                secondary_supplier_id = EXCLUDED.secondary_supplier_id,
                updated_at = CURRENT_TIMESTAMP
        """
        tuples = [
            (
                r["material_id"], r["sku"], r["name"], r["category"], r["unit_of_measure"],
                r["standard_cost"], r["current_unit_price"], r["safety_stock_level"],
                r["reorder_point"], r["target_stock_level"], r["min_order_qty"],
                r["lead_time_days"], r["is_critical"], r["primary_supplier_id"],
                r.get("secondary_supplier_id")
            )
            for r in records
        ]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, tuples)
            conn.commit()
        return len(records)

    def upsert_purchase_orders(self, orders: List[Dict[str, Any]]) -> int:
        if not orders:
            return 0
        sql = """
            INSERT INTO fact_purchase_orders (
                po_id, po_number, supplier_id, factory_id, warehouse_id,
                order_date, promised_delivery_date, status, total_amount, currency
            ) VALUES %s
            ON CONFLICT (po_id) DO UPDATE SET
                status = EXCLUDED.status,
                total_amount = EXCLUDED.total_amount,
                promised_delivery_date = EXCLUDED.promised_delivery_date,
                updated_at = CURRENT_TIMESTAMP
        """
        tuples = [
            (
                r["po_id"], r["po_number"], r["supplier_id"], r["factory_id"], r["warehouse_id"],
                r["order_date"], r["promised_delivery_date"], r["status"], r["total_amount"],
                r.get("currency", "USD")
            )
            for r in orders
        ]
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, tuples)
            conn.commit()
        return len(orders)

    def insert_inventory_movements(self, movements: List[Dict[str, Any]], batch_size: int = 5000) -> int:
        if not movements:
            return 0
        sql = """
            INSERT INTO fact_inventory_movements (
                movement_id, material_id, warehouse_id, factory_id,
                movement_date, movement_type, quantity, reference_doc_type, reference_doc_id
            ) VALUES %s
            ON CONFLICT (movement_id, movement_date) DO NOTHING
        """
        total = 0
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(movements), batch_size):
                    chunk = movements[i:i + batch_size]
                    tuples = [
                        (
                            r["movement_id"], r["material_id"], r["warehouse_id"], r["factory_id"],
                            r["movement_date"], r["movement_type"], r["quantity"],
                            r.get("reference_doc_type"), r.get("reference_doc_id")
                        )
                        for r in chunk
                    ]
                    execute_values(cur, sql, tuples)
                    total += len(chunk)
            conn.commit()
        return total

    def refresh_materialized_views(self):
        views = [
            "mv_supplier_performance",
            "mv_inventory_health_daily",
            "mv_production_at_risk"
        ]
        with self.get_connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for v in views:
                    logger.info(f"Refreshing materialized view {v}...")
                    cur.execute(f"REFRESH MATERIALIZED VIEW {v};")
        logger.info("All materialized views refreshed successfully.")
