import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_kpis_endpoint():
    response = client.get("/api/v1/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "on_time_delivery_rate" in data
    assert "total_spend_at_risk_usd" in data
    assert "active_stockouts_count" in data
    assert data["on_time_delivery_rate"] > 0

def test_suppliers_list_and_filter():
    response = client.get("/api/v1/suppliers")
    assert response.status_code == 200
    suppliers = response.json()
    assert len(suppliers) >= 100
    assert "otd_percentage" in suppliers[0]
    assert "risk_score" in suppliers[0]
    assert "explanation_text" in suppliers[0]

    # Filter by risk tier
    crit_res = client.get("/api/v1/suppliers?risk_tier=CRITICAL")
    assert crit_res.status_code == 200
    for s in crit_res.json():
        assert s["risk_tier"] == "CRITICAL"

def test_materials_list():
    response = client.get("/api/v1/materials?limit=50")
    assert response.status_code == 200
    materials = response.json()
    assert len(materials) == 50
    assert "days_of_inventory" in materials[0]
    assert "stock_health_status" in materials[0]

def test_purchase_orders():
    response = client.get("/api/v1/purchase-orders?limit=50")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 50
    assert "status" in orders[0]

def test_alerts_and_corrective_actions_workflow():
    # 1. Fetch alerts
    alerts_res = client.get("/api/v1/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    target_alert = alerts[0]

    # 2. Update alert status to ACKNOWLEDGED
    update_res = client.patch(f"/api/v1/alerts/{target_alert['alert_id']}", json={"status": "ACKNOWLEDGED"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "ACKNOWLEDGED"

    # 3. Create Corrective Action
    action_payload = {
        "alert_id": target_alert["alert_id"],
        "title": "Emergency Dual-Sourcing Qualification",
        "description": "Qualify secondary supplier for impacted critical material.",
        "assigned_to": "Lead Strategic Procurement Manager",
        "priority": "HIGH",
        "root_cause": "Supplier delivery variance spike",
        "mitigation_plan": "Expedite spot buy"
    }
    create_res = client.post("/api/v1/corrective-actions", json=action_payload)
    assert create_res.status_code == 200
    created_action = create_res.json()
    assert created_action["status"] == "OPEN"
    assert created_action["action_id"].startswith("CA-")

    # 4. Update status to RESOLVED
    action_id = created_action["action_id"]
    resolve_res = client.patch(f"/api/v1/corrective-actions/{action_id}", json={
        "status": "RESOLVED",
        "resolution_notes": "Secondary vendor certified. Spot inventory received."
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

def test_etl_governance_endpoints():
    audit_res = client.get("/api/v1/etl/audit-logs")
    assert audit_res.status_code == 200
    assert len(audit_res.json()) > 0

    reject_res = client.get("/api/v1/etl/rejected-records")
    assert reject_res.status_code == 200
    assert len(reject_res.json()) > 0

    dq_res = client.get("/api/v1/etl/data-quality")
    assert dq_res.status_code == 200
    assert len(dq_res.json()) > 0
