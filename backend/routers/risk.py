from typing import List, Dict, Any
from fastapi import APIRouter
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

@router.get("/suppliers")
def get_all_supplier_risk_scores():
    repo = SupplyGuardRepository()
    return repo.supplier_predictions

@router.get("/stockouts")
def get_all_stockout_risk_scores():
    repo = SupplyGuardRepository()
    return repo.material_predictions

@router.post("/run-scoring")
def trigger_scoring_pipeline():
    repo = SupplyGuardRepository()
    repo._init_models_and_scores()
    return {
        "status": "COMPLETED",
        "scored_suppliers": len(repo.supplier_predictions),
        "scored_materials": len(repo.material_predictions),
        "timestamp": repo.pos_df["order_date"].max()
    }
