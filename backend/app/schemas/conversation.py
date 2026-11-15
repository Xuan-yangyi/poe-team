from typing import Optional
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    conversation_id: str = ""
    msg_type: str = "text"
    content: str = Field(min_length=1)
    parent_msg_id: Optional[str] = None


class ConversationCreate(BaseModel):
    conv_type: str = Field(min_length=1, max_length=20)
    ref_id: str = Field(min_length=1, max_length=100)
    title: str = Field(default="", max_length=200)


class GroupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    member_ids: list[str] = Field(min_length=1, max_length=50)


class TagCreate(BaseModel):
    message_id: str
    tag_type: str = Field(min_length=1, max_length=30)
    tag_value: str = Field(min_length=1, max_length=500)
    tagged_by: str = "ai"
    confidence: Optional[float] = Field(None, ge=0, le=1)