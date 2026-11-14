from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class WoLineCreate(BaseModel):
    material_id: str
    qty_ordered: int = Field(gt=0)
    unit_price: Optional[Decimal] = None


class WorkOrderCreate(BaseModel):
    idh_id: str = Field(min_length=1, max_length=50)
    customer_id: str = ""
    due_date: date
    bom_ver: str = ""
    settle_mode: str = "purchase"
    priority: int = Field(default=5, ge=1, le=10)
    lines: list[WoLineCreate] = Field(min_length=1)


class WorkOrderIssue(BaseModel):
    pass  # No additional fields needed


class WorkOrderAccept(BaseModel):
    confirmed_due_date: Optional[date] = None
    remark: str = ""


class WorkOrderChange(BaseModel):
    change_type: str = Field(..., pattern="^(suspended|changed|cancelled)$")
    reason_code: str = ""
    remark: str = ""


class WorkOrderListQuery(BaseModel):
    status: Optional[str] = None
    idh_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class WoLineResponse(BaseModel):
    id: str
    line_no: int
    material_id: str
    qty_ordered: int
    qty_shipped: int
    qty_received: int
    qty_consumed: int
    unit_price: Optional[Decimal] = None


class WorkOrderResponse(BaseModel):
    id: str
    wo_no: str
    idh_id: str
    customer_id: str
    status: str
    due_date: Optional[date]
    confirmed_due_date: Optional[date]
    bom_ver: str
    settle_mode: str
    priority: int
    lines: list[WoLineResponse] = []
    created_at: str
    updated_at: str