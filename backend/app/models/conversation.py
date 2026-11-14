import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, Text, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class Conversation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    conv_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ref_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ConversationMember(Base, TenantMixin):
    __tablename__ = "conversation_member"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)


class Message(Base, TenantMixin):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    msg_type: Mapped[str] = mapped_column(String(20), default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_msg_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)


class MsgTag(Base, TenantMixin):
    __tablename__ = "msg_tag"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    tag_value: Mapped[str] = mapped_column(String(500), nullable=False)
    tagged_by: Mapped[str] = mapped_column(String(20), default="ai")
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)