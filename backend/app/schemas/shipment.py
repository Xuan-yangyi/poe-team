from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ShipmentLineCreate(BaseModel):
    material_id: str
    lot_id: str
    container_id: str = Field(min_length=1)
    parent_container_id: str = ""
    container_type: str = "reel"
    qty_per_container: int = Field(gt=0)
    qty_shipped: int = Field(gt=0)


class ShipmentCreate(BaseModel):
    wo_id: str
    idh_id: str = Field(min_length=1)
    eta: Optional[date] = None
    carrier: str = ""
    tracking_no: str = ""
    lines: list[ShipmentLineCreate] = Field(min_length=1)


class GoodsReceiptCreate(BaseModel):
    dn_no: str
    lot_id: str
    container_id: str
    qty_received: int = Field(gt=0)
    qty_shipped: int = Field(gt=0)
    diff_reason: str = ""
    received_by: str = ""