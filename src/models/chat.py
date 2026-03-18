"""聊天对话请求/响应模型 - 与 OpenAI /v1/chat/completions 语义一致"""

from typing import Optional, List, Union, Any, Dict
from pydantic import BaseModel, Field


# -------- 多模态消息内容 --------


class ImageURL(BaseModel):
    """图片 URL（多模态 content 中的 image_url）"""
    url: str = Field(..., description="图片 URL")


class ContentPartText(BaseModel):
    """文本内容块"""
    type: str = "text"
    text: str = Field(..., description="文本内容")


class ContentPartImageURL(BaseModel):
    """图片内容块"""
    type: str = "image_url"
    image_url: ImageURL = Field(..., description="图片 URL 信息")


# ContentPart 为 text 或 image_url 之一
ContentPart = Union[ContentPartText, ContentPartImageURL]


class ChatMessage(BaseModel):
    """单条聊天消息"""
    role: str = Field(..., description="角色：system / user / assistant")
    content: Union[str, List[Dict[str, Any]]] = Field(
        ...,
        description="内容：字符串或多模态内容列表 [{type, text} | {type, image_url}]",
    )


class ResponseFormat(BaseModel):
    """响应格式（如 JSON 模式）"""
    type: Optional[str] = Field(None, description="如 json_object")


# -------- 请求 --------


class ChatCompletionRequest(BaseModel):
    """聊天补全请求 - OpenAI 兼容"""

    model: str = Field(..., description="模型 ID，如 gpt-4、claude-3-5-sonnet、gemini-2.5-flash")
    messages: List[ChatMessage] = Field(..., description="消息列表")

    temperature: Optional[float] = Field(None, description="采样温度 0~2")
    top_p: Optional[float] = Field(None, description="核采样 top_p")
    n: Optional[int] = Field(1, description="生成条数")
    stream: Optional[bool] = Field(False, description="是否流式返回")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止序列")
    max_tokens: Optional[int] = Field(None, description="最大生成 token 数")
    presence_penalty: Optional[float] = Field(None, description="存在惩罚 -2~2")
    frequency_penalty: Optional[float] = Field(None, description="频率惩罚 -2~2")
    user: Optional[str] = Field(None, description="终端用户标识")
    response_format: Optional[ResponseFormat] = Field(None, description="响应格式")
    tools: Optional[List[Any]] = Field(None, description="工具列表")
    tool_choice: Optional[Any] = Field(None, description="工具选择")

    # 上下文管理扩展
    session_id: Optional[str] = Field(None, description="会话ID，用于维护对话历史")
    enable_context: Optional[bool] = Field(False, description="是否启用上下文管理")
    files: Optional[List[str]] = Field(None, description="文件ID或URL列表")


# -------- 响应（非流式）--------


class Usage(BaseModel):
    """Token 使用量"""
    prompt_tokens: int = Field(..., description="输入 token 数")
    completion_tokens: int = Field(..., description="生成 token 数")
    total_tokens: int = Field(..., description="总 token 数")


class ChoiceMessage(BaseModel):
    """choices[].message"""
    role: str = Field(..., description="角色")
    content: Optional[str] = Field(None, description="内容")


class Choice(BaseModel):
    """choices 项"""
    index: int = Field(..., description="索引")
    message: ChoiceMessage = Field(..., description="消息")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class ChatCompletionResponse(BaseModel):
    """聊天补全响应 - OpenAI 兼容"""

    id: str = Field(..., description="本次补全 ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    choices: List[Choice] = Field(..., description="候选回复")
    usage: Optional[Usage] = Field(None, description="Token 使用量（流式时可为空）")
