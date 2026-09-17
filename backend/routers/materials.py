from typing import List, Optional
from fastapi import APIRouter, Query
from backend.schemas.schemas import MaterialOut
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/materials", tags=["Materials & Inventory"])

@router.get("", response_model=List[MaterialOut])
def list_materials(
    category: Optional[str] = Query(None, description="Filter by material category"),
    risk_tier: Optional[str] = Query(None, description="Filter by stockout risk tier"),
    is_critical: Optional[bool] = Query(None, description="Filter critical path materials"),
    search: Optional[str] = Query(None, description="Search by SKU or material name"),
    limit: int = Query(200, ge=1, le=1000)
):
    repo = SupplyGuardRepository()
    return repo.get_materials(category=category, risk_tier=risk_tier, is_critical=is_critical, search=search, limit=limit)
