import uuid
from sqlalchemy import String, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, TenantMixin


class LLMConfig(Base, TimestampMixin, TenantMixin):
    """Per-tenant LLM provider configuration."""

    __tablename__ = "llm_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Provider: anthropic, openai, openai_compatible, custom
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="anthropic")
    # API base URL (e.g., https://api.anthropic.com, https://api.openai.com/v1, or custom)
    api_base: Mapped[str] = mapped_column(String(500), nullable=False, default="https://api.anthropic.com")
    # API key (encrypted or plaintext — for MVP, stored as-is behind auth)
    api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Model name (e.g., claude-sonnet-4-20250514, gpt-4o, deepseek-chat)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="claude-sonnet-4-20250514")
    # Extra parameters as JSON: {"temperature": 0.7, "max_tokens": 1024, ...}
    extra_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Optional description for this config
    description: Mapped[str] = mapped_column(String(200), default="")