import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, SmallInteger, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, TenantMixin


class WorkOrder(Base, TimestampMixin, TenantMixin):
    __tablename__ = "work_order"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    idh_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bom_ver: Mapped[str] = mapped_column(String(20), default="")
    settle_mode: Mapped[str] = mapped_column(String(20), default="purchase")
    priority: Mapped[int] = mapped_column(SmallInteger, default=5)

    lines = relationship("WoLine", back_populates="work_order")


class WoLine(Base, TimestampMixin, TenantMixin):
    __tablename__ = "wo_line"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    wo_id: Mapped[str] = mapped_column(nullable=False)
    line_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    material_id: Mapped[str] = mapped_column(nullable=False)
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_shipped: Mapped[int] = mapped_column(Integer, default=0)
    qty_received: Mapped[int] = mapped_column(Integer, default=0)
    qty_consumed: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)

    work_order = relationship("WorkOrder", back_populates="lines")