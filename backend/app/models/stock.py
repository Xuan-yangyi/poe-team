import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TenantMixin


class StockLedger(Base, TenantMixin):
    __tablename__ = "stock_ledger"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(nullable=False)
    lot_id: Mapped[str] = mapped_column(nullable=False)
    idh_id: Mapped[str] = mapped_column(String(50), default="")
    owner: Mapped[str] = mapped_column(String(20), default="factory")
    status: Mapped[str] = mapped_column(String(20), default="available")
    qty_change: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_after: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)