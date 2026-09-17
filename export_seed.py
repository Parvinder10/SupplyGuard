import os
import json
from backend.services.repository import SupplyGuardRepository

def export():
    repo = SupplyGuardRepository()
    data = {
        "kpis": repo.get_kpis(),
        "suppliers": repo.get_suppliers(),
        "materials": repo.get_materials(limit=300),
        "orders": repo.get_purchase_orders(limit=150),
        "alerts": repo.get_alerts(),
        "actions": repo.get_corrective_actions(),
        "auditLogs": repo.get_etl_audit_logs(),
        "rejectedRecords": repo.get_etl_rejected_records(),
        "dqResults": repo.get_data_quality_results()
    }
    out_path = os.path.join("frontend", "src", "services", "seedData.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, indent=2)
    print("Seed data generated successfully at:", out_path)

if __name__ == "__main__":
    export()
