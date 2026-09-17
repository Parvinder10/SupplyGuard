"""
SupplyGuard: Explainable AI Natural Language Narrative Generator
Translates ML risk scores, attribution factors, and supply chain telemetry
into clear, actionable executive summaries and mitigation recommendations.
"""

from typing import Dict, Any, List


class RiskNarrativeExplainer:
    FEATURE_FRIENDLY_NAMES = {
        "otd_rate_90d": "On-Time Delivery Degradation",
        "avg_variance_days": "Excess Delivery Delay Variance",
        "std_variance_days": "Lead-Time Volatility",
        "defect_ppm_90d": "Elevated Defect PPM Rate",
        "financial_risk_score": "Supplier Financial Distress",
        "single_source_count": "Single-Source Material Bottleneck",
        "overdue_po_count": "Overdue PO Order Backlog",
        "days_of_inventory": "Depleted Days of Inventory (DOI)",
        "safety_stock_ratio": "Safety Stock Threshold Breach",
        "is_critical": "Critical Path BOM Component",
        "total_shortage_units": "Active Work Order Shortage"
    }

    @classmethod
    def generate_supplier_explanation(cls, prediction: Dict[str, Any]) -> str:
        score = prediction["risk_score"]
        tier = prediction["risk_tier"]
        name = prediction.get("supplier_name", prediction["supplier_id"])
        top_factors = prediction.get("top_contributing_factors", [])

        factor_phrases = []
        for idx, f in enumerate(top_factors[:3], 1):
            feat_label = cls.FEATURE_FRIENDLY_NAMES.get(f["feature"], f["feature"])
            pct = f["impact_percentage"]
            val = f["raw_value"]
            if f["feature"] == "otd_rate_90d":
                detail = f"current OTD at {val:.1f}%"
            elif f["feature"] == "defect_ppm_90d":
                detail = f"defect rate at {val:,.0f} PPM"
            elif f["feature"] == "avg_variance_days":
                detail = f"average delivery slip +{val:.1f} days"
            elif f["feature"] == "single_source_count":
                detail = f"exclusive supplier for {int(val)} critical SKUs"
            else:
                detail = f"metric value {val}"
            factor_phrases.append(f"({idx}) {feat_label} ({pct:.0f}% contribution; {detail})")

        drivers_text = "; ".join(factor_phrases) if factor_phrases else "Standard historical baseline"

        if tier == "CRITICAL":
            recommendation = "IMMEDIATE MITIGATION: Dual-source critical parts immediately, enforce mandatory lot quality inspections, and issue formal supplier corrective action request (SCAR)."
        elif tier == "HIGH":
            recommendation = "RECOMMENDED ACTION: Expedite buffer stock orders, increase incoming QC sample rates, and schedule operational review with vendor leadership."
        elif tier == "MEDIUM":
            recommendation = "MONITOR: Track next 3 inbound shipments for lead-time stabilization and verify quality certs."
        else:
            recommendation = "MAINTAIN: Supplier operating within acceptable tolerances. Eligible for preferred vendor rebate tiers."

        return f"{tier} RISK (Score: {score}/100) for {name}. Primary disruption drivers: {drivers_text}. {recommendation}"

    @classmethod
    def generate_stockout_explanation(cls, prediction: Dict[str, Any]) -> str:
        score = prediction["stockout_risk_score"]
        tier = prediction["risk_tier"]
        sku = prediction.get("sku", prediction["material_id"])
        doi = prediction.get("days_of_inventory", 0.0)
        safety_ratio = prediction.get("safety_stock_ratio", 0.0)
        shortage = prediction.get("total_shortage_units", 0)

        conditions = []
        if doi < 7.0:
            conditions.append(f"critically low inventory covering only {doi:.1f} days of production")
        elif doi < 15.0:
            conditions.append(f"below-target buffer with {doi:.1f} days of inventory remaining")

        if safety_ratio < 0.5:
            conditions.append(f"operating at {safety_ratio * 100:.0f}% of minimum safety threshold")

        if shortage > 0:
            conditions.append(f"{shortage:,} units already short across active production schedules")

        cond_text = ", ".join(conditions) if conditions else "inventory levels tracking near reorder trigger"

        if tier in ("CRITICAL", "HIGH"):
            action = "Trigger emergency spot-buy purchase order and resequence scheduled factory work orders."
        else:
            action = "Initiate planned reorder replenishment through standard procurement channels."

        return f"{tier} STOCKOUT RISK (Score: {score}/100) on SKU {sku}. Condition: {cond_text}. Action: {action}"
