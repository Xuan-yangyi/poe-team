import uuid
from datetime import date
from sqlalchemy import String, Integer, SmallInteger, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class Shipment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipment"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    dn_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    wo_id: Mapped[str] = mapped_column(nullable=False)
    idh_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    eta: Mapped[date | None] = mapped_column(Date, nullable=True)
    carrier: Mapped[str] = mapped_column(String(100), default="")
    tracking_no: Mapped[str] = mapped_column(String(100), default="")


class ShipmentLine(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipment_line"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id: Mapped[str] = mapped_column(nullable=False)
    line_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    material_id: Mapped[str] = mapped_column(nullable=False)
    lot_id: Mapped[str] = mapped_column(nullable=False)
    container_id: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_container_id: Mapped[str] = mapped_column(String(50), default="")
    container_type: Mapped[str] = mapped_column(String(20), default="reel")
    qty_per_container: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_shipped: Mapped[int] = mapped_column(Integer, nullable=False)


class GoodsReceipt(Base, TimestampMixin, TenantMixin):
    __tablename__ = "goods_receipt"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    dn_no: Mapped[str] = mapped_column(String(30), nullable=False)
    container_id: Mapped[str] = mapped_column(String(50), nullable=False)
    lot_id: Mapped[str] = mapped_column(nullable=False)
    qty_received: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_shipped: Mapped[int] = mapped_column(Integer, nullable=False)
    diff_reason: Mapped[str] = mapped_column(String(20), default="")
    received_by: Mapped[str] = mapped_column(String(100), default="")