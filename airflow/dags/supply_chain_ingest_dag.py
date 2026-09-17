"""
SupplyGuard Airflow DAG: Ingestion & Dead-Letter Filtering
Validates raw inbound data batches, routes corrupt or duplicate rows to etl_rejected_records,
stages valid rows, and logs comprehensive pipeline audit metrics.
"""

from datetime import datetime, timedelta
import os
import json
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default Airflow args
default_args = {
    "owner": "supplyguard_data_platform",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

logger = logging.getLogger("AirflowIngestDAG")


def extract_and_validate_inbound(**context):
    import pandas as pd
    from etl.validator import ETLValidator
    from etl.warehouse_loader import WarehouseLoader

    loader = WarehouseLoader()
    run_id = loader.log_pipeline_start("AIRFLOW_INGESTION_PIPELINE", batch_id=context.get("run_id"))
    data_dir = os.getenv("DATA_DIR", "data")
    
    total_extracted = 0
    total_valid = 0
    total_rejected = 0

    entities = ["suppliers", "materials", "purchase_orders"]
    for entity in entities:
        filepath = os.path.join(data_dir, f"{entity}.csv")
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue

        df = pd.read_csv(filepath)
        records = df.to_dict(orient="records")
        total_extracted += len(records)

        valid_recs, rejected_recs = ETLValidator.validate_records(
            entity_name=entity,
            records=records,
            pipeline_name="AIRFLOW_INGESTION_PIPELINE",
            batch_id=context.get("run_id")
        )

        total_valid += len(valid_recs)
        total_rejected += len(rejected_recs)

        if rejected_recs:
            loader.store_rejected_records(rejected_recs)

        # Stage or upsert valid records
        if entity == "suppliers":
            loader.upsert_suppliers(valid_recs)
        elif entity == "materials":
            loader.upsert_materials(valid_recs)
        elif entity == "purchase_orders":
            loader.upsert_purchase_orders(valid_recs)

    loader.log_pipeline_finish(
        run_id=run_id,
        status="SUCCESS",
        rows_extracted=total_extracted,
        rows_loaded=total_valid,
        rows_rejected=total_rejected
    )
    logger.info(f"Ingestion batch completed: {total_valid} loaded, {total_rejected} rejected.")


with DAG(
    "supply_chain_ingestion_pipeline",
    default_args=default_args,
    description="Ingests inbound ERP files with schema validation, dead-letter routing, and audit logs.",
    schedule_interval="@daily",
    catchup=False,
    tags=["supplyguard", "ingestion", "etl"]
) as dag:

    ingest_task = PythonOperator(
        task_id="extract_validate_stage_inbound",
        python_callable=extract_and_validate_inbound,
        provide_context=True
    )
