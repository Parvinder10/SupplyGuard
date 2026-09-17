"""
SupplyGuard Airflow DAG: Warehouse Transformation & Materialized View Maintenance
Loads facts into partitioned tables, reconciles receipts and inspections,
and triggers concurrent refreshes on analytical materialized views.
"""

from datetime import datetime, timedelta
import os
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "supplyguard_data_platform",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

logger = logging.getLogger("AirflowTransformDAG")


def load_partitioned_inventory_movements(**context):
    import pandas as pd
    from etl.warehouse_loader import WarehouseLoader

    loader = WarehouseLoader()
    run_id = loader.log_pipeline_start("AIRFLOW_MOVEMENTS_LOAD", batch_id=context.get("run_id"))
    data_dir = os.getenv("DATA_DIR", "data")
    mov_path = os.path.join(data_dir, "inventory_movements.csv")

    if os.path.exists(mov_path):
        df = pd.read_csv(mov_path)
        movements = df.to_dict(orient="records")
        loaded = loader.insert_inventory_movements(movements, batch_size=5000)
        loader.log_pipeline_finish(
            run_id=run_id,
            status="SUCCESS",
            rows_extracted=len(movements),
            rows_loaded=loaded,
            rows_rejected=0
        )
        logger.info(f"Loaded {loaded} partitioned inventory movements into PostgreSQL.")
    else:
        loader.log_pipeline_finish(run_id=run_id, status="FAILED", rows_extracted=0, rows_loaded=0, rows_rejected=0, error_message="File not found")


def refresh_warehouse_views(**context):
    from etl.warehouse_loader import WarehouseLoader
    loader = WarehouseLoader()
    loader.refresh_materialized_views()
    logger.info("Materialized views refreshed.")


with DAG(
    "supply_chain_warehouse_transform",
    default_args=default_args,
    description="Loads facts into partitioned tables and refreshes analytical materialized views.",
    schedule_interval="@daily",
    catchup=False,
    tags=["supplyguard", "warehouse", "transformation"]
) as dag:

    load_movements = PythonOperator(
        task_id="load_partitioned_inventory_movements",
        python_callable=load_partitioned_inventory_movements,
        provide_context=True
    )

    refresh_views = PythonOperator(
        task_id="refresh_analytical_materialized_views",
        python_callable=refresh_warehouse_views,
        provide_context=True
    )

    load_movements >> refresh_views
