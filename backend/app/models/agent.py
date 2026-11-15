import uuid
from sqlalchemy import String, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, TenantMixin


class Agent(Base, TimestampMixin, TenantMixin):
    """AI agent that can participate in group conversations as a role."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(10), default="🤖")
    role_description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), default="claude")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    # Every agent gets a user record for conversation membership
    user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    # Agent's own LLM config (each agent has independent credentials)
    provider: Mapped[str] = mapped_column(String(50), default="anthropic")
    api_base: Mapped[str] = mapped_column(String(500), default="")
    api_key: Mapped[str] = mapped_column(Text, default="")
    agent_model: Mapped[str] = mapped_column(String(100), default="")
    # Legacy: reference to shared llm_config (kept for backward compatibility)
    llm_config_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    skills: Mapped[list["AgentSkill"]] = relationship(
        "AgentSkill", back_populates="agent", cascade="all, delete-orphan"
    )


class AgentSkill(Base, TimestampMixin, TenantMixin):
    """A capability attached to an agent — defines triggers, data sources, and response template."""

    __tablename__ = "agent_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    # Comma-separated or JSON array of trigger keywords
    trigger_keywords: Mapped[str] = mapped_column(Text, default="")
    # What this skill does: analyze_risk, check_progress, query_inventory, summarize, custom
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Extra prompt appended to system_prompt when this skill activates
    skill_prompt: Mapped[str] = mapped_column(Text, default="")
    # JSON config for data sources: {"tables": ["work_orders"], "filters": {...}}
    data_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="skills")