from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.schemas.schemas import SupplierScorecard
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

@router.get("", response_model=List[SupplierScorecard])
def list_suppliers(
    tier: Optional[str] = Query(None, description="Filter by supplier tier (TIER_1, TIER_2, TIER_3)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_tier: Optional[str] = Query(None, description="Filter by ML risk tier (CRITICAL, HIGH, MEDIUM, LOW)"),
    search: Optional[str] = Query(None, description="Search by name, code or ID")
):
    repo = SupplyGuardRepository()
    return repo.get_suppliers(tier=tier, category=category, risk_tier=risk_tier, search=search)

@router.get("/{supplier_id}", response_model=SupplierScorecard)
def get_supplier(supplier_id: str):
    repo = SupplyGuardRepository()
    sup = repo.get_supplier_by_id(supplier_id)
    if not sup:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return sup
