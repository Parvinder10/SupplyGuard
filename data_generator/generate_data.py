"""
SupplyGuard Enterprise Dataset Generator
Generates realistic manufacturing supply chain datasets:
- >= 100 suppliers with categories, reliability profiles, lead times
- >= 1,000 materials (SKUs) with safety stocks, costs, BOM tiering
- >= 5,000 purchase orders with line items, promised dates, statuses
- >= 100,000 inventory movements across factories & warehouses
- Goods receipts with delivery variance & damage tracking
- Quality inspections with defect classification and PPM
- Production schedules & work orders with component BOM allocations
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Deterministic seed for reproducible testing & benchmarks
DEFAULT_SEED = 42

SUPPLIER_CATEGORIES = [
    ("Electronic Components", ["Microcontrollers", "Capacitors", "Sensors", "PCBs", "Connectors"]),
    ("Mechanical & Machining", ["CNC Castings", "Hydraulic Valves", "Shafts", "Gears", "Bearings"]),
    ("Raw Metallurgy", ["Aluminum Billets 6061", "Sheet Metal Stainless 304", "Carbon Steel Bars", "Copper Rods", "Titanium Plates"]),
    ("Polymers & Chemical", ["ABS Resin Pellets", "Polycarbonate Sheets", "Silicone Gaskets", "Industrial Lubricants", "Epoxy Adhesives"]),
    ("Packaging & Hardware", ["Corrugated Heavy Boxes", "Hex Flange Bolts M8", "Vibration Dampers", "Antistatic Foam", "Thermal Pallet Wraps"])
]

COUNTRIES = [
    ("USA", ["Detroit, MI", "Austin, TX", "Cleveland, OH", "Chicago, IL"]),
    ("Germany", ["Munich", "Stuttgart", "Nuremberg", "Frankfurt"]),
    ("Japan", ["Nagoya", "Tokyo", "Osaka", "Yokohama"]),
    ("South Korea", ["Seoul", "Busan", "Ulsan", "Incheon"]),
    ("Taiwan", ["Hsinchu", "Taipei", "Taichung", "Tainan"]),
    ("Mexico", ["Monterrey", "Guadalajara", "Saltillo", "Juarez"]),
    ("Vietnam", ["Hai Phong", "Da Nang", "Ho Chi Minh City", "Binh Duong"])
]

FACTORIES = [
    {"factory_id": "FAC-US-01", "name": "Detroit Automotive & Precision Assembly", "country": "USA", "region": "North America"},
    {"factory_id": "FAC-EU-01", "name": "Munich Advanced Hydraulics & Systems", "country": "Germany", "region": "Europe"},
    {"factory_id": "FAC-APAC-01", "name": "Singapore Microelectronics Center", "country": "Singapore", "region": "Asia-Pacific"},
    {"factory_id": "FAC-MX-01", "name": "Monterrey High-Volume Sub-Assembly", "country": "Mexico", "region": "North America"},
]

WAREHOUSES = [
    {"warehouse_id": "WH-US-RAW-01", "factory_id": "FAC-US-01", "name": "Detroit Central Raw Materials", "warehouse_type": "RAW_MATERIALS", "capacity_sqm": 25000},
    {"warehouse_id": "WH-US-FIN-01", "factory_id": "FAC-US-01", "name": "Detroit Finished Goods Distribution", "warehouse_type": "FINISHED_GOODS", "capacity_sqm": 35000},
    {"warehouse_id": "WH-EU-RAW-01", "factory_id": "FAC-EU-01", "name": "Munich Raw Components Hub", "warehouse_type": "RAW_MATERIALS", "capacity_sqm": 18000},
    {"warehouse_id": "WH-EU-FIN-01", "factory_id": "FAC-EU-01", "name": "Munich Systems Staging Depot", "warehouse_type": "FINISHED_GOODS", "capacity_sqm": 22000},
    {"warehouse_id": "WH-APAC-RAW-01", "factory_id": "FAC-APAC-01", "name": "Singapore Cleanroom Raw Buffer", "warehouse_type": "RAW_MATERIALS", "capacity_sqm": 15000},
    {"warehouse_id": "WH-APAC-FIN-01", "factory_id": "FAC-APAC-01", "name": "Singapore Export Hub", "warehouse_type": "FINISHED_GOODS", "capacity_sqm": 20000},
    {"warehouse_id": "WH-MX-RAW-01", "factory_id": "FAC-MX-01", "name": "Monterrey Inbound Receiving", "warehouse_type": "RAW_MATERIALS", "capacity_sqm": 28000},
    {"warehouse_id": "WH-MX-FIN-01", "factory_id": "FAC-MX-01", "name": "Monterrey Border Staging Hub", "warehouse_type": "FINISHED_GOODS", "capacity_sqm": 30000},
]

DEFECT_TYPES = [
    {"defect_type_code": "DEF_DIMENSIONAL", "name": "Dimensional Out of Tolerance", "severity": "HIGH", "category": "Mechanical"},
    {"defect_type_code": "DEF_SURFACE", "name": "Surface Flaw / Scratch / Burr", "severity": "LOW", "category": "Cosmetic"},
    {"defect_type_code": "DEF_ELECTRICAL", "name": "Electrical Open / Short / Drift", "severity": "CRITICAL", "category": "Electronics"},
    {"defect_type_code": "DEF_CONTAMINATION", "name": "Chemical / Particulate Contamination", "severity": "CRITICAL", "category": "Chemical"},
    {"defect_type_code": "DEF_PACKAGING", "name": "Packaging Damage / Moisture Seal Breach", "severity": "MEDIUM", "category": "Logistics"},
    {"defect_type_code": "DEF_METALLURGY", "name": "Material Tensile / Hardness Non-conformance", "severity": "HIGH", "category": "Material"}
]


class SupplyChainDataGenerator:
    def __init__(self, seed=DEFAULT_SEED):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.start_date = datetime(2025, 1, 1)
        self.end_date = datetime(2026, 6, 30)

    def generate_suppliers(self, count=120):
        suppliers = []
        company_suffixes = ["Technologies", "Precision Mfg", "Industries Inc", "Global Parts", "Solutions Corp", "Systems AG", "Materials Ltd"]
        
        for i in range(1, count + 1):
            sup_id = f"SUP-{i:04d}"
            cat_tuple = random.choice(SUPPLIER_CATEGORIES)
            category = cat_tuple[0]
            country, cities = random.choice(COUNTRIES)
            city = random.choice(cities)
            name = f"{city.split(',')[0]} {random.choice(cat_tuple[1])} {random.choice(company_suffixes)}"
            
            # Risk profile clustering: 15% high risk, 65% standard reliable, 20% elite
            profile_rand = random.random()
            if profile_rand < 0.15:
                reliability_rating = round(random.uniform(45.0, 68.0), 1)
                baseline_lead_time = random.randint(35, 65)
                financial_health = round(random.uniform(30.0, 58.0), 1)
                tier = "TIER_3"
            elif profile_rand < 0.80:
                reliability_rating = round(random.uniform(75.0, 92.0), 1)
                baseline_lead_time = random.randint(14, 35)
                financial_health = round(random.uniform(70.0, 88.0), 1)
                tier = "TIER_2"
            else:
                reliability_rating = round(random.uniform(93.0, 99.5), 1)
                baseline_lead_time = random.randint(7, 21)
                financial_health = round(random.uniform(88.0, 99.0), 1)
                tier = "TIER_1"

            suppliers.append({
                "supplier_id": sup_id,
                "name": name,
                "code": f"VND-{i:05d}",
                "category": category,
                "country": country,
                "city": city,
                "tier": tier,
                "reliability_rating": reliability_rating,
                "financial_health_score": financial_health,
                "baseline_lead_time_days": baseline_lead_time,
                "payment_terms": random.choice(["NET30", "NET45", "NET60", "2/10 NET30"]),
                "iso_certified": random.random() > 0.12,
                "is_active": True,
                "created_at": self.start_date.isoformat()
            })
        return pd.DataFrame(suppliers)

    def generate_materials(self, suppliers_df, count=1200):
        materials = []
        uoms = ["PCS", "KG", "METER", "LITER", "SET", "BOX"]
        supplier_ids = suppliers_df["supplier_id"].tolist()
        
        # Select 8% of suppliers to be single-source critical suppliers
        critical_suppliers = random.sample(supplier_ids, max(5, int(len(supplier_ids) * 0.08)))

        for i in range(1, count + 1):
            mat_id = f"MAT-{i:05d}"
            cat_tuple = random.choice(SUPPLIER_CATEGORIES)
            category = cat_tuple[0]
            subcat = random.choice(cat_tuple[1])
            name = f"{subcat} Grade-{random.choice(['A', 'B', 'Industrial', 'MilSpec', 'Commercial'])}-{i:03d}"
            sku = f"SKU-{category[:3].upper()}-{i:05d}"
            uom = random.choice(uoms)
            
            # Standard cost: lognormal distribution
            standard_cost = round(float(np.random.lognormal(mean=3.2, sigma=1.1)), 2)
            standard_cost = max(1.50, min(8500.0, standard_cost))
            current_unit_price = round(standard_cost * random.uniform(0.95, 1.15), 2)
            
            # Critical material flag (~12% critical)
            is_critical = random.random() < 0.12
            if is_critical and random.random() < 0.5:
                primary_sup = random.choice(critical_suppliers)
                secondary_sup = None # Single source!
            else:
                primary_sup = random.choice(supplier_ids)
                cand_secondary = random.choice(supplier_ids)
                secondary_sup = cand_secondary if cand_secondary != primary_sup else None

            # Inventory thresholds
            daily_usage_est = random.randint(5, 80)
            lead_time_days = random.randint(7, 45)
            safety_stock_level = int(daily_usage_est * (lead_time_days * random.uniform(0.3, 0.6)))
            reorder_point = safety_stock_level + int(daily_usage_est * lead_time_days)
            target_stock_level = int(reorder_point * random.uniform(1.4, 2.2))
            min_order_qty = random.choice([25, 50, 100, 250, 500, 1000])

            materials.append({
                "material_id": mat_id,
                "sku": sku,
                "name": name,
                "category": category,
                "unit_of_measure": uom,
                "standard_cost": standard_cost,
                "current_unit_price": current_unit_price,
                "safety_stock_level": safety_stock_level,
                "reorder_point": reorder_point,
                "target_stock_level": target_stock_level,
                "min_order_qty": min_order_qty,
                "lead_time_days": lead_time_days,
                "is_critical": is_critical,
                "primary_supplier_id": primary_sup,
                "secondary_supplier_id": secondary_sup,
                "created_at": self.start_date.isoformat()
            })
        return pd.DataFrame(materials)

    def generate_purchase_orders(self, suppliers_df, materials_df, count=6000):
        orders = []
        lines = []
        sup_dict = suppliers_df.set_index("supplier_id").to_dict("index")
        mat_dict = materials_df.set_index("material_id").to_dict("index")
        mat_ids = list(mat_dict.keys())

        # Pre-assign materials to raw warehouses
        raw_warehouses = [w for w in WAREHOUSES if w["warehouse_type"] == "RAW_MATERIALS"]
        
        total_days = (self.end_date - self.start_date).days
        line_counter = 1

        for po_idx in range(1, count + 1):
            po_id = f"PO-2025-{po_idx:05d}"
            po_number = f"PO-{po_idx:06d}"
            
            # Select random material and its primary supplier
            sampled_mat_id = random.choice(mat_ids)
            mat_info = mat_dict[sampled_mat_id]
            supplier_id = mat_info["primary_supplier_id"]
            sup_info = sup_dict[supplier_id]

            wh = random.choice(raw_warehouses)
            warehouse_id = wh["warehouse_id"]
            factory_id = wh["factory_id"]

            # Order date distributed over the timeline
            day_offset = int(np.random.triangular(0, total_days * 0.65, total_days))
            order_date = self.start_date + timedelta(days=day_offset)
            
            # Baseline promised lead time based on supplier baseline
            promised_lead_time = sup_info["baseline_lead_time_days"] + random.randint(-2, 5)
            promised_lead_time = max(3, promised_lead_time)
            promised_delivery_date = order_date + timedelta(days=promised_lead_time)

            # Determine PO status based on order date and current simulated date (2026-04-15)
            sim_now = datetime(2026, 4, 15)
            if promised_delivery_date <= sim_now:
                # Historical order: delivered, overdue, or cancelled
                stat_rand = random.random()
                if stat_rand < 0.86:
                    status = "DELIVERED"
                elif stat_rand < 0.94:
                    status = "OVERDUE"
                else:
                    status = "CANCELLED"
            else:
                # Future order
                status = "IN_TRANSIT" if (order_date + timedelta(days=3)) <= sim_now else "PENDING"

            # Create 1 to 4 line items for this PO
            num_lines = random.choices([1, 2, 3, 4], weights=[0.55, 0.25, 0.15, 0.05])[0]
            po_total = 0.0

            for l_idx in range(1, num_lines + 1):
                cur_mat_id = sampled_mat_id if l_idx == 1 else random.choice(mat_ids)
                c_mat = mat_dict[cur_mat_id]
                qty = int(c_mat["min_order_qty"] * random.uniform(1.0, 5.0))
                unit_price = c_mat["current_unit_price"]
                line_total = round(qty * unit_price, 2)
                po_total += line_total

                lines.append({
                    "po_line_id": f"POL-{line_counter:07d}",
                    "po_id": po_id,
                    "line_number": l_idx,
                    "material_id": cur_mat_id,
                    "quantity_ordered": qty,
                    "unit_price": unit_price,
                    "line_total": line_total,
                    "line_status": status
                })
                line_counter += 1

            orders.append({
                "po_id": po_id,
                "po_number": po_number,
                "supplier_id": supplier_id,
                "factory_id": factory_id,
                "warehouse_id": warehouse_id,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "promised_delivery_date": promised_delivery_date.strftime("%Y-%m-%d"),
                "status": status,
                "total_amount": round(po_total, 2),
                "currency": "USD",
                "created_at": order_date.isoformat()
            })

        return pd.DataFrame(orders), pd.DataFrame(lines)

    def generate_receipts_and_quality(self, pos_df, po_lines_df, suppliers_df):
        receipts = []
        inspections = []
        
        sup_dict = suppliers_df.set_index("supplier_id").to_dict("index")
        delivered_lines = po_lines_df[po_lines_df["line_status"].isin(["DELIVERED", "OVERDUE"])].copy()
        
        receipt_counter = 1
        inspection_counter = 1

        po_lookup = pos_df.set_index("po_id").to_dict("index")

        for _, row in delivered_lines.iterrows():
            po_info = po_lookup[row["po_id"]]
            sup_info = sup_dict[po_info["supplier_id"]]
            promised_date = datetime.strptime(po_info["promised_delivery_date"], "%Y-%m-%d")
            
            # Realistic lead time variance:
            # Low reliability suppliers have heavy right-tailed delays
            if sup_info["reliability_rating"] < 70.0:
                delay_days = int(np.random.exponential(scale=9.0) - 2)
            elif sup_info["reliability_rating"] < 90.0:
                delay_days = int(np.random.normal(loc=1.0, scale=3.5))
            else:
                delay_days = int(np.random.normal(loc=-1.0, scale=1.8))

            actual_delivery_date = promised_date + timedelta(days=delay_days)
            # Ensure actual delivery is not before order date
            order_date = datetime.strptime(po_info["order_date"], "%Y-%m-%d")
            if actual_delivery_date < order_date:
                actual_delivery_date = order_date + timedelta(days=2)

            qty_ordered = row["quantity_ordered"]
            
            # Delivery discrepancy (short shipments)
            disc_rand = random.random()
            if disc_rand < 0.08:
                qty_delivered = int(qty_ordered * random.uniform(0.70, 0.95))
            elif disc_rand < 0.11:
                qty_delivered = int(qty_ordered * random.uniform(1.02, 1.10))
            else:
                qty_delivered = qty_ordered

            receipt_id = f"GR-{receipt_counter:07d}"
            
            # Quality Inspection
            # Defect probability heavily correlated with supplier reliability
            sample_size = min(qty_delivered, max(10, int(qty_delivered * 0.15)))
            expected_defect_rate = (100.0 - sup_info["reliability_rating"]) / 200.0 # e.g. 95% -> 2.5% defects, 60% -> 20%
            defect_count = np.random.binomial(n=sample_size, p=max(0.001, min(0.40, expected_defect_rate)))
            
            defect_ppm = int((defect_count / max(1, sample_size)) * 1_000_000)
            
            if defect_count == 0:
                disposition = "ACCEPTED"
                defect_type = None
                qty_rejected = 0
            elif defect_count / sample_size < 0.04:
                disposition = "CONCESSION" # minor deviation accepted
                defect_type = random.choice(DEFECT_TYPES)["defect_type_code"]
                qty_rejected = int(defect_count * (qty_delivered / sample_size))
            else:
                disposition = "REJECTED"
                defect_type = random.choice(DEFECT_TYPES)["defect_type_code"]
                qty_rejected = int(defect_count * (qty_delivered / sample_size))
                qty_rejected = min(qty_delivered, qty_rejected)

            qty_accepted = max(0, qty_delivered - qty_rejected)
            variance_days = (actual_delivery_date - promised_date).days

            receipts.append({
                "receipt_id": receipt_id,
                "po_id": row["po_id"],
                "po_line_id": row["po_line_id"],
                "supplier_id": po_info["supplier_id"],
                "material_id": row["material_id"],
                "warehouse_id": po_info["warehouse_id"],
                "factory_id": po_info["factory_id"],
                "receipt_date": actual_delivery_date.strftime("%Y-%m-%d"),
                "quantity_delivered": qty_delivered,
                "quantity_accepted": qty_accepted,
                "quantity_rejected": qty_rejected,
                "delivery_variance_days": variance_days,
                "damage_detected": qty_rejected > 0,
                "created_at": actual_delivery_date.isoformat()
            })

            inspections.append({
                "inspection_id": f"QC-{inspection_counter:07d}",
                "receipt_id": receipt_id,
                "material_id": row["material_id"],
                "supplier_id": po_info["supplier_id"],
                "inspection_date": actual_delivery_date.strftime("%Y-%m-%d"),
                "sample_size": sample_size,
                "defect_count": int(defect_count),
                "defect_ppm": defect_ppm,
                "defect_type_code": defect_type,
                "disposition": disposition,
                "inspector_id": f"INSP-{random.randint(101, 125)}"
            })

            receipt_counter += 1
            inspection_counter += 1

        return pd.DataFrame(receipts), pd.DataFrame(inspections)

    def generate_inventory_movements(self, materials_df, receipts_df, count=110000):
        movements = []
        materials_list = materials_df["material_id"].tolist()
        warehouses_list = [w["warehouse_id"] for w in WAREHOUSES]
        factory_map = {w["warehouse_id"]: w["factory_id"] for w in WAREHOUSES}

        # 1. Ingest receipts as positive inbound movements (~20% of movements)
        rec_count = min(len(receipts_df), int(count * 0.20))
        sampled_receipts = receipts_df.sample(n=rec_count, random_state=self.seed) if len(receipts_df) >= rec_count else receipts_df

        mov_counter = 1
        for _, rec in sampled_receipts.iterrows():
            if rec["quantity_accepted"] > 0:
                movements.append({
                    "movement_id": f"MOV-{mov_counter:08d}",
                    "material_id": rec["material_id"],
                    "warehouse_id": rec["warehouse_id"],
                    "factory_id": rec["factory_id"],
                    "movement_date": rec["receipt_date"],
                    "movement_type": "GOODS_RECEIPT",
                    "quantity": int(rec["quantity_accepted"]),
                    "reference_doc_type": "PURCHASE_ORDER",
                    "reference_doc_id": rec["receipt_id"]
                })
                mov_counter += 1

        # 2. Generate remaining synthetic daily inventory activity across factories
        remaining = count - len(movements)
        total_days = (self.end_date - self.start_date).days

        for _ in range(remaining):
            mat_id = random.choice(materials_list)
            wh_id = random.choice(warehouses_list)
            fac_id = factory_map[wh_id]
            day_offset = random.randint(0, total_days - 1)
            mov_date = self.start_date + timedelta(days=day_offset)

            mov_type_roll = random.random()
            if mov_type_roll < 0.65:
                # Production consumption / issue (negative delta)
                mov_type = "PRODUCTION_ISSUE"
                qty = -int(random.randint(5, 75))
                ref_type = "WORK_ORDER"
                ref_id = f"WO-ACT-{random.randint(1000, 9999)}"
            elif mov_type_roll < 0.82:
                # Internal transfer
                mov_type = "TRANSFER_OUT" if random.random() < 0.5 else "TRANSFER_IN"
                qty = -int(random.randint(10, 50)) if mov_type == "TRANSFER_OUT" else int(random.randint(10, 50))
                ref_type = "TRANSFER_ORDER"
                ref_id = f"TRF-{random.randint(10000, 99999)}"
            elif mov_type_roll < 0.94:
                # Scrap or damaged writeoff
                mov_type = "SCRAP"
                qty = -int(random.randint(1, 12))
                ref_type = "SCRAP_NOTICE"
                ref_id = f"SCR-{random.randint(1000, 9999)}"
            else:
                # Cycle count adjustment (variance reconciliation)
                mov_type = "CYCLE_ADJUSTMENT"
                qty = int(random.randint(-15, 20))
                ref_type = "AUDIT_COUNT"
                ref_id = f"AUD-{random.randint(100, 999)}"

            movements.append({
                "movement_id": f"MOV-{mov_counter:08d}",
                "material_id": mat_id,
                "warehouse_id": wh_id,
                "factory_id": fac_id,
                "movement_date": mov_date.strftime("%Y-%m-%d"),
                "movement_type": mov_type,
                "quantity": qty,
                "reference_doc_type": ref_type,
                "reference_doc_id": ref_id
            })
            mov_counter += 1

        return pd.DataFrame(movements)

    def generate_production_schedules(self, materials_df, count=1500):
        work_orders = []
        bom_allocations = []
        
        product_skus = [f"FG-AUTOSYS-{i:03d}" for i in range(1, 101)]
        materials_list = materials_df["material_id"].tolist()
        critical_materials = materials_df[materials_df["is_critical"] == True]["material_id"].tolist()
        
        wo_counter = 1
        alloc_counter = 1
        total_days = (self.end_date - self.start_date).days

        for _ in range(count):
            wo_id = f"WO-2025-{wo_counter:06d}"
            sku = random.choice(product_skus)
            fac = random.choice(FACTORIES)["factory_id"]
            
            day_offset = random.randint(15, total_days - 30)
            start_date = self.start_date + timedelta(days=day_offset)
            duration = random.randint(3, 14)
            end_date = start_date + timedelta(days=duration)
            
            planned_qty = random.choice([50, 100, 250, 500, 1000])
            
            # Status
            sim_now = datetime(2026, 4, 15)
            if end_date < sim_now:
                status = "COMPLETED"
                completed_qty = planned_qty
            elif start_date <= sim_now <= end_date:
                status = "IN_PROGRESS"
                completed_qty = int(planned_qty * random.uniform(0.2, 0.8))
            else:
                # Future: 10% blocked due to material shortage
                status = "BLOCKED_SHORTAGE" if random.random() < 0.10 else "PLANNED"
                completed_qty = 0

            work_orders.append({
                "work_order_id": wo_id,
                "product_sku": sku,
                "factory_id": fac,
                "planned_quantity": planned_qty,
                "completed_quantity": completed_qty,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "status": status,
                "priority": random.choice(["HIGH", "STANDARD", "CRITICAL"])
            })

            # Bill of Materials (BOM) explosion: 4 to 8 materials per work order
            num_components = random.randint(4, 8)
            chosen_components = random.sample(materials_list, num_components)
            # Inject a critical material
            if critical_materials and random.random() < 0.7:
                chosen_components[0] = random.choice(critical_materials)

            for comp_mat_id in chosen_components:
                unit_req = random.uniform(1.0, 5.0)
                total_req = int(planned_qty * unit_req)
                
                if status == "BLOCKED_SHORTAGE":
                    allocated_qty = int(total_req * random.uniform(0.1, 0.4))
                    shortage_qty = total_req - allocated_qty
                else:
                    allocated_qty = total_req
                    shortage_qty = 0

                bom_allocations.append({
                    "allocation_id": f"ALC-{alloc_counter:07d}",
                    "work_order_id": wo_id,
                    "material_id": comp_mat_id,
                    "required_quantity": total_req,
                    "allocated_quantity": allocated_qty,
                    "shortage_quantity": shortage_qty
                })
                alloc_counter += 1

            wo_counter += 1

        return pd.DataFrame(work_orders), pd.DataFrame(bom_allocations)

    def generate_all(self, output_dir="data"):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Generating realistic supply chain datasets (Seed={self.seed})...")

        # Dimensions
        print("1. Generating Suppliers (>=100)...")
        suppliers_df = self.generate_suppliers(count=120)
        suppliers_df.to_csv(os.path.join(output_dir, "suppliers.csv"), index=False)

        print("2. Generating Materials (>=1,000)...")
        materials_df = self.generate_materials(suppliers_df, count=1200)
        materials_df.to_csv(os.path.join(output_dir, "materials.csv"), index=False)

        # Factories, Warehouses, Defect Types
        pd.DataFrame(FACTORIES).to_csv(os.path.join(output_dir, "factories.csv"), index=False)
        pd.DataFrame(WAREHOUSES).to_csv(os.path.join(output_dir, "warehouses.csv"), index=False)
        pd.DataFrame(DEFECT_TYPES).to_csv(os.path.join(output_dir, "defect_types.csv"), index=False)

        print("3. Generating Purchase Orders (>=5,000)...")
        pos_df, po_lines_df = self.generate_purchase_orders(suppliers_df, materials_df, count=6000)
        pos_df.to_csv(os.path.join(output_dir, "purchase_orders.csv"), index=False)
        po_lines_df.to_csv(os.path.join(output_dir, "purchase_order_lines.csv"), index=False)

        print("4. Generating Goods Receipts & Quality Inspections...")
        receipts_df, inspections_df = self.generate_receipts_and_quality(pos_df, po_lines_df, suppliers_df)
        receipts_df.to_csv(os.path.join(output_dir, "goods_receipts.csv"), index=False)
        inspections_df.to_csv(os.path.join(output_dir, "quality_inspections.csv"), index=False)

        print("5. Generating Inventory Movements (>=100,000)...")
        movements_df = self.generate_inventory_movements(materials_df, receipts_df, count=110000)
        movements_df.to_csv(os.path.join(output_dir, "inventory_movements.csv"), index=False)

        print("6. Generating Production Schedules & BOM Allocations...")
        work_orders_df, bom_alloc_df = self.generate_production_schedules(materials_df, count=1500)
        work_orders_df.to_csv(os.path.join(output_dir, "production_schedules.csv"), index=False)
        bom_alloc_df.to_csv(os.path.join(output_dir, "bom_allocations.csv"), index=False)

        summary = {
            "suppliers": len(suppliers_df),
            "materials": len(materials_df),
            "purchase_orders": len(pos_df),
            "purchase_order_lines": len(po_lines_df),
            "goods_receipts": len(receipts_df),
            "quality_inspections": len(inspections_df),
            "inventory_movements": len(movements_df),
            "production_schedules": len(work_orders_df),
            "bom_allocations": len(bom_alloc_df),
            "factories": len(FACTORIES),
            "warehouses": len(WAREHOUSES)
        }
        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(summary, f, indent=2)

        print("\nDataset Generation Complete:")
        for k, v in summary.items():
            print(f"  - {k}: {v:,}")

        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic enterprise supply chain data.")
    parser.add_argument("--output-dir", default="data", help="Output directory for CSV files")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    args = parser.parse_args()

    gen = SupplyChainDataGenerator(seed=args.seed)
    gen.generate_all(output_dir=args.output_dir)
