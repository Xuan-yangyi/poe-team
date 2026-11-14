from typing import Optional
from pydantic import BaseModel, Field


class InventoryQuery(BaseModel):
    material_id: Optional[str] = None
    lot_id: Optional[str] = None
    idh_id: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)