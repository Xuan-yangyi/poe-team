import uuid
from sqlalchemy import String, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class Issue(Base, TenantMixin):
    __tablename__ = "issue"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id: Mapped[str] = mapped_column(nullable=False)
    lot_id: Mapped[str] = mapped_column(nullable=False)
    material_id: Mapped[str] = mapped_column(nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    operator: Mapped[str] = mapped_column(String(100), default="")
    scan_method: Mapped[str] = mapped_column(String(20), default="h5")
    created_at: Mapped[str] = mapped_column(nullable=False, default="")


class WipReport(Base, TenantMixin):
    __tablename__ = "wip_report"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id: Mapped[str] = mapped_column(nullable=False)
    process_code: Mapped[str] = mapped_column(String(20), nullable=False)
    process_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    qty_in: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_out: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_scrap: Mapped[int] = mapped_column(Integer, default=0)
    scrap_reason: Mapped[str] = mapped_column(String(50), default="")
    reported_by: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[str] = mapped_column(nullable=False, default="")


class FgReceipt(Base, TenantMixin):
    __tablename__ = "fg_receipt"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id: Mapped[str] = mapped_column(nullable=False)
    sn: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    lot_id: Mapped[str] = mapped_column(nullable=False)
    received_by: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[str] = mapped_column(nullable=False, default="")