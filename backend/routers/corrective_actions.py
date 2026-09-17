from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.schemas.schemas import CorrectiveActionCreate, CorrectiveActionUpdate, CorrectiveActionOut
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/corrective-actions", tags=["Corrective Actions"])

@router.get("", response_model=List[CorrectiveActionOut])
def list_corrective_actions(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, IN_PROGRESS, RESOLVED)")
):
    repo = SupplyGuardRepository()
    return repo.get_corrective_actions(status=status)

@router.post("", response_model=CorrectiveActionOut)
def create_corrective_action(payload: CorrectiveActionCreate):
    repo = SupplyGuardRepository()
    return repo.create_corrective_action(payload.model_dump())

@router.patch("/{action_id}", response_model=CorrectiveActionOut)
def update_corrective_action(action_id: str, payload: CorrectiveActionUpdate):
    repo = SupplyGuardRepository()
    updated = repo.update_corrective_action(action_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Corrective action {action_id} not found")
    return updated
