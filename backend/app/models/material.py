import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, TenantMixin


class Material(Base, TimestampMixin, TenantMixin):
    __tablename__ = "material"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    material_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    std_loss_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    aliases = relationship("MaterialAlias", back_populates="material")


class MaterialAlias(Base, TimestampMixin, TenantMixin):
    __tablename__ = "material_alias"
    __table_args__ = ()

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(nullable=False)
    alias_code: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="idh")

    material = relationship("Material", back_populates="aliases")