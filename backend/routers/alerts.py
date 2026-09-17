from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.schemas.schemas import AlertOut, AlertUpdate
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/alerts", tags=["Supply Alerts"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (STOCKOUT, HIGH_RISK_SUPPLIER)")
):
    repo = SupplyGuardRepository()
    return repo.get_alerts(severity=severity, alert_type=alert_type)

@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: str, payload: AlertUpdate):
    repo = SupplyGuardRepository()
    alt = repo.update_alert_status(alert_id, payload.status)
    if not alt:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alt
