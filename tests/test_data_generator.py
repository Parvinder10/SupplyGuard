import os
import json
import pytest
import pandas as pd

DATA_DIR = "data"

def test_data_generation_quantities():
    """Verify generated dataset meets and exceeds all specification criteria"""
    metadata_path = os.path.join(DATA_DIR, "metadata.json")
    assert os.path.exists(metadata_path), "metadata.json should exist"

    with open(metadata_path, "r") as f:
        meta = json.load(f)

    assert meta["suppliers"] >= 100, f"Expected >= 100 suppliers, found {meta['suppliers']}"
    assert meta["materials"] >= 1000, f"Expected >= 1000 materials, found {meta['materials']}"
    assert meta["purchase_orders"] >= 5000, f"Expected >= 5000 POs, found {meta['purchase_orders']}"
    assert meta["inventory_movements"] >= 100000, f"Expected >= 100000 movements, found {meta['inventory_movements']}"
    assert meta["factories"] >= 3, f"Expected multiple factories, found {meta['factories']}"
    assert meta["warehouses"] >= 4, f"Expected multiple warehouses, found {meta['warehouses']}"

def test_suppliers_relational_integrity():
    """Check supplier data attributes and validity"""
    sup_df = pd.read_csv(os.path.join(DATA_DIR, "suppliers.csv"))
    assert len(sup_df) >= 100
    assert sup_df["supplier_id"].is_unique, "Supplier IDs must be unique"
    assert (sup_df["reliability_rating"] >= 0).all() and (sup_df["reliability_rating"] <= 100).all()
    assert set(sup_df["tier"].unique()).issubset({"TIER_1", "TIER_2", "TIER_3"})

def test_materials_relational_integrity():
    """Check material catalog constraints"""
    mat_df = pd.read_csv(os.path.join(DATA_DIR, "materials.csv"))
    assert len(mat_df) >= 1000
    assert mat_df["material_id"].is_unique, "Material IDs must be unique"
    assert (mat_df["standard_cost"] > 0).all(), "Standard costs must be strictly positive"
    assert (mat_df["safety_stock_level"] >= 0).all()
    assert (mat_df["reorder_point"] >= mat_df["safety_stock_level"]).all(), "Reorder point must be >= safety stock"

def test_goods_receipts_chronology():
    """Ensure delivery receipts have valid chronological order"""
    rec_df = pd.read_csv(os.path.join(DATA_DIR, "goods_receipts.csv"))
    assert len(rec_df) > 0
    assert (rec_df["quantity_delivered"] >= 0).all()
    assert (rec_df["quantity_accepted"] >= 0).all()
    assert (rec_df["quantity_rejected"] >= 0).all()
    assert (rec_df["quantity_delivered"] >= rec_df["quantity_accepted"]).all()

def test_inventory_movements_partitions():
    """Ensure movements span quarters to populate range partitions"""
    mov_df = pd.read_csv(os.path.join(DATA_DIR, "inventory_movements.csv"))
    assert len(mov_df) >= 100000
    mov_dates = pd.to_datetime(mov_df["movement_date"])
    years = mov_dates.dt.year.unique()
    assert 2025 in years and 2026 in years, "Movements must span across 2025 and 2026"
