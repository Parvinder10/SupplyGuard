"""
SupplyGuard Risk Engine: Feature Engineering Pipeline
Extracts multi-dimensional telemetry across delivery variance, defect rates,
inventory velocity, BOM dependencies, and financial proxies to feed the ML risk models.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


class RiskFeatureExtractor:
    @staticmethod
    def extract_supplier_features(
        suppliers_df: pd.DataFrame,
        receipts_df: pd.DataFrame,
        inspections_df: pd.DataFrame,
        pos_df: pd.DataFrame,
        materials_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Computes predictive risk features for suppliers.
        """
        features = []

        # 1. Receipts & Delivery Variance
        rec_grouped = receipts_df.groupby("supplier_id")
        otd_metrics = rec_grouped.agg(
            total_deliveries=("receipt_id", "count"),
            on_time_deliveries=("delivery_variance_days", lambda x: (x <= 0).sum()),
            avg_variance_days=("delivery_variance_days", "mean"),
            std_variance_days=("delivery_variance_days", "std")
        ).reset_index()
        otd_metrics["otd_rate_90d"] = (otd_metrics["on_time_deliveries"] / otd_metrics["total_deliveries"]) * 100.0
        otd_metrics["std_variance_days"] = otd_metrics["std_variance_days"].fillna(0.0)

        # 2. Quality & Defect PPM
        insp_grouped = inspections_df.groupby("supplier_id")
        qc_metrics = insp_grouped.agg(
            total_sample=("sample_size", "sum"),
            total_defects=("defect_count", "sum")
        ).reset_index()
        qc_metrics["defect_ppm_90d"] = np.where(
            qc_metrics["total_sample"] > 0,
            (qc_metrics["total_defects"] / qc_metrics["total_sample"]) * 1_000_000,
            0.0
        )

        # 3. Overdue Spend & PO Count
        overdue_pos = pos_df[pos_df["status"] == "OVERDUE"]
        overdue_metrics = overdue_pos.groupby("supplier_id").agg(
            overdue_po_count=("po_id", "count"),
            overdue_spend_usd=("total_amount", "sum")
        ).reset_index()

        # 4. Critical Material Dependencies (Single-Source Exposure)
        single_source_mats = materials_df[materials_df["secondary_supplier_id"].isna() & (materials_df["is_critical"] == True)]
        dep_metrics = single_source_mats.groupby("primary_supplier_id").agg(
            single_source_count=("material_id", "count")
        ).reset_index().rename(columns={"primary_supplier_id": "supplier_id"})

        # Merge onto suppliers_df
        merged = suppliers_df.copy()
        merged = merged.merge(otd_metrics, on="supplier_id", how="left")
        merged = merged.merge(qc_metrics, on="supplier_id", how="left")
        merged = merged.merge(overdue_metrics, on="supplier_id", how="left")
        merged = merged.merge(dep_metrics, on="supplier_id", how="left")

        # Fill defaults for suppliers with zero historical events
        merged["otd_rate_90d"] = merged["otd_rate_90d"].fillna(merged["reliability_rating"])
        merged["avg_variance_days"] = merged["avg_variance_days"].fillna(0.0)
        merged["std_variance_days"] = merged["std_variance_days"].fillna(1.0)
        merged["defect_ppm_90d"] = merged["defect_ppm_90d"].fillna(500.0)
        merged["overdue_po_count"] = merged["overdue_po_count"].fillna(0).astype(int)
        merged["overdue_spend_usd"] = merged["overdue_spend_usd"].fillna(0.0)
        merged["single_source_count"] = merged["single_source_count"].fillna(0).astype(int)
        merged["financial_risk_score"] = 100.0 - merged["financial_health_score"]

        return merged

    @staticmethod
    def extract_material_features(
        materials_df: pd.DataFrame,
        movements_df: pd.DataFrame,
        pos_df: pd.DataFrame,
        bom_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Computes stockout and supply interruption features for materials.
        """
        # Current Stock on Hand
        stock_agg = movements_df.groupby("material_id").agg(
            current_stock=("quantity", "sum")
        ).reset_index()

        # 30-Day Burn Rate
        consumed_movements = movements_df[movements_df["quantity"] < 0].copy()
        burn_agg = consumed_movements.groupby("material_id").agg(
            total_consumed_30d=("quantity", lambda x: abs(x.sum()))
        ).reset_index()
        burn_agg["daily_burn_rate"] = (burn_agg["total_consumed_30d"] / 90.0).clip(lower=0.1)

        # Pending Replenishments
        open_pos = pos_df[pos_df["status"].isin(["PENDING", "IN_TRANSIT"])]
        # We estimate PO lines from total POs
        po_counts = open_pos.groupby("warehouse_id").agg(open_pos_count=("po_id", "count")).reset_index()

        # Work Order Allocations (Shortage Pressure)
        bom_agg = bom_df.groupby("material_id").agg(
            active_allocations_count=("allocation_id", "count"),
            total_required_units=("required_quantity", "sum"),
            total_shortage_units=("shortage_quantity", "sum")
        ).reset_index()

        merged = materials_df.copy()
        merged = merged.merge(stock_agg, on="material_id", how="left")
        merged = merged.merge(burn_agg, on="material_id", how="left")
        merged = merged.merge(bom_agg, on="material_id", how="left")

        merged["current_stock"] = merged["current_stock"].fillna(100).clip(lower=0)
        merged["daily_burn_rate"] = merged["daily_burn_rate"].fillna(5.0)
        merged["days_of_inventory"] = (merged["current_stock"] / merged["daily_burn_rate"]).round(1)
        merged["safety_stock_ratio"] = (merged["current_stock"] / merged["safety_stock_level"].clip(lower=1)).round(2)
        merged["total_shortage_units"] = merged["total_shortage_units"].fillna(0).astype(int)
        merged["active_allocations_count"] = merged["active_allocations_count"].fillna(0).astype(int)

        return merged
