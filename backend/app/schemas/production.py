from pydantic import BaseModel, Field


class IssueCreate(BaseModel):
    wo_id: str
    lot_id: str
    material_id: str
    qty: int = Field(gt=0)
    operator: str = ""
    scan_method: str = "h5"


class WipReportCreate(BaseModel):
    wo_id: str
    process_code: str = Field(min_length=1)
    process_seq: int = Field(ge=1)
    qty_in: int = Field(ge=0)
    qty_out: int = Field(ge=0)
    qty_scrap: int = Field(default=0, ge=0)
    scrap_reason: str = ""
    reported_by: str = ""


class FgReceiptCreate(BaseModel):
    wo_id: str
    sn: str = Field(min_length=1)
    qty: int = Field(default=1, gt=0)
    lot_id: str
    received_by: str = ""