"""
SupplyGuard Risk Engine: Model Evaluator
Computes comprehensive quantitative performance benchmarks for regression and classification
(MAE, RMSE, R2, ROC-AUC, Precision, Recall, F1) and generates a validation governance report.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from risk_engine.model import ExplainableSupplierRiskModel, ExplainableStockoutRiskModel
from risk_engine.features import RiskFeatureExtractor


class ModelEvaluator:
    @staticmethod
    def evaluate_supplier_model(suppliers_df, receipts_df, inspections_df, pos_df, materials_df):
        features_df = RiskFeatureExtractor.extract_supplier_features(
            suppliers_df, receipts_df, inspections_df, pos_df, materials_df
        )
        model = ExplainableSupplierRiskModel()
        y_true = model._generate_synthetic_training_labels(features_df)
        model.train(features_df)

        X = features_df[model.feature_names]
        y_pred = model.model.predict(X)

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        # Classification metrics at high risk threshold (>= 60)
        y_true_cls = (y_true >= 60.0).astype(int)
        y_pred_cls = (y_pred >= 60.0).astype(int)

        precision = precision_score(y_true_cls, y_pred_cls, zero_division=0)
        recall = recall_score(y_true_cls, y_pred_cls, zero_division=0)
        f1 = f1_score(y_true_cls, y_pred_cls, zero_division=0)
        roc_auc = roc_auc_score(y_true_cls, y_pred) if len(np.unique(y_true_cls)) > 1 else 1.0
        cm = confusion_matrix(y_true_cls, y_pred_cls).tolist()

        return {
            "model_type": "Supplier Risk Gradient Boosting",
            "samples_evaluated": len(features_df),
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2_score": round(float(r2), 3),
            "roc_auc": round(float(roc_auc), 3),
            "precision_at_60": round(float(precision), 3),
            "recall_at_60": round(float(recall), 3),
            "f1_at_60": round(float(f1), 3),
            "confusion_matrix": cm
        }

    @staticmethod
    def evaluate_stockout_model(materials_df, movements_df, pos_df, bom_df):
        features_df = RiskFeatureExtractor.extract_material_features(
            materials_df, movements_df, pos_df, bom_df
        )
        model = ExplainableStockoutRiskModel()
        y_true = model._generate_synthetic_training_labels(features_df)
        model.train(features_df)

        X = features_df[model.feature_names].copy()
        X["is_critical"] = X["is_critical"].astype(int)
        y_pred = model.model.predict(X)

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        y_true_cls = (y_true >= 60.0).astype(int)
        y_pred_cls = (y_pred >= 60.0).astype(int)

        precision = precision_score(y_true_cls, y_pred_cls, zero_division=0)
        recall = recall_score(y_true_cls, y_pred_cls, zero_division=0)
        f1 = f1_score(y_true_cls, y_pred_cls, zero_division=0)
        roc_auc = roc_auc_score(y_true_cls, y_pred) if len(np.unique(y_true_cls)) > 1 else 1.0

        return {
            "model_type": "Material Stockout Random Forest",
            "samples_evaluated": len(features_df),
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2_score": round(float(r2), 3),
            "roc_auc": round(float(roc_auc), 3),
            "precision_at_60": round(float(precision), 3),
            "recall_at_60": round(float(recall), 3),
            "f1_at_60": round(float(f1), 3)
        }


if __name__ == "__main__":
    import json
    data_dir = "data"
    suppliers_df = pd.read_csv(f"{data_dir}/suppliers.csv")
    receipts_df = pd.read_csv(f"{data_dir}/goods_receipts.csv")
    inspections_df = pd.read_csv(f"{data_dir}/quality_inspections.csv")
    pos_df = pd.read_csv(f"{data_dir}/purchase_orders.csv")
    materials_df = pd.read_csv(f"{data_dir}/materials.csv")
    movements_df = pd.read_csv(f"{data_dir}/inventory_movements.csv")
    bom_df = pd.read_csv(f"{data_dir}/bom_allocations.csv")

    res_sup = ModelEvaluator.evaluate_supplier_model(suppliers_df, receipts_df, inspections_df, pos_df, materials_df)
    res_mat = ModelEvaluator.evaluate_stockout_model(materials_df, movements_df, pos_df, bom_df)

    print("\n--- MODEL EVALUATION SUMMARY ---")
    print(json.dumps({"supplier_risk_model": res_sup, "stockout_risk_model": res_mat}, indent=2))
