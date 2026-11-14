from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ReconPeriodCreate(BaseModel):
    period: str = Field(min_length=7, max_length=7)
    idh_id: str = Field(min_length=1)


class ReconItemUpdate(BaseModel):
    dispute_reason: str = ""
    dispute_attachments: list = []


class AdjustCreate(BaseModel):
    period_id: int
    recon_item_id: int
    lot_id: str
    qty_before: int
    qty_after: int
    diff_code: str
    reason: str = ""


class AdjustApprove(BaseModel):
    approved_by: str
    role: str  # factory or idh