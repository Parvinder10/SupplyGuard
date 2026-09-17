import pytest
from etl.validator import ETLValidator

def test_etl_validator_valid_supplier():
    valid_batch = [{
        "supplier_id": "SUP-9999",
        "code": "VND-99999",
        "name": "Stuttgart Precision Tech",
        "category": "Mechanical & Machining",
        "country": "Germany",
        "city": "Stuttgart",
        "tier": "TIER_1",
        "reliability_rating": 95.5,
        "financial_health_score": 88.0,
        "baseline_lead_time_days": 14,
        "payment_terms": "NET30",
        "iso_certified": True,
        "is_active": True
    }]
    valid, rejected = ETLValidator.validate_records("suppliers", valid_batch)
    assert len(valid) == 1
    assert len(rejected) == 0

def test_etl_validator_invalid_tier_rejection():
    invalid_batch = [{
        "supplier_id": "SUP-8888",
        "code": "VND-88888",
        "name": "Invalid Tier Supplier",
        "category": "Electronics",
        "country": "USA",
        "city": "Detroit",
        "tier": "TIER_INVALID",
        "reliability_rating": 90.0,
        "financial_health_score": 75.0,
        "baseline_lead_time_days": 20,
        "payment_terms": "NET30",
        "iso_certified": True
    }]
    valid, rejected = ETLValidator.validate_records("suppliers", invalid_batch)
    assert len(valid) == 0
    assert len(rejected) == 1
    assert rejected[0]["error_code"] == "ERR_SCHEMA_VALIDATION"
    assert "Invalid supplier tier" in rejected[0]["error_reason"]

def test_etl_validator_duplicate_detection():
    dup_batch = [
        {
            "supplier_id": "SUP-7777",
            "code": "VND-77771",
            "name": "First Instance",
            "category": "Raw Metallurgy",
            "country": "Germany",
            "city": "Munich",
            "tier": "TIER_2",
            "reliability_rating": 85.0,
            "financial_health_score": 80.0,
            "baseline_lead_time_days": 21,
            "payment_terms": "NET30",
            "iso_certified": True
        },
        {
            "supplier_id": "SUP-7777", # Duplicate ID
            "code": "VND-77772",
            "name": "Second Instance Duplicate",
            "category": "Raw Metallurgy",
            "country": "Germany",
            "city": "Munich",
            "tier": "TIER_2",
            "reliability_rating": 85.0,
            "financial_health_score": 80.0,
            "baseline_lead_time_days": 21,
            "payment_terms": "NET30",
            "iso_certified": True
        }
    ]
    valid, rejected = ETLValidator.validate_records("suppliers", dup_batch)
    assert len(valid) == 1
    assert len(rejected) == 1
    assert rejected[0]["error_code"] == "ERR_DUPLICATE_KEY"

def test_etl_validator_material_safety_stock_logic():
    # Reorder point cannot be below safety stock
    invalid_mat = [{
        "material_id": "MAT-99999",
        "sku": "SKU-TEST-01",
        "name": "Test Hydraulic Fluid",
        "category": "Polymers & Chemical",
        "unit_of_measure": "LITER",
        "standard_cost": 25.0,
        "current_unit_price": 27.5,
        "safety_stock_level": 100,
        "reorder_point": 50, # Invalid: 50 < 100
        "target_stock_level": 200,
        "min_order_qty": 25,
        "lead_time_days": 14,
        "is_critical": False,
        "primary_supplier_id": "SUP-0001"
    }]
    valid, rejected = ETLValidator.validate_records("materials", invalid_mat)
    assert len(valid) == 0
    assert len(rejected) == 1
    assert "Reorder point (50) must be greater than or equal to safety stock (100)" in rejected[0]["error_reason"]
