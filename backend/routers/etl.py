from typing import List
from fastapi import APIRouter
from backend.schemas.schemas import ETLAuditLogOut, ETLRejectedRecordOut, DataQualityTestOut
from backend.services.repository import SupplyGuardRepository

router = APIRouter(prefix="/etl", tags=["ETL Governance"])

@router.get("/audit-logs", response_model=List[ETLAuditLogOut])
def get_pipeline_audit_logs():
    repo = SupplyGuardRepository()
    return repo.get_etl_audit_logs()

@router.get("/rejected-records", response_model=List[ETLRejectedRecordOut])
def get_dead_letter_rejected_records():
    repo = SupplyGuardRepository()
    return repo.get_etl_rejected_records()

@router.get("/data-quality", response_model=List[DataQualityTestOut])
def get_data_quality_results():
    repo = SupplyGuardRepository()
    return repo.get_data_quality_results()
