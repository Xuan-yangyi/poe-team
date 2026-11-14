from typing import Optional
from pydantic import BaseModel, Field


class AlertAck(BaseModel):
    acknowledged_by: str = Field(min_length=1)


class AlertResolve(BaseModel):
    resolved_by: str = Field(min_length=1)
    resolution: str = ""