"""
SupplyGuard Airflow DAG: Automated Data Quality Assurance
Executes SQL assertion suite, evaluates metric bounds, logs to data_quality_test_results,
and triggers operational incident alerts when critical thresholds fail.
"""

from datetime import datetime, timedelta
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

logger = logging.getLogger("AirflowDQDAG")


def run_data_quality_checks(**context):
    from etl.data_quality import DataQualityEngine
    engine = DataQualityEngine()
    results = engine.run_all_assertions(run_id=context.get("run_id"))
    
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        logger.warning(f"Data Quality Assertions failed: {len(failures)} critical failures detected.")
        # Trigger an alert in supply_alerts if a database connection is active
        try:
            with engine.get_connection() as conn:
                with conn.cursor() as cur:
                    for f in failures:
                        cur.execute("""
                            INSERT INTO supply_alerts (
                                alert_id, alert_type, severity, title, message, entity_type, entity_id, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                            ON CONFLICT (alert_id) DO NOTHING;
                        """, (
                            f"DQ-ALERT-{f['test_name']}",
                            "DATA_QUALITY_FAILURE",
                            f["severity"],
                            f"Data Quality Assertion Failed: {f['test_name']}",
                            f["details"],
                            "SYSTEM_TABLE",
                            f["target_table"]
                        ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record DQ incident alert: {e}")
    else:
        logger.info("All Data Quality Assertions passed successfully.")


with DAG(
    "supply_chain_data_quality_pipeline",
    default_args=default_args,
    description="Automated SQL data quality assertions with automated alert triage.",
    schedule_interval="@daily",
    catchup=False,
    tags=["supplyguard", "governance", "data_quality"]
) as dag:

    dq_task = PythonOperator(
        task_id="run_data_quality_suite",
        python_callable=run_data_quality_checks,
        provide_context=True
    )
