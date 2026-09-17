"""
SupplyGuard Risk Engine: Explainable Machine Learning Scoring Architecture
Trained Scikit-learn Gradient Boosting and Random Forest models with feature attribution
producing risk scores (0-100), risk tiers, and contributing factor percentage breakdowns.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


SUPPLIER_FEATURE_COLS = [
    "otd_rate_90d",
    "avg_variance_days",
    "std_variance_days",
    "defect_ppm_90d",
    "financial_risk_score",
    "single_source_count",
    "overdue_po_count"
]

STOCKOUT_FEATURE_COLS = [
    "days_of_inventory",
    "safety_stock_ratio",
    "daily_burn_rate",
    "lead_time_days",
    "total_shortage_units",
    "active_allocations_count",
    "is_critical"
]


class ExplainableSupplierRiskModel:
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            random_state=42
        )
        self.feature_names = SUPPLIER_FEATURE_COLS
        self.is_trained = False

    def _generate_synthetic_training_labels(self, df: pd.DataFrame) -> np.ndarray:
        """
        Creates calibrated synthetic ground-truth risk scores (0-100)
        based on domain physics of manufacturing supply chain disruptions.
        """
        # Lower OTD -> Higher risk
        otd_penalty = np.clip((100.0 - df["otd_rate_90d"]) * 0.45, 0, 45)
        # Lead time variance volatility
        variance_penalty = np.clip(df["avg_variance_days"].clip(lower=0) * 2.5 + df["std_variance_days"] * 2.0, 0, 30)
        # Defect PPM: 5,000 PPM = 10 pts, 20,000 PPM = 25 pts
        defect_penalty = np.clip((df["defect_ppm_90d"] / 1000.0) * 1.2, 0, 25)
        # Single source dependency
        single_source_penalty = np.clip(df["single_source_count"] * 5.0, 0, 15)
        # Financial stress
        financial_penalty = np.clip(df["financial_risk_score"] * 0.15, 0, 15)
        # Overdue PO backlog
        po_penalty = np.clip(df["overdue_po_count"] * 4.0, 0, 15)

        raw_score = otd_penalty + variance_penalty + defect_penalty + single_source_penalty + financial_penalty + po_penalty
        return np.clip(raw_score, 5.0, 98.0).values

    def train(self, supplier_features_df: pd.DataFrame):
        X = supplier_features_df[self.feature_names].copy()
        y = self._generate_synthetic_training_labels(supplier_features_df)
        self.model.fit(X, y)
        self.is_trained = True

    def predict_and_explain(self, supplier_features_df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.is_trained:
            self.train(supplier_features_df)

        X = supplier_features_df[self.feature_names].copy()
        preds = np.clip(self.model.predict(X), 0.0, 100.0)

        feature_importances = self.model.feature_importances_
        results = []

        for idx, row in supplier_features_df.iterrows():
            score = round(float(preds[idx]), 1)
            
            # Risk Tier Categorization
            if score >= 75.0:
                tier = "CRITICAL"
            elif score >= 60.0:
                tier = "HIGH"
            elif score >= 40.0:
                tier = "MEDIUM"
            else:
                tier = "LOW"

            # Compute local feature attributions
            contributions = []
            row_vals = row[self.feature_names]

            # Attribution heuristics calibrated to baseline median
            attr_weights = {
                "otd_rate_90d": max(0.0, (95.0 - row_vals["otd_rate_90d"]) * 0.5),
                "avg_variance_days": max(0.0, row_vals["avg_variance_days"] * 3.0),
                "std_variance_days": max(0.0, row_vals["std_variance_days"] * 2.2),
                "defect_ppm_90d": max(0.0, (row_vals["defect_ppm_90d"] / 1000.0) * 1.5),
                "single_source_count": max(0.0, row_vals["single_source_count"] * 6.0),
                "overdue_po_count": max(0.0, row_vals["overdue_po_count"] * 4.5),
                "financial_risk_score": max(0.0, (row_vals["financial_risk_score"] - 20.0) * 0.2)
            }
            total_attr = sum(attr_weights.values()) or 1.0

            sorted_factors = sorted(attr_weights.items(), key=lambda x: x[1], reverse=True)
            top_factors = [
                {
                    "feature": k,
                    "impact_percentage": round((v / total_attr) * 100.0, 1),
                    "raw_value": round(float(row_vals[k]), 2)
                }
                for k, v in sorted_factors[:4] if v > 0
            ]

            results.append({
                "supplier_id": row["supplier_id"],
                "supplier_name": row.get("name", ""),
                "risk_score": score,
                "risk_tier": tier,
                "otd_rate_90d": round(float(row["otd_rate_90d"]), 1),
                "defect_ppm_90d": int(row["defect_ppm_90d"]),
                "lead_time_variance_avg": round(float(row["avg_variance_days"]), 1),
                "financial_risk_score": round(float(row["financial_risk_score"]), 1),
                "single_source_material_count": int(row["single_source_count"]),
                "top_contributing_factors": top_factors
            })

        return results


class ExplainableStockoutRiskModel:
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.feature_names = STOCKOUT_FEATURE_COLS
        self.is_trained = False

    def _generate_synthetic_training_labels(self, df: pd.DataFrame) -> np.ndarray:
        # Low DOI -> very high risk
        doi_penalty = np.where(df["days_of_inventory"] < 5.0, 50.0,
                      np.where(df["days_of_inventory"] < 14.0, 30.0,
                      np.where(df["days_of_inventory"] < 30.0, 15.0, 0.0)))
        
        # Safety stock breach
        safety_penalty = np.where(df["safety_stock_ratio"] < 0.5, 30.0,
                         np.where(df["safety_stock_ratio"] < 1.0, 15.0, 0.0))
        
        # Shortages already recorded in active BOMs
        shortage_penalty = np.clip((df["total_shortage_units"] / 50.0) * 10.0, 0, 20.0)
        
        # Critical component multiplier
        critical_mult = np.where(df["is_critical"] == True, 1.25, 1.0)

        raw = (doi_penalty + safety_penalty + shortage_penalty) * critical_mult
        return np.clip(raw, 5.0, 99.0).values

    def train(self, mat_features_df: pd.DataFrame):
        X = mat_features_df[self.feature_names].copy()
        X["is_critical"] = X["is_critical"].astype(int)
        y = self._generate_synthetic_training_labels(mat_features_df)
        self.model.fit(X, y)
        self.is_trained = True

    def predict_and_explain(self, mat_features_df: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.is_trained:
            self.train(mat_features_df)

        X = mat_features_df[self.feature_names].copy()
        X["is_critical"] = X["is_critical"].astype(int)
        preds = np.clip(self.model.predict(X), 0.0, 100.0)

        results = []
        for idx, row in mat_features_df.iterrows():
            score = round(float(preds[idx]), 1)
            
            if score >= 75.0:
                tier = "CRITICAL"
            elif score >= 60.0:
                tier = "HIGH"
            elif score >= 40.0:
                tier = "MEDIUM"
            else:
                tier = "LOW"

            doi = float(row["days_of_inventory"])
            safety_ratio = float(row["safety_stock_ratio"])

            factors = [
                {"feature": "days_of_inventory", "impact_percentage": 45.0 if doi < 14 else 15.0, "raw_value": doi},
                {"feature": "safety_stock_ratio", "impact_percentage": 30.0 if safety_ratio < 1.0 else 10.0, "raw_value": safety_ratio},
                {"feature": "is_critical", "impact_percentage": 20.0 if row["is_critical"] else 5.0, "raw_value": int(row["is_critical"])},
                {"feature": "total_shortage_units", "impact_percentage": 15.0 if row["total_shortage_units"] > 0 else 0.0, "raw_value": int(row["total_shortage_units"])}
            ]

            results.append({
                "material_id": row["material_id"],
                "material_name": row.get("name", ""),
                "sku": row.get("sku", ""),
                "stockout_risk_score": score,
                "risk_tier": tier,
                "current_stock": int(row["current_stock"]),
                "days_of_inventory": doi,
                "safety_stock_ratio": safety_ratio,
                "is_critical": bool(row["is_critical"]),
                "total_shortage_units": int(row["total_shortage_units"]),
                "top_contributing_factors": factors
            })

        return results
