"""
SupplyGuard Airflow DAG: ML Risk Scoring & Explainability Engine
Extracts features, trains/scores Gradient Boosting & Random Forest models,
generates natural language explanations, logs scores to warehouse, and raises alerts.
"""

from datetime import datetime, timedelta
import os
import logging
import pandas as pd
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

logger = logging.getLogger("AirflowRiskDAG")


def score_and_alert_suppliers(**context):
    from risk_engine.features import RiskFeatureExtractor
    from risk_engine.model import ExplainableSupplierRiskModel
    from risk_engine.explainer import RiskNarrativeExplainer
    from etl.warehouse_loader import WarehouseLoader

    data_dir = os.getenv("DATA_DIR", "data")
    suppliers_df = pd.read_csv(f"{data_dir}/suppliers.csv")
    receipts_df = pd.read_csv(f"{data_dir}/goods_receipts.csv")
    inspections_df = pd.read_csv(f"{data_dir}/quality_inspections.csv")
    pos_df = pd.read_csv(f"{data_dir}/purchase_orders.csv")
    materials_df = pd.read_csv(f"{data_dir}/materials.csv")

    features_df = RiskFeatureExtractor.extract_supplier_features(
        suppliers_df, receipts_df, inspections_df, pos_df, materials_df
    )
    model = ExplainableSupplierRiskModel()
    predictions = model.predict_and_explain(features_df)

    loader = WarehouseLoader()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Log to fact_supplier_risk_scores and trigger alerts for CRITICAL/HIGH
    try:
        with loader.get_connection() as conn:
            with conn.cursor() as cur:
                for p in predictions:
                    expl = RiskNarrativeExplainer.generate_supplier_explanation(p)
                    import json
                    cur.execute("""
                        INSERT INTO fact_supplier_risk_scores (
                            supplier_id, score_date, risk_score, risk_tier,
                            otd_rate_90d, defect_ppm_90d, lead_time_variance_avg,
                            financial_risk_score, single_source_material_count,
                            top_contributing_factors, explanation_text
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (supplier_id, score_date) DO UPDATE SET
                            risk_score = EXCLUDED.risk_score,
                            risk_tier = EXCLUDED.risk_tier,
                            explanation_text = EXCLUDED.explanation_text;
                    """, (
                        p["supplier_id"], today_str, p["risk_score"], p["risk_tier"],
                        p["otd_rate_90d"], p["defect_ppm_90d"], p["lead_time_variance_avg"],
                        p["financial_risk_score"], p["single_source_material_count"],
                        json.dumps(p["top_contributing_factors"]), expl
                    ))

                    if p["risk_tier"] in ("CRITICAL", "HIGH"):
                        cur.execute("""
                            INSERT INTO supply_alerts (
                                alert_id, alert_type, severity, title, message, entity_type, entity_id, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                            ON CONFLICT (alert_id) DO NOTHING;
                        """, (
                            f"ALT-SUP-{p['supplier_id']}-{today_str}",
                            "HIGH_RISK_SUPPLIER",
                            p["risk_tier"],
                            f"Supplier Risk Alert: {p.get('supplier_name', p['supplier_id'])} ({p['risk_tier']})",
                            expl,
                            "SUPPLIER",
                            p["supplier_id"]
                        ))
            conn.commit()
        logger.info(f"Supplier Risk Scoring complete: {len(predictions)} suppliers scored.")
    except Exception as e:
        logger.warning(f"Database connection not available or failed during supplier scoring: {e}")


def score_and_alert_stockouts(**context):
    from risk_engine.features import RiskFeatureExtractor
    from risk_engine.model import ExplainableStockoutRiskModel
    from risk_engine.explainer import RiskNarrativeExplainer
    from etl.warehouse_loader import WarehouseLoader

    data_dir = os.getenv("DATA_DIR", "data")
    materials_df = pd.read_csv(f"{data_dir}/materials.csv")
    movements_df = pd.read_csv(f"{data_dir}/inventory_movements.csv")
    pos_df = pd.read_csv(f"{data_dir}/purchase_orders.csv")
    bom_df = pd.read_csv(f"{data_dir}/bom_allocations.csv")

    features_df = RiskFeatureExtractor.extract_material_features(
        materials_df, movements_df, pos_df, bom_df
    )
    model = ExplainableStockoutRiskModel()
    predictions = model.predict_and_explain(features_df)

    loader = WarehouseLoader()
    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        with loader.get_connection() as conn:
            with conn.cursor() as cur:
                for p in predictions:
                    expl = RiskNarrativeExplainer.generate_stockout_explanation(p)
                    import json
                    cur.execute("""
                        INSERT INTO fact_stockout_risk_scores (
                            material_id, score_date, stockout_risk_score, risk_tier,
                            current_stock, days_of_inventory, safety_stock_ratio,
                            consumption_trend_factor, open_po_count,
                            top_contributing_factors, explanation_text
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (material_id, score_date) DO UPDATE SET
                            stockout_risk_score = EXCLUDED.stockout_risk_score,
                            risk_tier = EXCLUDED.risk_tier,
                            explanation_text = EXCLUDED.explanation_text;
                    """, (
                        p["material_id"], today_str, p["stockout_risk_score"], p["risk_tier"],
                        p["current_stock"], p["days_of_inventory"], p["safety_stock_ratio"],
                        1.0, 1, json.dumps(p["top_contributing_factors"]), expl
                    ))

                    if p["risk_tier"] == "CRITICAL":
                        cur.execute("""
                            INSERT INTO supply_alerts (
                                alert_id, alert_type, severity, title, message, entity_type, entity_id, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                            ON CONFLICT (alert_id) DO NOTHING;
                        """, (
                            f"ALT-MAT-{p['material_id']}-{today_str}",
                            "STOCKOUT",
                            "CRITICAL",
                            f"Critical Stockout Alert: {p.get('sku', p['material_id'])}",
                            expl,
                            "MATERIAL",
                            p["material_id"]
                        ))
            conn.commit()
        logger.info(f"Stockout Risk Scoring complete: {len(predictions)} materials scored.")
    except Exception as e:
        logger.warning(f"Database connection not available or failed during stockout scoring: {e}")


with DAG(
    "supply_chain_ml_risk_scoring",
    default_args=default_args,
    description="Calculates ML supplier and inventory risk scores with explainable attribution.",
    schedule_interval="@daily",
    catchup=False,
    tags=["supplyguard", "machine_learning", "risk_engine"]
) as dag:

    score_suppliers = PythonOperator(
        task_id="score_and_explain_suppliers",
        python_callable=score_and_alert_suppliers,
        provide_context=True
    )

    score_stockouts = PythonOperator(
        task_id="score_and_explain_stockouts",
        python_callable=score_and_alert_stockouts,
        provide_context=True
    )

    score_suppliers >> score_stockouts
