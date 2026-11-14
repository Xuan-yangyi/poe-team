import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class ReconPeriod(Base, TimestampMixin, TenantMixin):
    __tablename__ = "recon_period"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    idh_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    matched: Mapped[int] = mapped_column(Integer, default=0)
    diff_count: Mapped[int] = mapped_column(Integer, default=0)
    diff_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReconItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "recon_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(Integer, nullable=False)
    material_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    lot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    diff_code: Mapped[str] = mapped_column(String(10), nullable=False)
    qty_a: Mapped[int] = mapped_column(Integer, default=0)
    qty_b: Mapped[int] = mapped_column(Integer, default=0)
    qty_c: Mapped[int] = mapped_column(Integer, default=0)
    qty_diff: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    dispute_reason: Mapped[str] = mapped_column(Text, default="")
    dispute_attachments: Mapped[list] = mapped_column(JSONB, default=[])
    dispute_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Adjustment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "adjustment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    adj_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    period_id: Mapped[int] = mapped_column(Integer, nullable=False)
    recon_item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    lot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    qty_before: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_after: Mapped[int] = mapped_column(Integer, nullable=False)
    diff_code: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    factory_approved_by: Mapped[str] = mapped_column(String(100), default="")
    factory_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idh_approved_by: Mapped[str] = mapped_column(String(100), default="")
    idh_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)