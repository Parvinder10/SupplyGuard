from fastapi import APIRouter
from backend.schemas.schemas import ExecutiveKPIs
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/kpis", tags=["Executive KPIs"])

@router.get("", response_model=ExecutiveKPIs)
def get_executive_kpis():
    repo = SupplyGuardRepository()
    return repo.get_kpis()
