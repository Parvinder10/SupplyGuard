import os
import pytest
import pandas as pd
from risk_engine.features import RiskFeatureExtractor
from risk_engine.model import ExplainableSupplierRiskModel, ExplainableStockoutRiskModel
from risk_engine.explainer import RiskNarrativeExplainer

DATA_DIR = "data"

@pytest.fixture(scope="module")
def loaded_data():
    return {
        "suppliers": pd.read_csv(os.path.join(DATA_DIR, "suppliers.csv")),
        "materials": pd.read_csv(os.path.join(DATA_DIR, "materials.csv")),
        "pos": pd.read_csv(os.path.join(DATA_DIR, "purchase_orders.csv")),
        "receipts": pd.read_csv(os.path.join(DATA_DIR, "goods_receipts.csv")),
        "inspections": pd.read_csv(os.path.join(DATA_DIR, "quality_inspections.csv")),
        "movements": pd.read_csv(os.path.join(DATA_DIR, "inventory_movements.csv")),
        "bom": pd.read_csv(os.path.join(DATA_DIR, "bom_allocations.csv"))
    }

def test_supplier_feature_extraction(loaded_data):
    features_df = RiskFeatureExtractor.extract_supplier_features(
        loaded_data["suppliers"],
        loaded_data["receipts"],
        loaded_data["inspections"],
        loaded_data["pos"],
        loaded_data["materials"]
    )
    assert len(features_df) == len(loaded_data["suppliers"])
    assert "otd_rate_90d" in features_df.columns
    assert "defect_ppm_90d" in features_df.columns
    assert "single_source_count" in features_df.columns

def test_supplier_risk_scoring_bounds_and_attribution(loaded_data):
    features_df = RiskFeatureExtractor.extract_supplier_features(
        loaded_data["suppliers"],
        loaded_data["receipts"],
        loaded_data["inspections"],
        loaded_data["pos"],
        loaded_data["materials"]
    )
    model = ExplainableSupplierRiskModel()
    predictions = model.predict_and_explain(features_df)

    assert len(predictions) == len(features_df)
    for p in predictions:
        score = p["risk_score"]
        assert 0.0 <= score <= 100.0, f"Risk score {score} out of bounds"
        assert p["risk_tier"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        assert len(p["top_contributing_factors"]) > 0
        
        # Check narrative generation
        expl = RiskNarrativeExplainer.generate_supplier_explanation(p)
        assert len(expl) > 20
        assert p["risk_tier"] in expl

def test_material_stockout_risk_scoring(loaded_data):
    features_df = RiskFeatureExtractor.extract_material_features(
        loaded_data["materials"],
        loaded_data["movements"],
        loaded_data["pos"],
        loaded_data["bom"]
    )
    model = ExplainableStockoutRiskModel()
    predictions = model.predict_and_explain(features_df)

    assert len(predictions) == len(features_df)
    for p in predictions:
        score = p["stockout_risk_score"]
        assert 0.0 <= score <= 100.0
        assert p["risk_tier"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        expl = RiskNarrativeExplainer.generate_stockout_explanation(p)
        assert len(expl) > 20
