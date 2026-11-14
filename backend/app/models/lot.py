import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class Lot(Base, TimestampMixin, TenantMixin):
    __tablename__ = "lot"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    lot_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    material_id: Mapped[str] = mapped_column(nullable=False)
    wafer_lot: Mapped[str] = mapped_column(String(50), default="")
    assembly_lot: Mapped[str] = mapped_column(String(50), default="")
    date_code: Mapped[str] = mapped_column(String(10), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")