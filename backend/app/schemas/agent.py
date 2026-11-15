from typing import Optional
from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    trigger_keywords: str = Field(default="", max_length=500)
    action_type: str = Field(default="custom", max_length=50)
    skill_prompt: str = Field(default="", max_length=2000)
    data_config: Optional[dict] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    trigger_keywords: Optional[str] = Field(None, max_length=500)
    action_type: Optional[str] = Field(None, max_length=50)
    skill_prompt: Optional[str] = Field(None, max_length=2000)
    data_config: Optional[dict] = None


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=100)
    avatar_emoji: str = Field(default="🤖", max_length=10)
    role_description: str = Field(default="", max_length=500)
    system_prompt: str = Field(min_length=1, max_length=3000)
    provider: str = Field(default="anthropic", max_length=50)
    api_base: str = Field(default="", max_length=500)
    api_key: str = Field(default="", max_length=2000)
    agent_model: str = Field(default="", max_length=100)
    skills: list[SkillCreate] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_emoji: Optional[str] = Field(None, max_length=10)
    role_description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=1, max_length=3000)
    is_active: Optional[bool] = None
    provider: Optional[str] = Field(None, max_length=50)
    api_base: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=2000)
    agent_model: Optional[str] = Field(None, max_length=100)
    skills: Optional[list[SkillCreate]] = None