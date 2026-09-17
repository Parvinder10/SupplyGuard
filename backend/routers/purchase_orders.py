from typing import List, Optional
from fastapi import APIRouter, Query
from backend.schemas.schemas import PurchaseOrderOut
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])

@router.get("", response_model=List[PurchaseOrderOut])
def list_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status (DELIVERED, OVERDUE, IN_TRANSIT, PENDING)"),
    supplier_id: Optional[str] = Query(None, description="Filter by supplier ID"),
    search: Optional[str] = Query(None, description="Search by PO number"),
    limit: int = Query(150, ge=1, le=500)
):
    repo = SupplyGuardRepository()
    return repo.get_purchase_orders(status=status, supplier_id=supplier_id, search=search, limit=limit)
