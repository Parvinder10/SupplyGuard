"""
SupplyGuard: ETL Schema Validator & Dead-Letter Filter
Provides strict Pydantic/dataclass schema validation, duplicate detection,
logical rule enforcement, and dead-letter record separation for enterprise pipelines.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field, field_validator, ValidationError


class SupplierInboundSchema(BaseModel):
    supplier_id: str
    code: str
    name: str
    category: str
    country: str
    city: str
    tier: str
    reliability_rating: float = Field(ge=0.0, le=100.0)
    financial_health_score: float = Field(ge=0.0, le=100.0)
    baseline_lead_time_days: int = Field(gt=0)
    payment_terms: str
    iso_certified: bool
    is_active: bool = True

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid_tiers = {"TIER_1", "TIER_2", "TIER_3"}
        if v not in valid_tiers:
            raise ValueError(f"Invalid supplier tier: {v}. Expected one of {valid_tiers}")
        return v


class MaterialInboundSchema(BaseModel):
    material_id: str
    sku: str
    name: str
    category: str
    unit_of_measure: str
    standard_cost: float = Field(gt=0.0)
    current_unit_price: float = Field(gt=0.0)
    safety_stock_level: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    target_stock_level: int = Field(ge=0)
    min_order_qty: int = Field(gt=0)
    lead_time_days: int = Field(gt=0)
    is_critical: bool
    primary_supplier_id: str
    secondary_supplier_id: str | None = None

    @field_validator("reorder_point")
    @classmethod
    def validate_reorder_point(cls, v: int, info) -> int:
        safety_stock = info.data.get("safety_stock_level")
        if safety_stock is not None and v < safety_stock:
            raise ValueError(f"Reorder point ({v}) must be greater than or equal to safety stock ({safety_stock})")
        return v


class PurchaseOrderInboundSchema(BaseModel):
    po_id: str
    po_number: str
    supplier_id: str
    factory_id: str
    warehouse_id: str
    order_date: str
    promised_delivery_date: str
    status: str
    total_amount: float = Field(ge=0.0)
    currency: str = "USD"

    @field_validator("promised_delivery_date")
    @classmethod
    def validate_date_sequence(cls, v: str, info) -> str:
        order_date_str = info.data.get("order_date")
        if order_date_str:
            order_dt = datetime.strptime(order_date_str, "%Y-%m-%d")
            deliv_dt = datetime.strptime(v, "%Y-%m-%d")
            if deliv_dt < order_dt:
                raise ValueError(f"Promised delivery date ({v}) cannot be before order date ({order_date_str})")
        return v


class InventoryMovementInboundSchema(BaseModel):
    movement_id: str
    material_id: str
    warehouse_id: str
    factory_id: str
    movement_date: str
    movement_type: str
    quantity: int
    reference_doc_type: str
    reference_doc_id: str

    @field_validator("movement_type")
    @classmethod
    def validate_movement_type(cls, v: str) -> str:
        valid_types = {
            "GOODS_RECEIPT", "PRODUCTION_ISSUE", "SCRAP", 
            "TRANSFER_IN", "TRANSFER_OUT", "CYCLE_ADJUSTMENT"
        }
        if v not in valid_types:
            raise ValueError(f"Invalid movement type '{v}'. Allowed: {valid_types}")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity_logic(cls, v: int, info) -> int:
        mov_type = info.data.get("movement_type")
        if mov_type == "GOODS_RECEIPT" and v <= 0:
            raise ValueError("GOODS_RECEIPT movements must have positive quantity.")
        if mov_type in ("PRODUCTION_ISSUE", "SCRAP") and v > 0:
            raise ValueError(f"{mov_type} movements must have negative quantity consumption.")
        return v


class ETLValidator:
    """
    Validates batch datasets against Pydantic schemas, identifies duplicates,
    and partitions the records into valid records and rejected dead-letter records.
    """
    SCHEMA_MAP = {
        "suppliers": (SupplierInboundSchema, "supplier_id"),
        "materials": (MaterialInboundSchema, "material_id"),
        "purchase_orders": (PurchaseOrderInboundSchema, "po_id"),
        "inventory_movements": (InventoryMovementInboundSchema, "movement_id")
    }

    @classmethod
    def validate_records(
        cls, 
        entity_name: str, 
        records: List[Dict[str, Any]], 
        pipeline_name: str = "ETL_INBOUND_PIPELINE",
        batch_id: str = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns: (valid_records, rejected_records)
        """
        if entity_name not in cls.SCHEMA_MAP:
            # Pass through if no explicit schema registered
            return records, []

        schema_cls, pk_field = cls.SCHEMA_MAP[entity_name]
        valid_records = []
        rejected_records = []
        seen_pks = set()

        for row in records:
            pk_val = row.get(pk_field)

            # 1. Duplicate detection check
            if pk_val in seen_pks:
                rejected_records.append({
                    "pipeline_name": pipeline_name,
                    "batch_id": batch_id,
                    "source_table": f"raw_{entity_name}",
                    "payload": json.dumps(row),
                    "error_code": "ERR_DUPLICATE_KEY",
                    "error_reason": f"Duplicate primary business key '{pk_val}' detected in batch."
                })
                continue

            # 2. Pydantic schema & logic validation
            try:
                validated_model = schema_cls(**row)
                valid_records.append(validated_model.model_dump())
                seen_pks.add(pk_val)
            except ValidationError as err:
                errors_summary = "; ".join([f"{e['loc'][0]}: {e['msg']}" for e in err.errors()])
                rejected_records.append({
                    "pipeline_name": pipeline_name,
                    "batch_id": batch_id,
                    "source_table": f"raw_{entity_name}",
                    "payload": json.dumps(row),
                    "error_code": "ERR_SCHEMA_VALIDATION",
                    "error_reason": errors_summary
                })
            except Exception as ex:
                rejected_records.append({
                    "pipeline_name": pipeline_name,
                    "batch_id": batch_id,
                    "source_table": f"raw_{entity_name}",
                    "payload": json.dumps(row),
                    "error_code": "ERR_UNEXPECTED",
                    "error_reason": str(ex)
                })

        return valid_records, rejected_records
