from typing import Optional
from pydantic import BaseModel, Field


# Supported provider presets
PROVIDER_PRESETS = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "api_base": "https://api.anthropic.com",
        "model": "claude-sonnet-4-20250514",
    },
    "openai": {
        "label": "OpenAI (GPT)",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4o",
    },
    "openai_compatible": {
        "label": "OpenAI 兼容 (DeepSeek / 通义千问 / 本地)",
        "api_base": "",
        "model": "",
    },
    "custom": {
        "label": "自定义",
        "api_base": "",
        "model": "",
    },
}


class LLMConfigCreate(BaseModel):
    provider: str = Field(default="anthropic", max_length=50)
    api_base: str = Field(default="https://api.anthropic.com", max_length=500)
    api_key: str = Field(default="", max_length=2000)
    model: str = Field(default="claude-sonnet-4-20250514", max_length=100)
    extra_params: Optional[dict] = None
    description: str = Field(default="", max_length=200)


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = Field(None, max_length=50)
    api_base: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=2000)
    model: Optional[str] = Field(None, max_length=100)
    extra_params: Optional[dict] = None
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class LLMConfigTest(BaseModel):
    """Test connectivity to the configured LLM."""
    message: str = Field(default="Hello, please respond with 'OK'.", max_length=500)