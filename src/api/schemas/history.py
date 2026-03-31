"""History route request/response schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Conversation message model."""

    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")
    created_at: Optional[str] = Field(None, description="创建时间")


class ConversationInfo(BaseModel):
    """Conversation info model."""

    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    message_count: int = Field(..., description="消息数量")
    image_count: int = Field(..., description="图片数量")


class ConversationSummary(BaseModel):
    """Conversation summary model."""

    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题（第一条用户消息）")
    created_at: str = Field(..., description="创建时间")
    message_count: int = Field(..., description="消息数量")
    last_message: Optional[str] = Field(None, description="最后一条消息")


class CreateSessionRequest(BaseModel):
    """Create conversation session request."""

    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题")
    model: str = Field(..., description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")


class SaveMessageRequest(BaseModel):
    """Save conversation message request."""

    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")
    timestamp: Optional[str] = Field(None, description="时间戳")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    files: Optional[List[Dict[str, Any]]] = Field(None, description="文件信息列表")
    user_request_id: Optional[str] = Field(None, description="关联的用户请求ID")

