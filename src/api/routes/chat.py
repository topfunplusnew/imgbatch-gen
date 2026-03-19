"""用户对话接口 - OpenAI 兼容 /v1/chat/completions，支持 ChatGPT、Claude、Gemini 等"""

import json
import io
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from openai import AsyncOpenAI
import httpx
import pdfplumber
from docx import Document

from ...config.settings import settings
from ...models.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ChoiceMessage,
    Usage,
)
from ...utils.session_context import session_manager
from ...database import get_db_manager


router = APIRouter(prefix="/api/v1", tags=["chat"])


def _normalize_openai_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/v1"):
        normalized += "/v1"
    return normalized


def _get_openai_client(api_key: str | None = None) -> AsyncOpenAI:
    """使用前端请求中的 API Key 构建 OpenAI 兼容客户端。"""
    key = (api_key or "").strip()
    if not key:
        raise ValueError("API Key 未配置，请在前端页面设置 API Key")
    base_url = _normalize_openai_base_url(settings.openai_base_url or settings.relay_base_url or None)
    logger.info(f"OpenAI client base_url={base_url}")
    return AsyncOpenAI(
        api_key=key,
        base_url=base_url,
    )


def _extract_api_key(http_request: Request) -> str | None:
    """从 HTTP Authorization header 提取 Bearer token"""
    auth = http_request.headers.get("Authorization") or http_request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:].strip() or None
    return None


def _require_api_key(http_request: Request) -> str:
    api_key = _extract_api_key(http_request)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization Bearer API Key. Please configure API Key in frontend.",
        )
    return api_key


def _get_model_endpoint_type(model_name: str, app_state) -> str:
    """
    根据模型的 supported_endpoint_types 决定使用哪种 API 端点。
    返回 'openai'（chat completions）或 'openai-response'（responses API）。
    """
    try:
        model_registry = getattr(app_state, "model_registry", None)
        if not model_registry:
            return "openai"
        model_info = model_registry.get_model_info(model_name)
        if not model_info:
            return "openai"
        types = model_info.supported_endpoint_types
        # 优先用 openai（chat completions）
        if "openai" in types:
            return "openai"
        if "openai-response" in types:
            return "openai-response"
        # anthropic/gemini 等也走 chat completions 兼容接口
        return "openai"
    except Exception:
        return "openai"


def _request_to_kwargs(req: ChatCompletionRequest) -> Dict[str, Any]:
    """将 Pydantic 请求转为 OpenAI client.create() 的 kwargs，仅包含非 None 字段"""
    messages = []
    for m in req.messages:
        msg = {"role": m.role, "content": m.content}
        messages.append(msg)

    kwargs: Dict[str, Any] = {
        "model": req.model,
        "messages": messages,
        "stream": req.stream or False,
    }
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature
    if req.top_p is not None:
        kwargs["top_p"] = req.top_p
    if req.n is not None:
        kwargs["n"] = req.n
    if req.stop is not None:
        kwargs["stop"] = req.stop
    if req.max_tokens is not None:
        kwargs["max_tokens"] = req.max_tokens
    if req.presence_penalty is not None:
        kwargs["presence_penalty"] = req.presence_penalty
    if req.frequency_penalty is not None:
        kwargs["frequency_penalty"] = req.frequency_penalty
    if req.user is not None:
        kwargs["user"] = req.user
    if req.response_format is not None:
        kwargs["response_format"] = req.response_format.model_dump(exclude_none=True)
    if req.tools is not None:
        kwargs["tools"] = req.tools
    if req.tool_choice is not None:
        kwargs["tool_choice"] = req.tool_choice
    return kwargs


def _messages_to_responses_input(messages: list) -> list:
    """将 chat messages 格式转为 Responses API 的 input 格式"""
    result = []
    for m in messages:
        content = m.get("content", "")
        role = m.get("role", "user")
        if isinstance(content, list):
            # 多模态内容直接透传
            result.append({"role": role, "content": content})
        else:
            result.append({"role": role, "content": content})
    return result


async def _call_responses_api(client: AsyncOpenAI, req: ChatCompletionRequest, messages: list, stream: bool) -> Any:
    """调用 Responses API (/v1/responses)"""
    input_data = _messages_to_responses_input(messages)
    # 取最后一条 user 消息作为 input，其余作为 previous_messages
    kwargs: Dict[str, Any] = {
        "model": req.model,
        "input": input_data,
    }
    if req.max_tokens is not None:
        kwargs["max_output_tokens"] = req.max_tokens
    if stream:
        kwargs["stream"] = True
    return await client.responses.create(**kwargs)


async def _process_files_to_messages(files: list[str], messages: list) -> list:
    """将文件转换为多模态消息格式或文本内容"""
    if not files:
        return messages

    image_urls = []
    doc_texts = []

    for file_url in files:
        try:
            ext = file_url.split('?')[0].rsplit('.', 1)[-1].lower()
            filename = file_url.split('?')[0].rsplit('/', 1)[-1]

            # 图片：收集URL
            if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'):
                image_urls.append(file_url)
                logger.info(f"添加图片: {filename}")
                continue

            # 下载文档文件
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(file_url)
                resp.raise_for_status()
            file_bytes = resp.content

            # PDF：提取文本
            if ext == 'pdf':
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if text.strip():
                    doc_texts.append(f"[文档: {filename}]\n{text[:10000]}")
                    logger.info(f"提取PDF文本: {filename}, {len(text)} 字符")

            # Word：提取文本
            elif ext == 'docx':
                doc = Document(io.BytesIO(file_bytes))
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                if text.strip():
                    doc_texts.append(f"[文档: {filename}]\n{text[:10000]}")
                    logger.info(f"提取Word文本: {filename}, {len(text)} 字符")

        except Exception as e:
            logger.warning(f"处理文件 {file_url} 失败: {e}")

    if not image_urls and not doc_texts:
        return messages

    if messages and messages[-1].get('role') == 'user':
        last_msg = messages[-1]
        content = last_msg.get('content', '')

        # 文档文本：前置添加
        if doc_texts:
            content = "\n\n".join(doc_texts) + "\n\n" + content

        # 图片：多模态格式
        if image_urls:
            multimodal_content = [{"type": "text", "text": content}]
            for url in image_urls:
                multimodal_content.append({"type": "image_url", "image_url": {"url": url}})
            messages[-1]['content'] = multimodal_content
        else:
            messages[-1]['content'] = content

    return messages


def _response_from_openai(raw: Any) -> ChatCompletionResponse:
    """将 OpenAI 客户端返回对象转为 ChatCompletionResponse"""
    usage = None
    if getattr(raw, "usage", None) and raw.usage:
        usage = Usage(
            prompt_tokens=raw.usage.prompt_tokens or 0,
            completion_tokens=raw.usage.completion_tokens or 0,
            total_tokens=raw.usage.total_tokens or 0,
        )
    choices = []
    for i, c in enumerate(getattr(raw, "choices", []) or []):
        msg = getattr(c, "message", None)
        content = getattr(msg, "content", None) if msg else None
        role = getattr(msg, "role", "assistant") if msg else "assistant"
        choices.append(
            Choice(
                index=getattr(c, "index", i),
                message=ChoiceMessage(role=role, content=content),
                finish_reason=getattr(c, "finish_reason", None),
            )
        )
    return ChatCompletionResponse(
        id=getattr(raw, "id", "chatcmpl-unknown") or "chatcmpl-unknown",
        object=getattr(raw, "object", "chat.completion") or "chat.completion",
        created=getattr(raw, "created", 0) or 0,
        choices=choices,
        usage=usage,
    )


def _response_from_responses_api(raw: Any) -> ChatCompletionResponse:
    """将 Responses API 返回对象转为 ChatCompletionResponse"""
    # Responses API 返回 output 列表
    content = ""
    try:
        for item in getattr(raw, "output", []) or []:
            if getattr(item, "type", "") == "message":
                for part in getattr(item, "content", []) or []:
                    if getattr(part, "type", "") == "output_text":
                        content += getattr(part, "text", "")
    except Exception:
        content = str(raw)

    usage = None
    if getattr(raw, "usage", None):
        u = raw.usage
        usage = Usage(
            prompt_tokens=getattr(u, "input_tokens", 0) or 0,
            completion_tokens=getattr(u, "output_tokens", 0) or 0,
            total_tokens=(getattr(u, "input_tokens", 0) or 0) + (getattr(u, "output_tokens", 0) or 0),
        )

    return ChatCompletionResponse(
        id=getattr(raw, "id", "resp-unknown") or "resp-unknown",
        object="chat.completion",
        created=0,
        choices=[Choice(
            index=0,
            message=ChoiceMessage(role="assistant", content=content),
            finish_reason="stop",
        )],
        usage=usage,
    )


@router.post("/chat/completions")
async def chat_completions(http_request: Request):
    """
    聊天补全接口，与 OpenAI /v1/chat/completions 语义一致。
    根据模型的 supported_endpoint_types 自动选择 chat completions 或 responses API。
    """
    try:
        body = await http_request.json()
        req = ChatCompletionRequest.model_validate(body)
    except Exception as e:
        logger.warning(f"解析请求失败: {e}")
        raise HTTPException(status_code=400, detail=f"请求格式错误: {str(e)}")

    if not req.model or not req.messages:
        raise HTTPException(status_code=400, detail="model 与 messages 为必填")

    request_api_key = _require_api_key(http_request)

    try:
        client = _get_openai_client(request_api_key)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # 根据模型的 supported_endpoint_types 决定端点
    endpoint_type = _get_model_endpoint_type(req.model, http_request.app.state)
    logger.info(f"模型 {req.model} 使用端点类型: {endpoint_type}")

    # 处理上下文管理
    messages_to_send = [{"role": m.role, "content": m.content} for m in req.messages]

    # 处理文件（图片）
    if req.files:
        messages_to_send = await _process_files_to_messages(req.files, messages_to_send)

    if req.enable_context and req.session_id:
        messages_to_send = await session_manager.get_context_messages(
            session_id=req.session_id,
            new_messages=messages_to_send,
            api_key=request_api_key,
            base_url=settings.openai_base_url or settings.relay_base_url,
            summary_model=req.model
        )
        logger.info(f"会话 {req.session_id} 使用上下文，共 {len(messages_to_send)} 条消息")

    try:
        if endpoint_type == "openai-response":
            # 走 Responses API
            if req.stream:
                async def stream_responses():
                    collected_content = ""
                    resp = await _call_responses_api(client, req, messages_to_send, stream=True)
                    async for event in resp:
                        event_type = getattr(event, "type", "")
                        if event_type == "response.output_text.delta":
                            delta = getattr(event, "delta", "")
                            collected_content += delta
                            chunk = {
                                "id": "resp-stream",
                                "object": "chat.completion.chunk",
                                "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}]
                            }
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                        elif event_type == "response.completed":
                            yield "data: [DONE]\n\n"
                            if req.enable_context and req.session_id and collected_content:
                                user_msg = next((m.content for m in req.messages if m.role == "user"), "")
                                if isinstance(user_msg, list):
                                    user_msg = str(user_msg)
                                session_manager.record_exchange(req.session_id, user_msg, collected_content)

                return StreamingResponse(
                    stream_responses(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
                )
            else:
                raw = await _call_responses_api(client, req, messages_to_send, stream=False)
                resp = _response_from_responses_api(raw)
                if req.enable_context and req.session_id and resp.choices:
                    user_msg = next((m.content for m in req.messages if m.role == "user"), "")
                    if isinstance(user_msg, list):
                        user_msg = str(user_msg)
                    session_manager.record_exchange(req.session_id, user_msg, resp.choices[0].message.content or "")
                return resp.model_dump(exclude_none=True)

        else:
            # 走 Chat Completions API
            kwargs = _request_to_kwargs(req)
            kwargs["messages"] = messages_to_send

            if kwargs.get("stream"):
                async def stream_events():
                    stream = await client.chat.completions.create(**kwargs)
                    collected_content = ""
                    async for chunk in stream:
                        if hasattr(chunk, "choices") and chunk.choices:
                            delta = getattr(chunk.choices[0], "delta", None)
                            if delta and hasattr(delta, "content") and delta.content:
                                collected_content += delta.content
                        try:
                            if hasattr(chunk, "model_dump"):
                                data = chunk.model_dump(exclude_none=True)
                            else:
                                data = dict(chunk) if hasattr(chunk, "__iter__") else {}
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        except Exception:
                            pass
                    yield "data: [DONE]\n\n"
                    if req.enable_context and req.session_id and collected_content:
                        user_msg = next((m.content for m in req.messages if m.role == "user"), "")
                        if isinstance(user_msg, list):
                            user_msg = str(user_msg)
                        session_manager.record_exchange(req.session_id, user_msg, collected_content)

                return StreamingResponse(
                    stream_events(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
                )
            else:
                kwargs["stream"] = False
                raw = await client.chat.completions.create(**kwargs)
                resp = _response_from_openai(raw)
                if req.enable_context and req.session_id and resp.choices:
                    user_msg = next((m.content for m in req.messages if m.role == "user"), "")
                    if isinstance(user_msg, list):
                        user_msg = str(user_msg)
                    session_manager.record_exchange(req.session_id, user_msg, resp.choices[0].message.content or "")
                return resp.model_dump(exclude_none=True)

    except Exception as e:
        logger.error(f"对话请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

