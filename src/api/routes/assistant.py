"""统一AI助手聊天接口"""

import asyncio
import hashlib
import json
import mimetypes
import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from ...api.routes.chat import _extract_api_key, _get_openai_client
from ...api.auth import get_current_user
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from ...config.settings import settings
from ...engine import TaskManager
from ...models.image import ImageParams
from ...models.task import TaskStatus
from ...database import get_db_manager
from ...workflows import plan_assistant_execution
from ...services.account_service import get_account_service


router = APIRouter(prefix="/api/v1", tags=["assistant"])


# ==================== 请求/响应模型 ====================

class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: Any = Field(default="", description="消息内容（支持文本或多模态格式）")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class ImageParamsInput(BaseModel):
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")
    style: Optional[str] = Field(None, description="风格")
    quality: Optional[str] = Field(None, description="质量")
    n: Optional[int] = Field(None, description="生成数量")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    seed: Optional[int] = Field(None, description="随机种子")
    model_name: Optional[str] = Field(None, description="模型名称")
    provider: Optional[str] = Field(None, description="指定Provider")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数（如watermark/prompt_extend等）")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话历史")
    session_id: Optional[str] = Field(None, description="会话ID")
    files: Optional[List[str]] = Field(None, description="附件文件ID列表")
    stream: bool = Field(False, description="是否使用流式响应")
    image_params: Optional[ImageParamsInput] = Field(None, description="图像生成参数")
    model: Optional[str] = Field(None, description="聊天模型名称")
    model_type: Optional[str] = Field(None, description="模型类型: image/chat")


class Intent(BaseModel):
    type: str = Field(..., description="意图类型: single_generate/batch_generate/chat/general")
    confidence: float = Field(..., description="置信度 0-1")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="提取的参数")
    reasoning: str = Field("", description="推理过程")


class ChatResponse(BaseModel):
    message: ChatMessage
    intent: Optional[Intent] = None
    task_id: Optional[str] = None
    batch_id: Optional[str] = None
    requires_action: bool = Field(False, description="是否需要进一步操作")
    metadata: Optional[Dict[str, Any]] = None


async def _refund_frozen_billing_if_needed(
    *,
    user_id: Optional[str],
    billing_info: Optional[Dict[str, Any]],
    model_name: Optional[str],
    request_id: str,
    error_reason: str,
    provider: str = "unknown",
) -> Optional[Dict[str, Any]]:
    if not user_id or not billing_info:
        return billing_info

    if billing_info.get("status") != "frozen" or not billing_info.get("freeze_id"):
        return billing_info

    try:
        account_service = get_account_service()
        return await account_service.settle_frozen_points(
            user_id=user_id,
            freeze_id=billing_info["freeze_id"],
            success=False,
            model_name=model_name or "unknown",
            provider=provider or "unknown",
            request_id=request_id,
            prompt="",
            error_reason=error_reason,
        )
    except Exception as refund_error:
        logger.error("冻结积分返还失败: {}", refund_error)
        return billing_info


def _extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip() if content is not None else ""


def _request_messages_to_payloads(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
    return [{"role": message.role, "content": message.content} for message in messages]


def _trim_image_context_snippet(text: str, limit: int = 260) -> str:
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1]}…"


def _prepare_image_request_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Prioritize the latest image prompt while keeping recent history as auxiliary context."""
    normalized_messages: List[ChatMessage] = []
    for message in messages:
        role = str(message.role or "").strip()
        if not role:
            continue
        text = _extract_message_text(message.content)
        if role == "assistant" and (not text or text.startswith("正在处理")):
            continue
        normalized_messages.append(ChatMessage(role=role, content=message.content))

    user_messages = [message for message in normalized_messages if message.role == "user"]
    if not user_messages:
        return normalized_messages

    latest_user_message = user_messages[-1]
    previous_messages = [message for message in normalized_messages if message is not latest_user_message]

    previous_user_lines = [
        f"- {_trim_image_context_snippet(_extract_message_text(message.content), limit=240)}"
        for message in previous_messages
        if message.role == "user" and _extract_message_text(message.content)
    ][-3:]
    previous_assistant_lines = [
        f"- {_trim_image_context_snippet(_extract_message_text(message.content), limit=180)}"
        for message in previous_messages
        if message.role == "assistant" and _extract_message_text(message.content)
    ][-2:]

    if not previous_user_lines and not previous_assistant_lines:
        return [latest_user_message]

    context_sections = [
        "Image generation context rule: always treat the latest user request as the primary prompt. "
        "Use prior conversation only as optional supporting context when it clearly helps continuity.",
    ]
    if previous_user_lines:
        context_sections.append("Recent user prompts:\n" + "\n".join(previous_user_lines))
    if previous_assistant_lines:
        context_sections.append("Recent assistant outputs:\n" + "\n".join(previous_assistant_lines))

    return [
        ChatMessage(role="system", content="\n\n".join(context_sections)),
        latest_user_message,
    ]


def _plan_messages_to_chat_messages(messages: List[Dict[str, Any]]) -> List[ChatMessage]:
    normalized: List[ChatMessage] = []
    for message in messages:
        role = str(message.get("role", "")).strip()
        if not role:
            continue
        normalized.append(ChatMessage(role=role, content=message.get("content", "")))
    return normalized


def _normalize_reference_image_sources(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _guess_image_mime_type(source: str) -> str:
    guessed, _ = mimetypes.guess_type(source)
    if guessed and guessed.startswith("image/"):
        return guessed
    extension = urlsplit(source).path.rsplit(".", 1)[-1].lower() if "." in urlsplit(source).path else ""
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "svg": "image/svg+xml",
    }.get(extension, "image/png")


async def _resolve_reference_image_input(reference_image_sources: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    sources = _normalize_reference_image_sources(reference_image_sources)
    if not sources:
        return None

    primary_source = sources[0]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(primary_source)
            response.raise_for_status()
            mime_type = (response.headers.get("content-type") or "").split(";", 1)[0].strip()
            if not mime_type.startswith("image/"):
                mime_type = _guess_image_mime_type(primary_source)
            return {
                "bytes": response.content,
                "source": primary_source,
                "mime_type": mime_type or _guess_image_mime_type(primary_source),
                "count": len(sources),
            }
    except Exception as exc:
        logger.warning("下载参考图片失败 {}: {}", primary_source, exc)
        return None


def _strengthen_prompt_with_reference_image(prompt_text: str, reference_count: int) -> str:
    base_prompt = str(prompt_text or "").strip()
    reference_instruction = (
        "请严格参考上传图片的主体、构图、版式、关键文字、颜色关系与核心视觉元素进行生成；"
        "除非用户明确要求改动，否则不要偏离原图语义与画面结构。"
    )
    if reference_count > 1:
        reference_instruction = (
            "请严格参考上传图片，优先保持主参考图的主体、构图、版式、关键文字、颜色关系与核心视觉元素；"
            "同时吸收其余参考图的重要信息，除非用户明确要求改动，否则不要偏离原图语义与画面结构。"
        )
    if reference_instruction in base_prompt:
        return base_prompt
    if not base_prompt:
        return reference_instruction
    return f"{base_prompt}\n\n{reference_instruction}"


def _is_gemini_native_image_model(model_name: Optional[str]) -> bool:
    """判断模型是否属于 Gemini 系列原生图像模型（支持 inline_data 参照图）。

    匹配 gemini-*-image-*、gemini-*-flash-image 等，不包括 imagen 系列。
    """
    if not model_name:
        return False
    lowered = model_name.lower()
    return "gemini" in lowered and "imagen" not in lowered


def _build_generation_extra_params(
    image_params: Optional[ImageParamsInput],
    reference_image_input: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    extra_params = dict(image_params.extra_params or {}) if image_params else {}
    if not reference_image_input or extra_params.get("image") is not None:
        return extra_params

    extra_params["image"] = reference_image_input["bytes"]
    extra_params["reference_image_url"] = reference_image_input.get("source")
    extra_params["reference_image_mime_type"] = reference_image_input.get("mime_type")
    extra_params["reference_image_count"] = reference_image_input.get("count", 1)
    return extra_params

def get_task_manager(request: Request) -> TaskManager:
    """获取任务管理器（依赖注入）"""
    return request.app.state.task_manager


async def create_user_request(db_manager, request: ChatRequest, http_request: Request, user_id: str = "anonymous") -> str:
    """
    创建用户请求记录并返回请求ID

    Args:
        db_manager: 数据库管理器
        request: 聊天请求
        http_request: HTTP请求对象

    Returns:
        str: 用户请求ID
    """
    try:
        # 获取客户端信息
        client_host = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "")

        # 创建用户请求记录
        user_request = await db_manager.create_user_request(
            user_id=user_id,
            user_ip=client_host,
            user_agent=user_agent,
            request_type="chat",
            request_data={
                "session_id": request.session_id,
                "messages_count": len(request.messages),
                "has_files": bool(request.files)
            },
            status="processing"
        )

        return user_request.id

    except Exception as e:
        logger.error(f"创建用户请求记录失败: {str(e)}")
        # 如果创建失败，返回一个UUID作为fallback
        return str(uuid.uuid4())


# ==================== 聊天接口 ====================

# 请求去重缓存: {request_hash: (timestamp, response)}
_request_dedup_cache: dict = {}
_DEDUP_WINDOW_SECONDS = 5  # 5秒内相同请求视为重复


def _get_request_hash(user_id: str, messages: list, model: str = None) -> str:
    """计算请求指纹"""
    key_parts = [user_id, model or ""]
    for m in messages[-2:]:  # 只取最后2条消息计算哈希
        content = m.content if hasattr(m, 'content') else str(m)
        key_parts.append(f"{getattr(m, 'role', '')}:{content[:200]}")
    return hashlib.md5("|".join(key_parts).encode()).hexdigest()


def _cleanup_dedup_cache():
    """清理过期缓存"""
    now = time.time()
    expired = [k for k, (ts, _) in _request_dedup_cache.items() if now - ts > 30]
    for k in expired:
        _request_dedup_cache.pop(k, None)


@router.post("/assistant/chat")
async def assistant_chat(
    request: ChatRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    统一AI助手聊天接口
    """

    try:
        # 请求去重检查
        user_id_for_dedup = current_user.get("id", "")
        req_hash = _get_request_hash(user_id_for_dedup, request.messages, request.model)
        now = time.time()
        _cleanup_dedup_cache()

        cached = _request_dedup_cache.get(req_hash)
        if cached and (now - cached[0]) < _DEDUP_WINDOW_SECONDS:
            logger.warning(f"[去重] 检测到重复请求，直接返回缓存响应 (hash={req_hash[:8]})")
            return cached[1]
        # API Key 可选，如果未提供则使用管理员统一配置
        api_key = _extract_api_key(http_request)
        db_manager = get_db_manager()
        user_id = current_user["id"]

        effective_request_messages = (
            _prepare_image_request_messages(request.messages)
            if (request.model_type == "image" or request.image_params is not None)
            else request.messages
        )

        user_messages = [m for m in effective_request_messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="至少需要一条用户消息")

        last_message = user_messages[-1]
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        original_user_text = _extract_message_text(last_message.content)
        requested_count = request.image_params.n if request.image_params and request.image_params.n else None

        user_request_id = await create_user_request(db_manager, request, http_request, user_id=user_id)
        logger.info(f"创建用户请求: {user_request_id}")

        execution_plan = await plan_assistant_execution(
            messages=_request_messages_to_payloads(effective_request_messages),
            files=request.files,
            user_instruction=original_user_text,
            request_model=request.model,
            request_model_type=request.model_type,
            requested_count=requested_count,
            db_manager=db_manager,
            app_state=http_request.app.state,
            api_key=api_key,
        )
        execution_plan_metadata = dict(execution_plan.metadata or {})
        planned_batch_prompts = execution_plan_metadata.pop("_batch_prompts", None)
        reference_image_sources = _normalize_reference_image_sources(
            execution_plan_metadata.pop("reference_image_sources", None)
        )
        route_metadata: Dict[str, Any] = {
            **execution_plan_metadata,
            "planned_mode": execution_plan.mode,
            "planned_intent_type": execution_plan.intent_type,
            "planned_effective_model": execution_plan.effective_model,
            "route_source": execution_plan.source,
            "route_reasoning": execution_plan.reasoning,
            "route_confidence": execution_plan.confidence,
        }
        logger.info(
            "Assistant execution plan selected: mode={}, intent={}, source={}, confidence={}",
            execution_plan.mode,
            execution_plan.intent_type,
            execution_plan.source,
            execution_plan.confidence,
        )

        intent: Optional[Intent] = None
        response = None
        billing_info: Optional[Dict[str, Any]] = None

        # 对 image 路由进行积分冻结
        if execution_plan.mode != "chat":
            account_service = get_account_service()
            image_model = (
                execution_plan.effective_model
                or request.model
                or (request.image_params.model_name if request.image_params else None)
                or "default"
            )
            # 计算需要冻结的图片数量
            if execution_plan.intent_type == "batch_generate" or execution_plan.batch_count > 1:
                freeze_count = execution_plan.batch_count
                if planned_batch_prompts:
                    freeze_count = len(planned_batch_prompts)
            else:
                freeze_count = 1

            freeze_result = await account_service.freeze_points(
                user_id=user_id,
                model_name=image_model,
                count=freeze_count,
                request_id=user_request_id,
            )

            if freeze_result["status"] == "insufficient":
                # 积分不足，直接返回
                return ChatResponse(
                    message=ChatMessage(
                        role="assistant",
                        content=f"积分不足，无法生成图片。{freeze_result['description']}",
                    ),
                    intent=Intent(
                        type=execution_plan.intent_type or "single_generate",
                        confidence=execution_plan.confidence,
                        parameters={},
                        reasoning="积分不足",
                    ),
                    requires_action=False,
                    metadata={
                        **route_metadata,
                        "billing": freeze_result,
                    },
                )

            billing_info = freeze_result
            route_metadata["billing"] = billing_info

        if execution_plan.mode == "chat":
            planned_messages = _plan_messages_to_chat_messages(
                execution_plan.messages or _request_messages_to_payloads(effective_request_messages)
            )
            planned_user_messages = [message for message in planned_messages if message.role == "user"]
            planned_last_message = planned_user_messages[-1] if planned_user_messages else last_message
            effective_chat_model = execution_plan.effective_model or _default_chat_execution_model()
            intent = Intent(
                type="chat",
                confidence=execution_plan.confidence,
                parameters={
                    "query": original_user_text,
                    "attachment_route": route_metadata.get("attachment_route", "none"),
                    "planning_basis": route_metadata.get("planning_basis", "text"),
                },
                reasoning=execution_plan.reasoning,
            )

            if request.stream:
                try:
                    await db_manager.update_user_request_status(
                        user_request_id=user_request_id,
                        status="completed",
                        metadata={
                            "intent_type": intent.type,
                            "response_status": "streaming",
                            **route_metadata,
                            "effective_model": effective_chat_model,
                        },
                    )
                except Exception as e:
                    logger.error(f"更新用户请求状态失败: {str(e)}")
                return await handle_chat_stream(effective_chat_model, planned_messages, api_key)

            response = await handle_chat_query(
                planned_last_message,
                planned_messages,
                effective_chat_model,
                api_key,
            )
        else:
            # Use original Chinese prompt for records, translated prompt for actual generation
            generation_prompt = execution_plan.prompt or original_user_text
            display_prompt = route_metadata.get("original_prompt") or original_user_text
            logger.info(
                "Image generation prompt prepared: chars={}, attachment_count={}, attachment_text_count={}, preview={}",
                len(generation_prompt or ""),
                route_metadata.get("attachment_count", 0),
                route_metadata.get("attachment_text_count", 0),
                (generation_prompt or "")[:400],
            )
            generation_message = ChatMessage(role="user", content=generation_prompt)
            image_model = (
                execution_plan.effective_model
                or request.model
                or (request.image_params.model_name if request.image_params else None)
            )

            if execution_plan.intent_type == "batch_generate" or execution_plan.batch_count > 1:
                intent = Intent(
                    type="batch_generate",
                    confidence=execution_plan.confidence,
                    parameters={
                        "count": execution_plan.batch_count,
                        "original_prompt": display_prompt,
                    },
                    reasoning=execution_plan.reasoning,
                )
                response = await handle_batch_generate(
                    generation_message,
                    intent,
                    task_manager,
                    user_request_id,
                    session_id,
                    request.image_params,
                    image_model,
                    api_key,
                    precomputed_prompts=planned_batch_prompts,
                    user_id=user_id,
                    freeze_id=billing_info["freeze_id"] if billing_info else None,
                    reference_image_sources=reference_image_sources,
                )
            else:
                intent = Intent(
                    type="single_generate",
                    confidence=execution_plan.confidence,
                    parameters={"prompt": generation_prompt, "display_prompt": display_prompt},
                    reasoning=execution_plan.reasoning,
                )
                response = await handle_single_generate(
                    generation_message,
                    intent,
                    task_manager,
                    user_request_id,
                    session_id,
                    request.image_params,
                    image_model,
                    api_key,
                    user_id=user_id,
                    freeze_id=billing_info["freeze_id"] if billing_info else None,
                    reference_image_sources=reference_image_sources,
                )

        if response and route_metadata:
            actual_model = (
                response.message.metadata.get("model")
                if response.message and response.message.metadata
                else None
            )
            if actual_model:
                route_metadata["effective_model"] = actual_model
            response.metadata = {
                **route_metadata,
                **(response.metadata or {}),
            }

        if (
            execution_plan.mode != "chat"
            and billing_info
            and response
            and not response.task_id
            and not response.batch_id
            and (response.metadata or {}).get("status") == "error"
        ):
            refunded_billing = await _refund_frozen_billing_if_needed(
                user_id=user_id,
                billing_info=billing_info,
                model_name=(
                    execution_plan.effective_model
                    or request.model
                    or (request.image_params.model_name if request.image_params else None)
                ),
                request_id=user_request_id,
                error_reason=(response.metadata or {}).get("error") or response.message.content or "任务创建失败",
                provider=(request.image_params.provider if request.image_params else "unknown") or "unknown",
            )
            response.metadata = {
                **(response.metadata or {}),
                "billing": refunded_billing,
            }
            route_metadata["billing"] = refunded_billing

        if response and intent and intent.type == "chat" and response.message:
            await save_assistant_response(
                db_manager,
                session_id,
                response.message,
                user_request_id,
            )

        try:
            await db_manager.update_user_request_status(
                user_request_id=user_request_id,
                status="completed",
                metadata={
                    "intent_type": intent.type if intent else "unknown",
                    "response_status": "success",
                    **route_metadata,
                    "effective_model": route_metadata.get("effective_model") or execution_plan.effective_model or request.model,
                }
            )
        except Exception as e:
            logger.error(f"更新用户请求状态失败: {str(e)}")

        # 缓存响应用于去重
        _request_dedup_cache[req_hash] = (time.time(), response)
        return response

    except Exception as e:
        logger.error("聊天接口错误: {}", e)

        if 'billing_info' in locals() and execution_plan.mode != "chat":
            response_obj = locals().get("response")
            task_already_created = bool(response_obj and (response_obj.task_id or response_obj.batch_id))
            if not task_already_created:
                await _refund_frozen_billing_if_needed(
                    user_id=locals().get("user_id"),
                    billing_info=billing_info,
                    model_name=(
                        execution_plan.effective_model
                        or request.model
                        or (request.image_params.model_name if request.image_params else None)
                    ),
                    request_id=locals().get("user_request_id", ""),
                    error_reason=str(e),
                    provider=(request.image_params.provider if request.image_params else "unknown") or "unknown",
                )

        # 如果创建了用户请求，更新其状态为失败
        if 'user_request_id' in locals():
            try:
                await db_manager.update_user_request_status(
                    user_request_id=user_request_id,
                    status="failed",
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error(f"更新用户请求失败状态失败: {db_error}")

        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


async def handle_single_generate(message: ChatMessage, intent: Intent, task_manager: TaskManager, user_request_id: str = "", session_id: str = "", image_params: Optional[ImageParamsInput] = None, request_model: Optional[str] = None, api_key: str = None, user_id: str = None, freeze_id: str = None, reference_image_sources: Optional[List[str]] = None) -> ChatResponse:
    """处理单图生成意图"""

    try:
        ip = image_params or ImageParamsInput()
        prompt_text = intent.parameters.get("prompt", message.content)
        reference_image_input = await _resolve_reference_image_input(reference_image_sources)
        if reference_image_input and not _is_gemini_native_image_model(request_model):
            prompt_text = _strengthen_prompt_with_reference_image(
                prompt_text,
                int(reference_image_input.get("count") or 1),
            )

        # 确定尺寸：用户明确选择的尺寸（非0）优先，否则用 LLM 从提示词中分析
        if ip.width and ip.height:
            # 用户已选择具体尺寸，直接使用
            width = ip.width
            height = ip.height
            quality = ip.quality or "standard"
            logger.info(f"使用用户指定尺寸: width={width}, height={height}, quality={quality}")
        else:
            # auto模式：尝试用 LLM 分析提示词提取尺寸
            try:
                client = await _get_openai_client(api_key)
                analysis_prompt = f"""分析以下图像生成提示词，提取尺寸和质量参数。

提示词: {prompt_text}

请以JSON格式返回：
{{
  "width": 宽度像素值(整数),
  "height": 高度像素值(整数),
  "quality": "standard"或"hd"
}}

规则：
- 2k对应2048像素，4k对应4096像素
- 3:2比例表示宽高比为3:2
- 16:9比例表示宽高比为16:9
- "2k 3:2"表示在2k(2048)基础上按3:2比例计算，结果约为2048x1365
- "4k 16:9"表示在4k(4096)基础上按16:9比例计算
- 如果提到高清/超清/HD/4K/2K，quality设为"hd"
- 如果没有明确尺寸，返回0表示让模型自动决定"""

                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    response_format={"type": "json_object"}
                )

                import json
                params = json.loads(response.choices[0].message.content)
                width = params.get("width") or 0
                height = params.get("height") or 0
                quality = params.get("quality", ip.quality or "standard")
                logger.info(f"LLM分析提示词: width={width}, height={height}, quality={quality}")
            except Exception as e:
                logger.warning("LLM分析失败，使用auto模式: {}", e)
                width = 0
                height = 0
                quality = ip.quality or "standard"

        # 优先用外层 request.model，其次用 image_params.model_name
        model_name = request_model or ip.model_name

        # 解析 provider：优先用前端指定的 provider，其次用 registry，最后用 fallback
        provider_name = ip.provider
        if not provider_name and model_name:
            try:
                from ...config.model_registry import get_model_registry
                registry = await get_model_registry()
                mapping = registry.get_provider_mapping(model_name)
                if mapping:
                    provider_name = mapping.provider_type
                    logger.info(f"模型 {model_name} 从 registry 映射到 Provider: {provider_name}")
            except Exception:
                pass
        if not provider_name and model_name:
            from .unified import _fallback_provider_mapping
            provider_name = _fallback_provider_mapping(model_name)
        if not provider_name:
            provider_name = settings.default_image_provider

        extra_params = _build_generation_extra_params(ip, reference_image_input)

        params = ImageParams(
            prompt=prompt_text,
            model=model_name,
            width=width,
            height=height,
            quality=quality,
            n=ip.n or 1,
            negative_prompt=ip.negative_prompt,
            seed=ip.seed,
            provider=provider_name,
            api_key=api_key,
            extra_params=extra_params
        )

        # 检查是否是异步模型
        from ...config.model_registry import get_model_registry
        model_registry = await get_model_registry()
        is_async_model = False
        if model_registry and model_name:
            model_info = model_registry.get_model_info(model_name)
            if model_info and model_info.tags:
                tags = [t.strip() for t in model_info.tags.split(",") if t.strip()]
                is_async_model = "异步" in tags

        # 如果是异步模型，提交到异步任务数据库
        if is_async_model:
            from ...database.async_task_manager import get_async_task_manager
            async_manager = get_async_task_manager()
            db_manager = get_db_manager()
            credential_id = None
            if api_key:
                credential = await db_manager.store_api_credential(
                    api_key=api_key,
                    provider="relay",
                    user_id="assistant",
                    session_id=session_id or None,
                )
                credential_id = credential.id

            task = await async_manager.create_task(
                platform=model_name.split("/")[0] if "/" in model_name else "relay",
                model=model_name,
                prompt=params.prompt,
                params={
                    "width": params.width,
                    "height": params.height,
                    "quality": params.quality,
                    "n": params.n,
                    "credential_id": credential_id,
                }
            )

            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content="异步任务已提交，请在'异步任务'页面查看进度",
                    metadata={"task_id": task.id}
                ),
                intent=intent,
                task_id=task.id,
                requires_action=False,
                metadata={"status": "async", "is_async": True}
            )

        # 同步模型：创建生成任务，传入用户请求ID和会话ID
        session_id = session_id or f"session_{datetime.now().timestamp()}"
        display_prompt_for_record = intent.parameters.get("display_prompt") or intent.parameters.get("prompt", prompt_text)
        task = task_manager.create_task(
            params=params,
            user_input=display_prompt_for_record,
            user_request_id=user_request_id,
            metadata={
                "session_id": session_id,
                "user_request_id": user_request_id,
                "user_id": user_id,
                "freeze_id": freeze_id,
            }
        )
        task.user_id = user_id
        await task_manager.submit_task(task)

        # 保存任务信息到数据库
        db_manager = get_db_manager()
        # Save original Chinese prompt for display, not the translated English one
        display_prompt = intent.parameters.get("display_prompt") or intent.parameters.get("prompt", params.prompt)
        await db_manager.create_user_request(
            user_id=user_id or "anonymous",
            request_type="image_generation",
            request_data={
                "task_id": task.task_id,
                "prompt": display_prompt,
                "provider": params.provider
            },
            status="processing",
            metadata={"original_task_id": user_request_id}
        )

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=f"正在为您生成图像...（任务ID: {task.task_id}）",
                metadata={"task_id": task.task_id}
            ),
            intent=intent,
            task_id=task.task_id,
            requires_action=True,  # 前端需要轮询任务状态
            metadata={"status": "processing"}
        )

    except Exception as e:
        logger.error("单图生成失败: {}", e)
        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=f"生成图像时出错: {str(e)}"
            ),
            intent=intent,
            metadata={"status": "error", "error": str(e)}
        )


async def handle_batch_generate(message: ChatMessage, intent: Intent, task_manager: TaskManager, user_request_id: str = "", session_id: str = "", image_params: Optional[ImageParamsInput] = None, request_model: Optional[str] = None, api_key: str = None, precomputed_prompts: Optional[List[str]] = None, user_id: str = None, freeze_id: str = None, reference_image_sources: Optional[List[str]] = None) -> ChatResponse:
    """处理批量生成意图"""

    try:
        ip = image_params or ImageParamsInput()
        reference_image_input = await _resolve_reference_image_input(reference_image_sources)

        # 优先用外层 request.model，其次用 image_params.model_name
        model_name = request_model or ip.model_name

        # 解析 provider
        provider_name = ip.provider
        if not provider_name and model_name:
            try:
                from ...config.model_registry import get_model_registry
                registry = await get_model_registry()
                mapping = registry.get_provider_mapping(model_name)
                if mapping:
                    provider_name = mapping.provider_type
                    logger.info(f"模型 {model_name} 从 registry 映射到 Provider: {provider_name}")
            except Exception:
                pass
        if not provider_name and model_name:
            from .unified import _fallback_provider_mapping
            provider_name = _fallback_provider_mapping(model_name)
        if not provider_name:
            provider_name = settings.default_image_provider

        explicit_prompts = [
            str(prompt).strip()
            for prompt in (precomputed_prompts or [])
            if str(prompt).strip()
        ]

        if explicit_prompts:
            prompts = explicit_prompts
            count = len(prompts)
            original_prompt = intent.parameters.get("original_prompt", prompts[0])
            logger.info("使用预构建批量提示词，数量: {}", count)
        else:
            # 优先使用前端传来的 n 参数，其次用意图识别的 count
            count = ip.n or intent.parameters.get("count", 4)
            original_prompt = intent.parameters.get("original_prompt", message.content)

            # 生成多个不同的提示词
            prompts = await generate_batch_prompts(original_prompt, count)

        if reference_image_input and not _is_gemini_native_image_model(model_name):
            prompts = [
                _strengthen_prompt_with_reference_image(
                    prompt,
                    int(reference_image_input.get("count") or 1),
                )
                for prompt in prompts
            ]

        base_extra_params = _build_generation_extra_params(ip, reference_image_input)

        # 创建批量任务
        params_list = []
        for prompt in prompts:
            params = ImageParams(
                prompt=prompt,
                model=model_name,
                width=ip.width if ip.width else 0,
                height=ip.height if ip.height else 0,
                quality=ip.quality or "standard",
                n=1,
                negative_prompt=ip.negative_prompt,
                seed=ip.seed,
                provider=provider_name,
                api_key=api_key,
                extra_params=dict(base_extra_params)
            )
            params_list.append(params)

        # 创建批量任务，传入用户请求ID和会话ID
        session_id = session_id or f"session_{datetime.now().timestamp()}"
        batch_task = await task_manager.create_batch_task(
            params_list=params_list,
            user_inputs=prompts,
            user_request_id=user_request_id,
            metadata={
                "session_id": session_id,
                "user_request_id": user_request_id,
                "user_id": user_id,
                "freeze_id": freeze_id,
            }
        )

        # 保存批量任务信息到数据库
        db_manager = get_db_manager()
        await db_manager.create_user_request(
            user_id=user_id or "anonymous",
            request_type="batch_image_generation",
            request_data={
                "batch_id": batch_task.batch_id,
                "count": count,
                "original_prompt": original_prompt,
                "prompts": prompts
            },
            status="processing",
            metadata={"original_task_id": user_request_id}
        )

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=f"已创建 {count} 个生图任务，正在排队处理...（批次ID: {batch_task.batch_id}）",
                metadata={
                    "batch_id": batch_task.batch_id,
                    "total_count": count,
                    "stage": batch_task.stage.value,
                    "stage_label": batch_task.stage_label,
                    "stage_message": batch_task.stage_message,
                }
            ),
            intent=intent,
            batch_id=batch_task.batch_id,
            requires_action=True,
            metadata={
                "status": "processing",
                "total_count": count,
                "stage": batch_task.stage.value,
                "stage_label": batch_task.stage_label,
                "stage_message": batch_task.stage_message,
                "status_detail": batch_task.status_detail.model_dump(),
            }
        )

    except Exception as e:
        logger.error("批量生成失败: {}", e)
        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=f"批量生成时出错: {str(e)}"
            ),
            intent=intent,
            metadata={"status": "error", "error": str(e)}
        )


def _default_chat_execution_model() -> str:
    return settings.assistant_text_model or settings.langchain_pdf_prompt_model or settings.openai_model or "gpt-4o-mini"


def _should_retry_chat_with_safe_model(error: Exception) -> bool:
    text = str(error).lower()
    retry_markers = (
        "max_completion_tokens",
        "integer_below_min_value",
        "unsupported",
        "not support",
        "invalid_request_error",
        "model_not_found",
    )
    return any(marker in text for marker in retry_markers)


def _should_retry_chat_invalid_token(error: Exception) -> bool:
    raw_text = str(error)
    lowered = raw_text.lower()
    if "401" not in lowered:
        return False
    retry_markers = (
        "无效的令牌",
        "invalid token",
        "new_api_error",
        "unauthorized",
        "authentication",
    )
    return any(marker in raw_text or marker in lowered for marker in retry_markers)


async def _run_chat_completion(client, messages: List[Dict[str, Any]], model: str):
    safe_model = _default_chat_execution_model()
    attempts: List[tuple[str, Optional[int]]] = [(model, 2000)]
    if safe_model and safe_model != model:
        attempts.append((safe_model, None))

    # 打印 client 的 base_url 和 api_key（脱敏）
    client_base_url = getattr(client, 'base_url', 'unknown')
    client_api_key = getattr(client, 'api_key', '')
    masked_key = f"{client_api_key[:4]}...{client_api_key[-4:]}" if client_api_key and len(client_api_key) > 8 else "***"
    logger.info(f"_run_chat_completion client: base_url={client_base_url}, api_key={masked_key}")

    last_error: Optional[Exception] = None
    for index, (attempt_model, attempt_max_tokens) in enumerate(attempts):
        request_kwargs: Dict[str, Any] = {
            "model": attempt_model,
            "messages": messages,
            "stream": False,
        }
        if attempt_max_tokens is not None:
            request_kwargs["max_tokens"] = attempt_max_tokens

        same_model_retry_limit = 2
        for retry_index in range(same_model_retry_limit + 1):
            try:
                logger.info(
                    "非流式对话: model={}, messages={}条, request_attempt={}",
                    attempt_model,
                    len(messages),
                    retry_index + 1,
                )
                raw = await client.chat.completions.create(**request_kwargs)
                if isinstance(raw, str):
                    logger.error("LLM API 返回字符串而非对象: {}", raw[:200])
                    if index < len(attempts) - 1:
                        logger.warning(
                            "Chat completion returned non-object for model={}, retrying with {}",
                            attempt_model,
                            attempts[index + 1][0],
                        )
                        break
                    return raw, attempt_model
                else:
                    return raw, attempt_model
            except Exception as exc:
                last_error = exc
                if retry_index < same_model_retry_limit and _should_retry_chat_invalid_token(exc):
                    logger.warning(
                        "Chat completion got retryable 401 token error for model={}, retry {}/{}: {}",
                        attempt_model,
                        retry_index + 1,
                        same_model_retry_limit,
                        exc,
                    )
                    await asyncio.sleep(0.2)
                    continue
                if index < len(attempts) - 1 and _should_retry_chat_with_safe_model(exc):
                    logger.warning(
                        "Chat completion failed for model={}, retrying with {}: {}",
                        attempt_model,
                        attempts[index + 1][0],
                        exc,
                    )
                    break
                raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("Chat completion did not produce a result.")


async def _run_chat_completion_stream(client, messages: List[Dict[str, Any]], model: str):
    safe_model = _default_chat_execution_model()
    attempts: List[str] = [model]
    if safe_model and safe_model != model:
        attempts.append(safe_model)

    last_error: Optional[Exception] = None
    for index, attempt_model in enumerate(attempts):
        same_model_retry_limit = 2
        for retry_index in range(same_model_retry_limit + 1):
            try:
                logger.info(
                    "流式对话: model={}, messages={}条, request_attempt={}",
                    attempt_model,
                    len(messages),
                    retry_index + 1,
                )
                stream = await client.chat.completions.create(
                    model=attempt_model,
                    messages=messages,
                    stream=True,
                )
                return stream, attempt_model
            except Exception as exc:
                last_error = exc
                if retry_index < same_model_retry_limit and _should_retry_chat_invalid_token(exc):
                    logger.warning(
                        "Chat stream got retryable 401 token error for model={}, retry {}/{}: {}",
                        attempt_model,
                        retry_index + 1,
                        same_model_retry_limit,
                        exc,
                    )
                    await asyncio.sleep(0.2)
                    continue
                if index < len(attempts) - 1 and _should_retry_chat_with_safe_model(exc):
                    logger.warning(
                        "Chat stream failed for model={}, retrying with {}: {}",
                        attempt_model,
                        attempts[index + 1],
                        exc,
                    )
                    break
                raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("Chat completion stream did not produce a result.")


async def handle_chat_query(message: ChatMessage, history: List[ChatMessage], model: str = None, api_key: str = None) -> ChatResponse:
    """处理普通对话查询 - 调用 LLM 生成回复"""

    if not model:
        # 没有指定模型，返回预设响应
        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content="我是AI图像助手，可以帮您生成各种图像。您可以说：\n• \"生成一只可爱的猫\"（单图）\n• \"批量生成3张不同风格的风景\"（批量）\n• \"创建4张赛博朋克风格的城市\"（批量）"
            ),
            intent=Intent(type="chat", confidence=1.0, parameters={})
        )

    try:
        from .chat import _get_openai_client

        client = await _get_openai_client(api_key)
        effective_model = model or _default_chat_execution_model()
        messages = []
        for m in history:
            if m.content and str(m.content).strip():
                messages.append({"role": m.role, "content": m.content})

        if not messages:
            return ChatResponse(
                message=ChatMessage(role="assistant", content="消息列表为空，无法对话。"),
                intent=Intent(type="chat", confidence=1.0, parameters={})
            )

        raw, used_model = await _run_chat_completion(client, messages, effective_model)

        if isinstance(raw, str):
            content = "抱歉，对话请求失败，请稍后重试。"
        else:
            content = raw.choices[0].message.content if raw.choices else "抱歉，未能生成回复。"

        # 检查content是否包含图片URL的JSON数组
        images = None
        if content and content.strip().startswith('[') and content.strip().endswith(']'):
            try:
                import json
                parsed = json.loads(content)
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict) and 'url' in parsed[0]:
                    # 提取URL字符串列表
                    images = [url_obj.get('url') for url_obj in parsed if 'url' in url_obj]
                    content = "图像生成完成！"
            except:
                pass

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=content,
                images=images,
                metadata={"model": used_model},
            ),
            intent=Intent(type="chat", confidence=1.0, parameters={})
        )

    except Exception as e:
        logger.error("LLM 对话失败: {}", e)
        return ChatResponse(
            message=ChatMessage(role="assistant", content=f"对话请求失败: {str(e)}"),
            intent=Intent(type="chat", confidence=1.0, parameters={})
        )


async def handle_chat_stream(model: str, history: List[ChatMessage], api_key: str = None):
    """流式 LLM 对话，返回 SSE StreamingResponse"""

    async def event_generator():
        try:
            client = await _get_openai_client(api_key)
            effective_model = model or _default_chat_execution_model()
            messages = [{"role": m.role, "content": m.content} for m in history if m.content and str(m.content).strip()]

            if not messages:
                yield f"data: {json.dumps({'error': '消息列表为空'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            stream, used_model = await _run_chat_completion_stream(client, messages, effective_model)
            logger.info("流式对话输出使用模型: {}", used_model)

            collected_content = ""
            async for chunk in stream:
                delta_content = ""

                if hasattr(chunk, "choices") and chunk.choices:
                    delta = getattr(chunk.choices[0], "delta", None)
                    raw_delta = getattr(delta, "content", "") if delta else ""

                    if isinstance(raw_delta, str):
                        delta_content = raw_delta
                    elif isinstance(raw_delta, list):
                        delta_content = "".join(
                            str(item.get("text", ""))
                            for item in raw_delta
                            if isinstance(item, dict) and item.get("text")
                        )

                if not delta_content:
                    continue

                collected_content += delta_content
                data = json.dumps({"content": delta_content}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            logger.info(f"对话完成: {len(collected_content)} 字符")
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("流式对话失败: {e}", e=str(e), exc_info=True)
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def generate_batch_prompts(original_prompt: str, count: int) -> List[str]:
    """
    根据原始提示词生成多个不同的提示词

    Args:
        original_prompt: 原始提示词
        count: 需要生成的数量

    Returns:
        提示词列表
    """

    prompts = []

    # 生成不同风格的变体
    styles = ["写实风格", "艺术风格", "简约风格", "创意风格", "卡通风格", "油画风格"]

    for i in range(count):
        style = styles[i % len(styles)]
        prompts.append(f"{original_prompt}，{style}")

    return prompts


async def save_conversation_history(request: ChatRequest, http_request: Request, user_request_id: str = ""):
    """
    保存对话历史到数据库

    Args:
        request: 聊天请求
        http_request: HTTP请求对象
        user_request_id: 用户请求ID
    """
    try:
        db_manager = get_db_manager()
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"

        # 如果是新会话，创建会话记录
        try:
            await db_manager.create_conversation_session(
                session_id=session_id,
                title=f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                model="unknown",
                provider="assistant"
            )
        except Exception as e:
            logger.warning(f"创建会话记录可能已存在: {str(e)}")

        # 为每条消息创建记录
        for message in request.messages:
            try:
                # 使用消息的模型信息
                model = message.metadata.get("model") if message.metadata else None
                provider = message.metadata.get("provider") if message.metadata else None

                await db_manager.create_chat_conversation(
                    user_request_id=user_request_id,
                    session_id=session_id,
                    role=message.role,
                    content=message.content,
                    model=model or "unknown",
                    provider=provider or "unknown"
                )
            except Exception as e:
                logger.warning(f"保存对话消息失败: {str(e)}")

        logger.info(f"保存了 {len(request.messages)} 条对话记录，会话ID: {session_id}, 用户请求ID: {user_request_id}")

    except Exception as e:
        logger.error(f"保存对话历史失败: {str(e)}")
        # 保存失败不影响主要功能，只记录错误


async def save_assistant_response(db_manager, session_id: str, message: ChatMessage, user_request_id: str):
    """
    保存AI回复到数据库（仅后端非流式场景使用）

    Args:
        db_manager: 数据库管理器
        session_id: 会话ID
        message: AI回复消息
        user_request_id: 用户请求ID
    """
    try:
        # 保存AI回复
        await db_manager.create_chat_message(
            session_id=session_id,
            role=message.role,
            content=message.content,
            model=message.metadata.get("model") if message.metadata else "unknown",
            provider=message.metadata.get("provider") if message.metadata else "unknown",
            user_request_id=user_request_id
        )

        logger.info(f"保存AI回复到会话: {session_id}")

    except Exception as e:
        logger.error(f"保存AI回复失败: {str(e)}")


@router.post("/assistant/upload")
async def upload_file(
    file: UploadFile = File(...),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    文件上传接口

    支持: PDF, Word, Excel, 图片等
    用于提供参考材料或批量任务输入
    """

    try:
        # TODO: 实现文件保存和解析逻辑
        # 这里暂时返回文件ID

        file_id = f"file_{datetime.now().timestamp()}"

        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "uploaded",
            "message": "文件上传成功（TODO: 实现文件处理逻辑）"
        }

    except Exception as e:
        logger.error("文件上传失败: {}", e)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/assistant/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """查询任务状态（复用现有接口）"""

    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 使用自定义格式返回数据（包含images字段）
    return task.to_response_dict()


@router.get("/assistant/batch/{batch_id}")
async def get_batch_task_status(
    batch_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """查询批量任务状态（复用现有接口），批量完成时自动结算积分"""

    batch_task = task_manager.get_batch_task(batch_id)
    if not batch_task:
        raise HTTPException(status_code=404, detail="批量任务不存在")

    # 批量任务完成时，自动结算冻结积分
    response_data = batch_task.to_response_dict()
    if batch_task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        first_task = batch_task.tasks[0] if batch_task.tasks else None
        freeze_id = first_task.metadata.get("freeze_id") if first_task else None
        user_id = first_task.metadata.get("user_id") if first_task else None
        already_settled = first_task.metadata.get("batch_billing_settled") if first_task else False

        if freeze_id and user_id and not already_settled:
            try:
                account_service = get_account_service()
                completed_count = batch_task.completed
                failed_count = batch_task.failed
                total_count = batch_task.total

                # 收集成功任务的图片URL
                all_image_urls = []
                for t in batch_task.tasks:
                    if t.status == TaskStatus.COMPLETED and t.result:
                        all_image_urls.extend([img.url for img in t.result if img.url])

                if completed_count > 0 and completed_count == total_count:
                    # 全部成功：正常结算
                    billing_result = await account_service.settle_frozen_points(
                        user_id=user_id,
                        freeze_id=freeze_id,
                        success=True,
                        model_name=first_task.params.model or "unknown",
                        provider=first_task.params.provider or "unknown",
                        request_id=batch_id,
                        prompt="batch_generate",
                        image_count=completed_count,
                        image_urls=all_image_urls,
                    )
                elif completed_count == 0:
                    # 全部失败：全额退还
                    billing_result = await account_service.settle_frozen_points(
                        user_id=user_id,
                        freeze_id=freeze_id,
                        success=False,
                        model_name=first_task.params.model or "unknown",
                        provider=first_task.params.provider or "unknown",
                        request_id=batch_id,
                        prompt="batch_generate",
                        error_reason=f"批量任务全部失败（{failed_count}/{total_count}）",
                    )
                else:
                    # 部分成功：先结算成功部分，再退还失败部分的差额
                    billing_result = await account_service.settle_frozen_points(
                        user_id=user_id,
                        freeze_id=freeze_id,
                        success=True,
                        model_name=first_task.params.model or "unknown",
                        provider=first_task.params.provider or "unknown",
                        request_id=batch_id,
                        prompt="batch_generate",
                        image_count=completed_count,
                        image_urls=all_image_urls,
                    )
                    # 退还失败部分的积分
                    if failed_count > 0:
                        model_price = await account_service.get_model_price(first_task.params.model or "default")
                        refund_points = model_price["points"] * failed_count
                        account = await account_service.get_or_create_account(user_id)
                        refund_cost_type = billing_result.get("cost_type")
                        if refund_cost_type == "gift_points":
                            account.gift_points = (account.gift_points or 0) + refund_points
                        else:
                            account.points += refund_points
                        await account_service.db_manager.update_account(account)
                        await account_service.db_manager.add_transaction(
                            user_id=user_id,
                            transaction_type="refund",
                            amount=0,
                            points_change=refund_points,
                            description=f"批量生成部分失败退还 - {failed_count}/{total_count} 张失败",
                            related_request_id=batch_id,
                            apply_account_change=False,
                            balance_after=account.balance,
                            points_after=account.points,
                        )
                        billing_result["description"] += f"，已退还 {refund_points} 积分（{failed_count} 张失败）"
                        billing_result["balance_after"]["points"] = account.points
                        billing_result["balance_after"]["gift_points"] = account.gift_points or 0

                # 标记已结算，避免重复
                for t in batch_task.tasks:
                    t.metadata["batch_billing_settled"] = True
                    t.metadata["billing_result"] = billing_result

                response_data["billing"] = billing_result
                logger.info(f"批量任务 {batch_id} 结算完成: {billing_result['status']}")
            except Exception as e:
                logger.error(f"批量任务结算失败: {str(e)}")
        elif already_settled and first_task:
            response_data["billing"] = first_task.metadata.get("billing_result")

    return response_data
