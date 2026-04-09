"""LangGraph orchestration for multimodal assistant execution."""

from __future__ import annotations

import base64
import io
import json
import re
from typing import Any, Dict, List, Optional, TypedDict
from urllib.parse import unquote, urlsplit

import pdfplumber
from docx import Document
from loguru import logger
from pydantic import BaseModel, Field

from ..config.settings import settings
from ..utils.config_helper import get_relay_config, normalize_openai_base_url
from .multimodal_attachment_graph import (
    AttachmentDescriptor,
    build_attachment_route,
    build_text_attachment_prompt,
)

try:
    import fitz
except ImportError:
    fitz = None  # type: ignore[assignment]

try:
    import httpx
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph

    LANGCHAIN_ASSISTANT_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    HumanMessage = None  # type: ignore[assignment]
    SystemMessage = None  # type: ignore[assignment]
    ChatOpenAI = None  # type: ignore[assignment]
    StateGraph = None  # type: ignore[assignment]
    START = END = None  # type: ignore[assignment]
    LANGCHAIN_ASSISTANT_AVAILABLE = False


class AssistantExecutionPlan(BaseModel):
    mode: str = Field(..., description="chat or image")
    confidence: float = Field(0.0, description="0-1 confidence")
    reasoning: str = Field("", description="Why this route was chosen")
    source: str = Field("fallback", description="Workflow source")
    effective_model: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    prompt: Optional[str] = None
    intent_type: Optional[str] = None
    batch_count: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RequestRouteDecision(BaseModel):
    route: str = Field(..., description="chat or image")
    intent_type: str = Field(..., description="chat, single_generate, or batch_generate")
    batch_count: int = Field(1, description="Requested image count when route=image")
    confidence: float = Field(0.0, description="0-1 confidence")
    reasoning: str = Field("", description="Why this route was selected")
    source: str = Field("fallback", description="Workflow source")
    planning_basis: str = Field("text", description="text or attachments")


class TextIntentDecision(BaseModel):
    route: str = Field(..., description="chat or image")
    intent_type: str = Field(..., description="chat, single_generate, or batch_generate")
    batch_count: int = Field(1, description="Requested image count when route=image")
    confidence: float = Field(0.0, description="0-1 confidence")
    reasoning: str = Field("", description="Why this route was selected")


class AssistantExecutionState(TypedDict, total=False):
    """Mutable graph state for assistant planning."""

    messages: List[Dict[str, Any]]
    files: List[str]
    user_instruction: str
    request_model: Optional[str]
    request_model_type: Optional[str]
    requested_count: Optional[int]
    db_manager: Any
    app_state: Any
    api_key: Optional[str]
    attachments: List[Dict[str, Any]]
    route_decision: Dict[str, Any]
    execution_plan: Dict[str, Any]


def _has_llm_credentials(api_key: Optional[str] = None) -> bool:
    return bool((api_key or "").strip())


def _is_placeholder_assistant_message(content: Any) -> bool:
    text = _extract_message_text(content)
    if not text:
        return True

    stripped = text.strip()
    exact_matches = {
        "图像生成完成！",
        "抱歉，对话请求失败，请稍后重试。",
        "消息列表为空，无法对话。",
    }
    prefix_matches = (
        "正在上传文件",
        "正在为您批量生成",
        "正在处理",
        "对话请求失败:",
        "抱歉，对话请求失败",
    )

    if stripped in exact_matches:
        return True
    return any(stripped.startswith(prefix) for prefix in prefix_matches)


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


def _message_role_label(role: str) -> str:
    normalized_role = (role or "").strip().lower()
    if normalized_role == "assistant":
        return "Assistant"
    if normalized_role == "system":
        return "System"
    return "User"


def _build_recent_conversation_context(
    messages: List[Dict[str, Any]],
    *,
    max_messages: int = 6,
    max_chars: int = 3200,
    include_latest_user: bool = False,
) -> str:
    normalized = _normalize_messages(messages)
    if not normalized:
        return ""

    if not include_latest_user and normalized and normalized[-1]["role"] == "user":
        normalized = normalized[:-1]
    if not normalized:
        return ""

    rendered_messages: List[str] = []
    for message in normalized[-max_messages:]:
        text = _extract_message_text(message.get("content", ""))
        if not text:
            continue
        rendered_messages.append(
            f"{_message_role_label(str(message.get('role', 'user')))}: "
            f"{_trim_attachment_text(text, limit=900)}"
        )

    if not rendered_messages:
        return ""
    return _trim_attachment_text("\n\n".join(rendered_messages), limit=max_chars)


def _looks_like_contextual_follow_up(user_instruction: str) -> bool:
    lowered = (user_instruction or "").strip().lower()
    if not lowered:
        return False

    markers = (
        "根据你分析",
        "根据上面",
        "根据前面",
        "根据刚才",
        "根据之前",
        "根据上述",
        "基于上面",
        "基于前面",
        "基于刚才",
        "基于之前",
        "参考上面",
        "参考前面",
        "按上面",
        "按前面",
        "按刚才",
        "按之前",
        "按这个",
        "照这个",
        "用刚才的",
        "用上面的",
        "延续上面",
        "继续刚才",
        "上述内容",
        "前面的内容",
        "刚才的分析",
        "之前的分析",
        "based on your analysis",
        "based on the above",
        "based on that",
        "use the above",
        "from the previous",
    )
    return any(marker in lowered for marker in markers)


def _guess_extension(value: str) -> str:
    if not value:
        return ""
    cleaned = value.split("?", 1)[0].split("#", 1)[0].strip().lower()
    if "." not in cleaned:
        return ""
    return cleaned.rsplit(".", 1)[-1]


def _build_internal_minio_url(object_path: str) -> str:
    endpoint = (settings.minio_endpoint or "").strip()
    if not endpoint:
        return ""
    scheme = "https" if settings.minio_secure else "http"
    bucket = settings.minio_bucket_name or "images"
    normalized_object_path = object_path.lstrip("/")
    return f"{scheme}://{endpoint}/{bucket}/{normalized_object_path}"


def _try_map_public_url_to_internal_minio(raw_ref: str) -> Optional[str]:
    """Map browser-facing MinIO URL/path to backend-accessible MinIO URL."""
    if not raw_ref:
        return None

    bucket = settings.minio_bucket_name or "images"
    parsed = urlsplit(raw_ref) if raw_ref.startswith(("http://", "https://")) else None
    raw_path = parsed.path if parsed else raw_ref
    path = unquote(raw_path or "").strip()
    if not path:
        return None

    candidate_prefixes: List[str] = [f"/{bucket}"]
    prefix = (settings.minio_url_prefix or "").strip()
    if prefix:
        prefix_path = urlsplit(prefix).path if prefix.startswith(("http://", "https://")) else prefix
        prefix_path = "/" + prefix_path.lstrip("/")
        candidate_prefixes.insert(0, prefix_path.rstrip("/"))

    for candidate in candidate_prefixes:
        normalized_candidate = candidate.rstrip("/")
        if not normalized_candidate:
            continue
        marker = normalized_candidate + "/"
        if path.startswith(marker):
            object_path = path[len(marker):]
            internal_url = _build_internal_minio_url(object_path)
            if internal_url:
                return internal_url

    return None


def _get_default_text_model() -> str:
    return settings.assistant_text_model or settings.langchain_pdf_prompt_model or settings.openai_model or "gpt-4o-mini"


def _get_default_planner_model() -> str:
    return settings.assistant_planner_model or settings.langchain_pdf_prompt_model or _get_default_text_model()


def _get_default_ocr_model() -> str:
    return settings.assistant_ocr_model or _get_default_text_model()


IMAGE_MODEL_SYSTEM_PROMPT = (
    "You are an expert prompt orchestrator for image generation models. "
    "IMPORTANT: Unless the user explicitly requests English or another language, "
    "always generate images with Chinese text (中文). All text, labels, titles, captions, "
    "and annotations in the generated image MUST be in Chinese by default. "
    "When generating images, all visible text in the image must be in Chinese, and there must be no typos, misspellings, "
    "or incorrect characters. "
    "Write production-ready prompts that instruct the image model to use Chinese for all visible text. "
    "Follow the user's latest explicit request first, use recent conversation only as supporting context, "
    "and treat attachment-derived facts as grounded constraints. "
    "Preserve the main subject, composition, layout, visible text, numbers, colors, branding, and key visual hierarchy "
    "unless the user explicitly asks to change them. "
    "Favor coherent composition, accurate perspective, clean edges, natural lighting, plausible materials, "
    "readable typography, and no irrelevant extra objects, duplicated elements, or distorted details. "
    "When OCR text is provided, preserve the wording, casing, punctuation, numbers, and hierarchy faithfully unless "
    "the user explicitly requests a rewrite. "
    "Output only prompt content intended for the image model."
)

VISUAL_ANALYSIS_SYSTEM_PROMPT = (
    "You analyze a reference image for downstream image generation. "
    "Return concise grounded facts about subject, composition, layout, typography placement, color palette, "
    "lighting, materials, camera angle, scene structure, and notable constraints. "
    "Do not invent missing details."
)

IMAGE_OCR_SYSTEM_PROMPT = (
    "You perform OCR for reference images used in image generation. "
    "Extract all visible text faithfully, preserving numbers, punctuation, casing, brand names, slogans, and useful line breaks. "
    "If some text is unreadable, say so instead of guessing."
)

IMAGE_PROMPT_TRANSLATION_SYSTEM_PROMPT = (
    "You translate image-generation prompts into high-quality English prompts. "
    "Preserve all constraints, composition details, layout instructions, visual hierarchy, brand names, product names, "
    "numbers, and any literal text that should appear in the generated image. "
    "Keep OCR-derived visible text unchanged unless the source explicitly asks to translate it. "
    "Do not add new facts. Return valid JSON only."
)

TEXT_INTENT_CLASSIFIER_SYSTEM_PROMPT = (
    "你现在是一个生图或者文本问答意图识别的高手。"
    "请分析用户最新输入到底是要让模型生图，还是只是进行文本问答、解释、分析、总结、提取、翻译、润色或普通对话。"
    "如果用户明确要求生成图片、海报、插画、封面、配图、漫画、设计稿，或者要求画、绘制、创建、生成图片，则判断为 route=image。"
    "如果用户是在提问、解释内容、分析材料、总结信息、翻译文本、识别内容、讨论方案，判断为 route=chat。"
    "当表达有歧义时，优先判断为 route=chat，不要误判成生图。"
    "当 route=image 且用户要求多张图片时，intent_type=batch_generate；否则 intent_type=single_generate。"
    "当 route=chat 时，intent_type=chat。"
)

IMAGE_MODEL_TEXT_INTENT_CLASSIFIER_SYSTEM_PROMPT = (
    "你现在是一个生图意图识别高手。用户当前已经明确选择了生图模型。"
    "你只需要判断用户最新输入是不是明确在要求生成图片。"
    "如果用户是在要求制作海报、封面、插画、配图、漫画、KV、宣传图、视觉稿、设计图，"
    "或者要求画、绘制、生成图片、按某种风格排版出图，则判断为 route=image。"
    "如果用户只是提问、解释、分析、总结、翻译、润色、问答、讨论方案，而没有明确要求出图，则判断为 route=chat。"
    "当表达有歧义时，在已选择生图模型的前提下，只要存在明确的海报、图片、风格、排版、配色、字体、比例、分辨率、插画、视觉设计等出图信号，就优先判断为 route=image。"
    "当 route=image 且用户要求多张图片时，intent_type=batch_generate；否则 intent_type=single_generate。"
    "当 route=chat 时，intent_type=chat。"
)


def _trim_attachment_text(text: str, limit: Optional[int] = None) -> str:
    text = (text or "").strip()
    effective_limit = limit or settings.assistant_attachment_text_limit or 4000
    if len(text) <= effective_limit:
        return text
    return text[: effective_limit - 3].rstrip() + "..."


def _max_pdf_pages() -> int:
    return max(1, settings.assistant_pdf_ocr_max_pages or 50)


def _derive_batch_count(user_instruction: str, requested_count: Optional[int]) -> int:
    if requested_count and requested_count > 0:
        return max(1, min(requested_count, 10))

    lowered_instruction = (user_instruction or "").lower()
    patterns = (
        r"(\d+)\s*(?:张|个|幅|版|套)",
        r"(?:generate|create|make|draw|render)\s+(\d+)\s+(?:images?|variants?)",
    )
    for pattern in patterns:
        match = re.search(pattern, user_instruction or "", re.IGNORECASE)
        if not match:
            continue
        try:
            return max(1, min(int(match.group(1)), 10))
        except ValueError:
            continue
    batch_markers = (
        "多生成",
        "多来",
        "再来",
        "多张",
        "几张",
        "多一些",
        "类似图片",
        "more images",
        "more like this",
        "variations",
        "variants",
    )
    if any(marker in lowered_instruction for marker in batch_markers):
        return 4
    return 1


async def _build_model(api_key: Optional[str] = None, model: Optional[str] = None) -> "ChatOpenAI":
    """
    构建 LangChain ChatOpenAI 模型实例。
    如果未传入 api_key，使用管理员统一配置（从 SystemConfig 表读取）。
    """
    if not LANGCHAIN_ASSISTANT_AVAILABLE or ChatOpenAI is None:
        raise RuntimeError("LangChain/LangGraph is not installed.")

    key = (api_key or "").strip()
    if not key:
        # 使用管理员统一配置
        base_url, key = await get_relay_config()
        if not key:
            raise RuntimeError("系统未配置 API Key，请联系管理员")
        base_url = normalize_openai_base_url(base_url)
    else:
        base_url = normalize_openai_base_url(settings.openai_base_url or settings.relay_base_url)

    # 脱敏日志：只显示 key 的前4位和后4位
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
    logger.info(f"LangChain ChatOpenAI client: base_url={base_url}, api_key={masked_key}, model={model or _get_default_planner_model()}")

    return ChatOpenAI(
        model=model or _get_default_planner_model(),
        temperature=0,
        api_key=key,
        base_url=base_url,
    )


async def _resolve_file_reference(file_ref: str, db_manager) -> Dict[str, str]:
    raw_ref = str(file_ref).strip()
    if raw_ref.startswith(("http://", "https://")):
        parsed = urlsplit(raw_ref)
        name = unquote(parsed.path.rsplit("/", 1)[-1]) or raw_ref
        extension = _guess_extension(name) or _guess_extension(parsed.path)
        resolved_url = _try_map_public_url_to_internal_minio(raw_ref) or raw_ref
        logger.info(
            "Resolved attachment URL: original={}, resolved={}, extension={}",
            raw_ref,
            resolved_url,
            extension or "unknown",
        )
        return {
            "url": resolved_url,
            "name": name,
            "extension": extension,
        }

    if raw_ref.startswith("/"):
        name = unquote(raw_ref.split("?", 1)[0].rsplit("/", 1)[-1]) or raw_ref
        extension = _guess_extension(name) or _guess_extension(raw_ref)
        resolved_url = _try_map_public_url_to_internal_minio(raw_ref)
        if resolved_url:
            logger.info(
                "Resolved attachment path: original={}, resolved={}, extension={}",
                raw_ref,
                resolved_url,
                extension or "unknown",
            )
            return {
                "url": resolved_url,
                "name": name,
                "extension": extension,
            }

    file_info = await db_manager.get_file_by_id(file_ref)
    if not file_info:
        logger.warning("Attachment file reference not found in database: {}", file_ref)
        raise ValueError(f"File not found: {file_ref}")

    file_url = getattr(file_info, "file_url", "") or ""
    if file_url.startswith(("http://", "https://")):
        resolved_url = _try_map_public_url_to_internal_minio(file_url) or file_url
    else:
        minio_url = _try_map_public_url_to_internal_minio(file_url)
        if minio_url:
            resolved_url = minio_url
        else:
            base_url = getattr(settings, "base_url", "http://backend:8888")
            resolved_url = f"{base_url}{file_url}"

    extension = (
        (getattr(file_info, "file_extension", "") or "").lower().lstrip(".")
        or _guess_extension(getattr(file_info, "original_filename", "") or "")
        or _guess_extension(resolved_url)
    )
    name = getattr(file_info, "original_filename", "") or resolved_url.split("?", 1)[0].rsplit("/", 1)[-1]
    logger.info(
        "Resolved attachment file id={} -> url={}, extension={}",
        file_ref,
        resolved_url,
        extension or "unknown",
    )
    return {
        "url": resolved_url,
        "name": name,
        "extension": extension,
    }


async def _download_file_bytes(url: str) -> bytes:
    if httpx is None:
        raise RuntimeError("httpx is required for attachment loading.")

    async with httpx.AsyncClient(timeout=120) as client:
        logger.info("Downloading attachment bytes from {}", url)
        response = await client.get(url)
        response.raise_for_status()
        content = response.content
        logger.info("Downloaded attachment bytes: {} bytes from {}", len(content), url)
        return content


async def _run_visual_grounding_prompt(
    *,
    image_urls: List[str],
    instruction: str,
    api_key: Optional[str],
    system_prompt: str,
    model: Optional[str],
    log_label: str,
    limit: Optional[int] = None,
) -> str:
    if not image_urls or not LANGCHAIN_ASSISTANT_AVAILABLE or HumanMessage is None or SystemMessage is None:
        return ""

    try:
        llm = await _build_model(api_key=api_key, model=model)
        content: List[Dict[str, Any]] = [{"type": "text", "text": instruction}]
        for image_url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=content),
            ]
        )
        raw_text = response.content if isinstance(response.content, str) else _extract_message_text(response.content)
        return _trim_attachment_text(raw_text, limit=limit)
    except Exception as exc:
        logger.warning("{} failed: {}", log_label, exc)
        return ""


async def _extract_visual_excerpt(
    *,
    image_urls: List[str],
    instruction: str,
    api_key: Optional[str],
) -> str:
    return await _run_visual_grounding_prompt(
        image_urls=image_urls,
        instruction=instruction,
        api_key=api_key,
        system_prompt=(
            "You extract grounded content from visual attachments. "
            "Return concise plain text that preserves visible text, key entities, "
            "important numbers, and a short visual summary when useful."
        ),
        model=_get_default_ocr_model(),
        log_label="Visual attachment extraction",
    )


def _build_image_grounding_excerpt(visual_analysis: str, ocr_text: str) -> str:
    sections: List[str] = []
    if visual_analysis:
        sections.append(f"[Visual analysis]\n{visual_analysis}")
    if ocr_text:
        sections.append(f"[OCR]\n{ocr_text}")
    return _trim_attachment_text(
        "\n\n".join(section for section in sections if section),
        limit=settings.assistant_attachment_text_limit or 12000,
    )


async def _extract_image_grounding_bundle(
    file_bytes: bytes,
    extension: str,
    api_key: Optional[str],
) -> Dict[str, str]:
    mime_extension = "jpeg" if extension == "jpg" else extension
    data_url = f"data:image/{mime_extension};base64,{base64.b64encode(file_bytes).decode('ascii')}"

    visual_analysis = await _run_visual_grounding_prompt(
        image_urls=[data_url],
        instruction=(
            "Analyze this reference image for downstream image generation. "
            "Describe the subject, composition, spatial structure, scene, style, typography placement, "
            "key objects, lighting, colors, materials, and any visual constraints that should be preserved."
        ),
        api_key=api_key,
        system_prompt=VISUAL_ANALYSIS_SYSTEM_PROMPT,
        model=_get_default_planner_model(),
        log_label="Reference image analysis",
        limit=2400,
    )
    ocr_text = await _run_visual_grounding_prompt(
        image_urls=[data_url],
        instruction=(
            "Perform OCR on this reference image. Extract visible text faithfully and preserve line breaks, "
            "numbers, punctuation, casing, brand names, slogans, and typographic hierarchy when possible."
        ),
        api_key=api_key,
        system_prompt=IMAGE_OCR_SYSTEM_PROMPT,
        model=_get_default_ocr_model(),
        log_label="Reference image OCR",
        limit=2400,
    )

    return {
        "visual_analysis": visual_analysis,
        "ocr_text": ocr_text,
        "combined_excerpt": _build_image_grounding_excerpt(visual_analysis, ocr_text),
    }


def _extract_pdf_native_pages(file_bytes: bytes) -> List[str]:
    max_pages = _max_pdf_pages()
    native_pages: List[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages[:max_pages]:
            native_pages.append((page.extract_text() or "").strip())
    return native_pages


def _render_pdf_pages_to_data_urls(file_bytes: bytes) -> List[str]:
    if fitz is None:
        return []

    max_pages = _max_pdf_pages()
    document = fitz.open(stream=file_bytes, filetype="pdf")
    page_urls: List[str] = []
    try:
        for page_index in range(min(document.page_count, max_pages)):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            encoded = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
            page_urls.append(f"data:image/png;base64,{encoded}")
    finally:
        document.close()
    return page_urls


def _combine_pdf_page_excerpts(page_excerpts: List[str]) -> str:
    combined_pages = [
        f"[Page {page_index}]\n{page_excerpt}"
        for page_index, page_excerpt in enumerate(page_excerpts, start=1)
        if (page_excerpt or "").strip()
    ]
    if not combined_pages:
        return ""
    return _trim_attachment_text(
        "\n\n".join(combined_pages),
        limit=settings.assistant_attachment_text_limit or 12000,
    )


async def _extract_pdf_page_excerpts(file_bytes: bytes, api_key: Optional[str]) -> List[str]:
    native_pages = _extract_pdf_native_pages(file_bytes)
    if not native_pages:
        return []

    native_threshold = settings.assistant_pdf_native_text_threshold or 120
    needs_ocr = any(len((page_text or "").strip()) < native_threshold for page_text in native_pages)
    page_urls = _render_pdf_pages_to_data_urls(file_bytes) if needs_ocr else []

    page_excerpts: List[str] = []
    for page_index, native_text in enumerate(native_pages, start=1):
        trimmed_native = _trim_attachment_text(native_text)
        if len(trimmed_native.strip()) >= native_threshold:
            page_excerpts.append(trimmed_native)
            continue

        ocr_text = ""
        if page_index - 1 < len(page_urls):
            ocr_text = await _extract_visual_excerpt(
                image_urls=[page_urls[page_index - 1]],
                instruction=(
                    f"This is page {page_index} of a PDF. "
                    "Extract the visible text faithfully, preserve key numbers and headings, "
                    "and briefly mention diagrams or layout cues when they matter."
                ),
                api_key=api_key,
            )
        trimmed_ocr = _trim_attachment_text(ocr_text)
        page_excerpts.append(trimmed_ocr if len(trimmed_ocr) >= len(trimmed_native) else trimmed_native)

    return page_excerpts


async def _extract_pdf_excerpt_bundle(file_bytes: bytes, api_key: Optional[str]) -> tuple[str, List[str]]:
    page_excerpts = await _extract_pdf_page_excerpts(file_bytes, api_key)
    return _combine_pdf_page_excerpts(page_excerpts), page_excerpts


def _is_doc_heading(text: str, style_name: str) -> bool:
    stripped = (text or "").strip()
    normalized_style = (style_name or "").strip().lower()
    if not stripped:
        return False
    if "heading" in normalized_style:
        return True

    heading_patterns = (
        r"^第[一二三四五六七八九十百千0-9]+[章节部分篇条]",
        r"^[0-9]+(?:\.[0-9]+){0,3}[、.)． ]",
        r"^[一二三四五六七八九十]+[、.．)]",
    )
    return any(re.match(pattern, stripped) for pattern in heading_patterns)


def _extract_docx_section_excerpts(file_bytes: bytes) -> List[str]:
    document = Document(io.BytesIO(file_bytes))
    max_sections = max(1, settings.assistant_pdf_ocr_max_pages or 50)
    section_char_limit = min(1800, max(600, (settings.assistant_attachment_text_limit or 12000) // 4))

    sections: List[str] = []
    current_lines: List[str] = []
    current_chars = 0

    def flush_current() -> None:
        nonlocal current_lines, current_chars
        if not current_lines:
            return
        sections.append(
            _trim_attachment_text(
                "\n".join(current_lines),
                limit=section_char_limit,
            )
        )
        current_lines = []
        current_chars = 0

    for paragraph in document.paragraphs:
        text = (paragraph.text or "").strip()
        if not text:
            continue

        style_name = getattr(getattr(paragraph, "style", None), "name", "") or ""
        is_heading = _is_doc_heading(text, style_name)

        if is_heading and current_lines:
            flush_current()

        projected_chars = current_chars + len(text) + (1 if current_lines else 0)
        if current_lines and projected_chars > section_char_limit and len(sections) + 1 < max_sections:
            flush_current()

        current_lines.append(text)
        current_chars += len(text) + (1 if len(current_lines) > 1 else 0)

    flush_current()

    if not sections:
        return []
    return sections[:max_sections]


def _combine_docx_section_excerpts(section_excerpts: List[str]) -> str:
    combined_sections = [
        f"[Section {section_index}]\n{section_excerpt}"
        for section_index, section_excerpt in enumerate(section_excerpts, start=1)
        if (section_excerpt or "").strip()
    ]
    if not combined_sections:
        return ""
    return _trim_attachment_text(
        "\n\n".join(combined_sections),
        limit=settings.assistant_attachment_text_limit or 12000,
    )


def _extract_docx_excerpt_bundle(file_bytes: bytes) -> tuple[str, List[str]]:
    section_excerpts = _extract_docx_section_excerpts(file_bytes)
    return _combine_docx_section_excerpts(section_excerpts), section_excerpts


async def _extract_image_excerpt(file_bytes: bytes, extension: str, api_key: Optional[str]) -> str:
    mime_extension = "jpeg" if extension == "jpg" else extension
    data_url = f"data:image/{mime_extension};base64,{base64.b64encode(file_bytes).decode('ascii')}"
    return await _extract_visual_excerpt(
        image_urls=[data_url],
        instruction=(
            "Describe this attachment for downstream reasoning. "
            "Extract visible text, key entities, major objects, and the scene in concise plain text."
        ),
        api_key=api_key,
    )


async def _extract_attachment_excerpt(
    *,
    url: str,
    extension: str,
    api_key: Optional[str],
) -> str:
    if extension not in {"docx", "doc", "jpg", "jpeg", "png", "gif", "webp", "bmp"}:
        return ""

    if extension in {"docx", "doc"}:
        file_bytes = await _download_file_bytes(url)
        excerpt, _ = _extract_docx_excerpt_bundle(file_bytes)
        return excerpt
    if extension in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
        file_bytes = await _download_file_bytes(url)
        return await _extract_image_excerpt(file_bytes, extension, api_key)
    return ""


async def _load_attachment_descriptors(
    files: Optional[List[str]],
    db_manager,
    api_key: Optional[str],
) -> List[AttachmentDescriptor]:
    descriptors: List[AttachmentDescriptor] = []

    for file_ref in files or []:
        try:
            resolved = await _resolve_file_reference(file_ref, db_manager)
        except Exception as exc:
            logger.warning("Failed to resolve attachment reference {}: {}", file_ref, exc)
            continue

        extension = (resolved.get("extension") or "").lower()
        logger.info(
            "Processing attachment: name={}, extension={}, url={}",
            resolved.get("name", ""),
            extension or "unknown",
            resolved.get("url", ""),
        )
        if extension in {"pdf", "docx", "doc"}:
            page_excerpts: Optional[List[str]] = None
            try:
                file_bytes = await _download_file_bytes(resolved["url"])
                if extension == "pdf":
                    excerpt, page_excerpts = await _extract_pdf_excerpt_bundle(file_bytes, api_key)
                else:
                    excerpt, page_excerpts = _extract_docx_excerpt_bundle(file_bytes)
            except Exception as exc:
                logger.warning(
                    "Failed to extract text from attachment {} ({}): {}",
                    resolved.get("name", ""),
                    extension,
                    exc,
                )
                excerpt = ""
                page_excerpts = None
            if excerpt:
                logger.info(
                    "Attachment text extracted: name={}, extension={}, chars={}",
                    resolved.get("name", ""),
                    extension,
                    len(excerpt),
                )
            else:
                logger.warning(
                    "Attachment text extraction returned empty: name={}, extension={}",
                    resolved.get("name", ""),
                    extension,
                )
            descriptors.append(
                AttachmentDescriptor(
                    name=resolved["name"],
                    kind=extension,
                    source=resolved["url"],
                    text_excerpt=excerpt or None,
                    page_excerpts=page_excerpts or None,
                )
            )
            continue

        if extension in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
            excerpt = ""
            visual_analysis = ""
            ocr_text = ""
            try:
                file_bytes = await _download_file_bytes(resolved["url"])
                grounding_bundle = await _extract_image_grounding_bundle(
                    file_bytes,
                    extension,
                    api_key,
                )
                excerpt = grounding_bundle.get("combined_excerpt", "")
                visual_analysis = grounding_bundle.get("visual_analysis", "")
                ocr_text = grounding_bundle.get("ocr_text", "")
            except Exception as exc:
                logger.warning(
                    "Failed to extract image attachment context {} ({}): {}",
                    resolved.get("name", ""),
                    extension,
                    exc,
                )
                excerpt = ""
            descriptors.append(
                AttachmentDescriptor(
                    name=resolved["name"],
                    kind="image",
                    source=resolved["url"],
                    text_excerpt=excerpt or None,
                    visual_analysis=visual_analysis or None,
                    ocr_text=ocr_text or None,
                )
            )

        if extension not in {"pdf", "docx", "doc", "jpg", "jpeg", "png", "gif", "webp", "bmp"}:
            logger.warning(
                "Skipping unsupported attachment extension: name={}, extension={}",
                resolved.get("name", ""),
                extension or "unknown",
            )

    return descriptors


async def _is_image_model_name(model_name: Optional[str], app_state) -> bool:
    if not model_name:
        return False

    try:
        model_registry = getattr(app_state, "model_registry", None)
        if model_registry:
            model_info = model_registry.get_model_info(model_name)
            if model_info:
                model_type = str(getattr(model_info, "model_type", "") or "").lower()
                if any(token in model_type for token in ("image", "图像", "图片")):
                    return True
    except Exception:
        pass

    lowered = model_name.lower()
    image_tokens = (
        "dall-e",
        "midjourney",
        "ideogram",
        "imagen",
        "gpt-image",
        "image-preview",
        "flash-image",
        "image-generation",
        "stable-diffusion",
        "flux",
        "fal-ai",
        "kling",
        "wanx",
        "seedream",
    )
    if any(token in lowered for token in image_tokens):
        return True
    return bool(re.search(r"(?:^|[-_/])(image|images)(?:[-_/]|$)", lowered))


def _is_explicit_chat_model_type(model_type: Optional[str]) -> bool:
    normalized = str(model_type or "").strip().lower()
    return normalized in {"chat", "text", "文本"}


def _is_explicit_image_model_type(model_type: Optional[str]) -> bool:
    normalized = str(model_type or "").strip().lower()
    return normalized in {"image", "图像", "图片"}


async def _resolve_chat_model_name(
    request_model: Optional[str],
    request_model_type: Optional[str],
    app_state,
) -> str:
    if _is_explicit_image_model_type(request_model_type):
        return _get_default_text_model()
    if request_model and not await _is_image_model_name(request_model, app_state):
        return request_model
    return _get_default_text_model()


async def _resolve_image_model_name(
    request_model: Optional[str],
    request_model_type: Optional[str],
    app_state,
) -> Optional[str]:
    if request_model and _is_explicit_image_model_type(request_model_type):
        return request_model
    if request_model and await _is_image_model_name(request_model, app_state):
        return request_model
    return settings.openai_image_model or None


def _is_gemini_native_image_model_name(model_name: Optional[str]) -> bool:
    if not model_name:
        return False
    lowered = model_name.lower()
    return "gemini" in lowered and "imagen" not in lowered


def _build_reference_image_system_context(attachments: List[AttachmentDescriptor]) -> str:
    blocks: List[str] = []
    reference_index = 0

    for attachment in attachments:
        if attachment.kind != "image":
            continue
        if not attachment.visual_analysis and not attachment.ocr_text:
            continue

        reference_index += 1
        if reference_index > 3:
            break

        sections: List[str] = []
        if attachment.visual_analysis:
            sections.append(
                f"Reference image {reference_index} analysis:\n"
                f"{_trim_attachment_text(attachment.visual_analysis, limit=1800)}"
            )
        if attachment.ocr_text:
            sections.append(
                f"Reference image {reference_index} OCR text to preserve when relevant:\n"
                f"{_trim_attachment_text(attachment.ocr_text, limit=1800)}"
            )

        if sections:
            blocks.append("\n\n".join(sections))

    return "\n\n".join(blocks)


def _build_effective_image_system_prompt(
    *,
    attachments: List[AttachmentDescriptor],
    model_name: Optional[str],
) -> str:
    sections = [IMAGE_MODEL_SYSTEM_PROMPT.strip()]

    if _is_gemini_native_image_model_name(model_name):
        reference_context = _build_reference_image_system_context(attachments)
        if reference_context:
            sections.append(
                "Reference image grounding to honor while generating:\n"
                f"{reference_context}"
            )

    return "\n\n".join(section for section in sections if section)


def _compose_image_model_prompt(
    *,
    system_prompt: str,
    recent_context: str,
    user_prompt: str,
    planned_prompt: str,
) -> str:
    sections: List[str] = []

    if system_prompt.strip():
        sections.append(f"System instructions:\n{system_prompt.strip()}")
    if recent_context.strip():
        sections.append(f"Recent conversation context:\n{recent_context.strip()}")

    # 避免 user_prompt 和 planned_prompt 内容重复拼接
    user_text = user_prompt.strip()
    planned_text = planned_prompt.strip()
    if user_text and planned_text:
        # 如果两者内容基本一致（互相包含），只保留一份
        if user_text in planned_text or planned_text in user_text:
            sections.append(planned_text)
        else:
            sections.append(f"Latest user request:\n{user_text}")
            sections.append(f"Final grounded generation brief:\n{planned_text}")
    elif planned_text:
        sections.append(planned_text)
    elif user_text:
        sections.append(user_text)

    return _trim_attachment_text(
        "\n\n".join(sections),
        limit=settings.assistant_attachment_text_limit or 12000,
    )


async def _translate_prompts_to_english(
    prompts: List[str],
    api_key: Optional[str],
) -> List[str]:
    normalized_prompts = [str(prompt or "").strip() for prompt in prompts]
    if not normalized_prompts or not LANGCHAIN_ASSISTANT_AVAILABLE or HumanMessage is None or SystemMessage is None:
        return normalized_prompts

    try:
        llm = await _build_model(api_key=api_key, model=_get_default_planner_model())
        response = await llm.ainvoke(
            [
                SystemMessage(content=IMAGE_PROMPT_TRANSLATION_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        "Translate the following image-generation prompts into English for better model accuracy. "
                        "Return JSON only in the shape {\"prompts\": [...]} and keep the array length unchanged.\n\n"
                        f"{json.dumps({'prompts': normalized_prompts}, ensure_ascii=False)}"
                    )
                ),
            ]
        )
        raw_text = response.content if isinstance(response.content, str) else _extract_message_text(response.content)
        cleaned = (raw_text or "").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Translation response is not valid JSON")

        payload = json.loads(cleaned[start : end + 1])
        translated_prompts = payload.get("prompts")
        if (
            isinstance(translated_prompts, list)
            and len(translated_prompts) == len(normalized_prompts)
            and all(str(item or "").strip() for item in translated_prompts)
        ):
            return [str(item).strip() for item in translated_prompts]
        raise ValueError("Translation response has an unexpected prompts array")
    except Exception as exc:
        logger.warning("Image prompt translation failed, using original prompt text: {}", exc)
        return normalized_prompts


def _normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for message in messages:
        role = str(message.get("role", "")).strip()
        content = message.get("content", "")
        if not role:
            continue
        if role == "assistant" and _is_placeholder_assistant_message(content):
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def _apply_attachments_to_chat_messages(
    messages: List[Dict[str, Any]],
    attachments: List[AttachmentDescriptor],
) -> List[Dict[str, Any]]:
    normalized = _normalize_messages(messages)
    if not normalized:
        return normalized

    last_user_index = None
    for index in range(len(normalized) - 1, -1, -1):
        if normalized[index]["role"] == "user":
            last_user_index = index
            break

    if last_user_index is None or not attachments:
        return normalized

    text_blocks = [
        f"[Attachment: {attachment.name}]\n{attachment.text_excerpt}"
        for attachment in attachments
        if attachment.text_excerpt
    ]
    image_urls = [
        attachment.source
        for attachment in attachments
        if attachment.kind == "image" and attachment.source
    ]

    target_message = dict(normalized[last_user_index])
    base_text = _extract_message_text(target_message.get("content", ""))
    if text_blocks:
        base_text = "\n\n".join(text_blocks + ([base_text] if base_text else []))

    if image_urls:
        multimodal_content = [{"type": "text", "text": base_text or "Please use the attached images."}]
        for image_url in image_urls:
            multimodal_content.append({"type": "image_url", "image_url": {"url": image_url}})
        target_message["content"] = multimodal_content
    else:
        target_message["content"] = base_text

    normalized[last_user_index] = target_message
    return normalized


def _fallback_text_route(
    user_instruction: str,
    model_hint: Optional[str],
    requested_count: Optional[int],
    messages: Optional[List[Dict[str, Any]]] = None,
) -> TextIntentDecision:
    text = (user_instruction or "").strip().lower()
    batch_count = _derive_batch_count(user_instruction, requested_count)
    recent_context = _build_recent_conversation_context(messages or [])
    contextual_follow_up = _looks_like_contextual_follow_up(user_instruction)

    chat_keywords = [
        "summarize",
        "summary",
        "explain",
        "analyze",
        "translate",
        "extract",
        "review",
        "read",
        "question",
        "总结",
        "摘要",
        "解释",
        "分析",
        "翻译",
        "提取",
        "阅读",
        "问答",
        "识别",
        "内容",
        "讲了什么",
    ]
    image_keywords = [
        "generate image",
        "generate",
        "draw",
        "render",
        "illustration",
        "poster",
        "banner",
        "flyer",
        "layout",
        "typography",
        "color palette",
        "visual design",
        "cover",
        "concept art",
        "生图",
        "生成",
        "画",
        "绘制",
        "创建图片",
        "海报",
        "宣传图",
        "kv",
        "主视觉",
        "排版",
        "版式",
        "配色",
        "字体",
        "分辨率",
        "图片比例",
        "视觉",
        "设计稿",
        "插画风",
        "封面",
        "配图",
        "渲染",
        "出图",
    ]

    chat_keyword_score = sum(1 for keyword in chat_keywords if keyword in text)
    image_keyword_score = sum(1 for keyword in image_keywords if keyword in text)
    chat_score = chat_keyword_score
    image_score = image_keyword_score

    if model_hint == "chat":
        chat_score += 1
    if model_hint == "image" and image_keyword_score > 0:
        image_score += 1
    if model_hint == "image" and contextual_follow_up:
        if image_keyword_score > 0 or batch_count > 1:
            image_score += 2
        elif chat_keyword_score == 0 and recent_context and len(text) <= 24:
            image_score += 1

    if batch_count > 1:
        image_score += 2

    if not text:
        if model_hint == "image":
            return TextIntentDecision(
                route="image",
                intent_type="single_generate",
                batch_count=1,
                confidence=0.55,
                reasoning="Empty instruction with image model hint; defaulting to image generation.",
            )
        return TextIntentDecision(
            route="chat",
            intent_type="chat",
            batch_count=1,
            confidence=0.8,
            reasoning="Empty instruction; defaulting to chat.",
        )

    if image_score > chat_score and image_score >= 1 and (image_keyword_score > 0 or batch_count > 1):
        return TextIntentDecision(
            route="image",
            intent_type="batch_generate" if batch_count > 1 else "single_generate",
            batch_count=batch_count,
            confidence=min(0.9, 0.58 + image_score * 0.08),
            reasoning="Fallback rules detected image-generation intent from the text request.",
        )

    return TextIntentDecision(
        route="chat",
        intent_type="chat",
        batch_count=1,
        confidence=min(0.92, 0.68 + chat_score * 0.06),
        reasoning="Fallback rules defaulted to chat understanding.",
    )


def _has_clear_image_generation_cue_for_image_model(user_instruction: str) -> bool:
    text = (user_instruction or "").strip().lower()
    if not text:
        return False

    strong_image_patterns = (
        r"(帮我|请|给我|为我).{0,20}(做|生成|画|制作|设计|出).{0,20}(一张|海报|图片|图像|封面|插画|配图|宣传图|主视觉|kv)",
        r"(海报|封面|插画|配图|宣传图|主视觉|kv|视觉稿|设计稿)",
        r"(风格|排版|版式|配色|字体|比例|分辨率|尺寸|9:16|16:9|3d|2k|4k|高清|超清)",
        r"(生成一张|做一张|设计一张|出一张).{0,20}(海报|图片|图像|封面|插画)",
    )

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in strong_image_patterns)


async def _classify_text_request(
    *,
    messages: List[Dict[str, Any]],
    user_instruction: str,
    request_model: Optional[str],
    request_model_type: Optional[str],
    requested_count: Optional[int],
    app_state,
    api_key: Optional[str],
) -> RequestRouteDecision:
    explicit_image_model_selected = _is_explicit_image_model_type(request_model_type)
    model_hint = request_model_type
    if not model_hint and request_model:
        model_hint = "image" if await _is_image_model_name(request_model, app_state) else "chat"

    recent_context = _build_recent_conversation_context(messages)
    fallback = _fallback_text_route(
        user_instruction,
        model_hint,
        requested_count,
        messages=messages,
    )

    if explicit_image_model_selected and _has_clear_image_generation_cue_for_image_model(user_instruction):
        batch_count = _derive_batch_count(user_instruction, requested_count)
        return RequestRouteDecision(
            route="image",
            intent_type="batch_generate" if batch_count > 1 else "single_generate",
            batch_count=batch_count,
            confidence=0.96,
            reasoning="The user selected an image model and the prompt contains clear poster/design/image-generation cues.",
            source="image-model-cues",
            planning_basis="text",
        )

    if explicit_image_model_selected and fallback.route == "image":
        return RequestRouteDecision(
            route="image",
            intent_type=fallback.intent_type,
            batch_count=fallback.batch_count,
            confidence=max(fallback.confidence, 0.9),
            reasoning="The user selected an image model and the prompt contains clear image-generation cues.",
            source="image-model-rules",
            planning_basis="text",
        )

    if (
        not LANGCHAIN_ASSISTANT_AVAILABLE
        or SystemMessage is None
        or HumanMessage is None
        or not _has_llm_credentials(api_key)
    ):
        return RequestRouteDecision(
            route=fallback.route,
            intent_type=fallback.intent_type,
            batch_count=fallback.batch_count,
            confidence=fallback.confidence,
            reasoning=fallback.reasoning,
            source="fallback",
            planning_basis="text",
        )

    try:
        llm = await _build_model(
            api_key=api_key,
            model=_get_default_planner_model(),
        )
        structured = llm.with_structured_output(TextIntentDecision, method="function_calling")
        decision = await structured.ainvoke(
            [
                SystemMessage(
                    content=(
                        IMAGE_MODEL_TEXT_INTENT_CLASSIFIER_SYSTEM_PROMPT
                        if explicit_image_model_selected
                        else TEXT_INTENT_CLASSIFIER_SYSTEM_PROMPT
                    )
                ),
                HumanMessage(
                    content=(
                        f"Recent conversation context (latest first-hand references should be resolved against this): "
                        f"{recent_context or 'None'}\n"
                        f"User instruction: {user_instruction or 'None'}\n"
                        f"Model hint: {model_hint or 'none'}\n"
                        f"Requested image count hint: {_derive_batch_count(user_instruction, requested_count)}"
                    )
                ),
            ]
        )

        batch_count = _derive_batch_count(user_instruction, requested_count)
        if decision.route != "image":
            return RequestRouteDecision(
                route="chat",
                intent_type="chat",
                batch_count=1,
                confidence=max(0.0, float(decision.confidence or 0.75)),
                reasoning=decision.reasoning or "LangGraph classified the text request as chat.",
                source="langgraph",
                planning_basis="text",
            )

        llm_batch_count = decision.batch_count or batch_count
        if requested_count and requested_count > 0:
            llm_batch_count = requested_count
        llm_batch_count = max(1, min(llm_batch_count, 10))
        intent_type = "batch_generate" if llm_batch_count > 1 or decision.intent_type == "batch_generate" else "single_generate"
        return RequestRouteDecision(
            route="image",
            intent_type=intent_type,
            batch_count=llm_batch_count,
            confidence=max(0.0, float(decision.confidence or 0.75)),
            reasoning=decision.reasoning or "LangGraph classified the text request as image generation.",
            source="langgraph",
            planning_basis="text",
        )
    except Exception as exc:
        logger.warning("Assistant text classification failed, falling back to rules: {}", exc)
        return RequestRouteDecision(
            route=fallback.route,
            intent_type=fallback.intent_type,
            batch_count=fallback.batch_count,
            confidence=fallback.confidence,
            reasoning=fallback.reasoning,
            source="fallback",
            planning_basis="text",
        )


async def _decide_execution_route(
    *,
    attachments: List[AttachmentDescriptor],
    messages: List[Dict[str, Any]],
    user_instruction: str,
    request_model: Optional[str],
    request_model_type: Optional[str],
    requested_count: Optional[int],
    app_state,
    api_key: Optional[str],
) -> RequestRouteDecision:
    if _is_explicit_chat_model_type(request_model_type):
        return RequestRouteDecision(
            route="chat",
            intent_type="chat",
            batch_count=1,
            confidence=1.0,
            reasoning="The selected model is a text model, so the request is forced into chat mode.",
            source="model-selection",
            planning_basis="text",
        )

    model_hint = request_model_type
    if not model_hint and request_model:
        model_hint = "image" if await _is_image_model_name(request_model, app_state) else "chat"

    if attachments:
        decision = await build_attachment_route(
            user_instruction,
            attachments,
            api_key=api_key,
            model_hint=model_hint,
        )
        if decision.route == "image":
            batch_count = _derive_batch_count(user_instruction, requested_count)
            return RequestRouteDecision(
                route="image",
                intent_type="batch_generate" if batch_count > 1 else "single_generate",
                batch_count=batch_count,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
                source=decision.source,
                planning_basis="attachments",
            )
        return RequestRouteDecision(
            route="chat",
            intent_type="chat",
            batch_count=1,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            source=decision.source,
            planning_basis="attachments",
        )

    return await _classify_text_request(
        messages=messages,
        user_instruction=user_instruction,
        request_model=request_model,
        request_model_type=request_model_type,
        requested_count=requested_count,
        app_state=app_state,
        api_key=api_key,
    )


async def _build_image_prompt_from_attachments(
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    api_key: Optional[str] = None,
) -> str:
    def _build_attachment_grounding_block() -> str:
        blocks: List[str] = []
        for index, attachment in enumerate(attachments, start=1):
            header = f"[Attachment {index}] name={attachment.name}, kind={attachment.kind}"
            excerpt = (attachment.text_excerpt or "").strip()
            if excerpt:
                snippet = _trim_attachment_text(excerpt, limit=1600)
                blocks.append(f"{header}\n{snippet}")
            else:
                blocks.append(f"{header}\n(No OCR/text excerpt was extracted.)")
        return "\n\n".join(blocks)

    def _merge_prompt_with_grounding(base_prompt: str, grounding_block: str) -> str:
        base = (base_prompt or "").strip()
        if not grounding_block:
            return base

        if base:
            merged = (
                f"{base}\n\n"
                "Grounding content extracted from uploaded files (must be reflected in the output):\n"
                f"{grounding_block}"
            )
        else:
            merged = (
                "Generate an image strictly based on the uploaded files.\n\n"
                "Grounding content extracted from uploaded files:\n"
                f"{grounding_block}"
            )
        return _trim_attachment_text(merged, limit=settings.assistant_attachment_text_limit or 12000)

    text_attachments = [attachment for attachment in attachments if attachment.text_excerpt]
    image_attachments = [attachment for attachment in attachments if attachment.kind == "image" and attachment.source]
    grounding_block = _build_attachment_grounding_block()

    if (
        image_attachments
        and LANGCHAIN_ASSISTANT_AVAILABLE
        and HumanMessage is not None
        and SystemMessage is not None
        and _has_llm_credentials(api_key)
    ):
        try:
            llm = await _build_model(api_key=api_key, model=_get_default_planner_model())
            content: List[Dict[str, Any]] = []
            attachment_lines = [
                f"- {attachment.name}: {attachment.text_excerpt}"
                for attachment in text_attachments
                if attachment.text_excerpt
            ]
            prompt_text = (
                f"User instruction: {user_instruction or 'None'}\n"
                "Create one grounded image-generation prompt. "
                "Use attached text documents and reference images only as evidence. "
                "Do not invent unsupported details."
            )
            if attachment_lines:
                prompt_text += "\nDocument excerpts:\n" + "\n".join(attachment_lines)
            content.append({"type": "text", "text": prompt_text})
            for attachment in image_attachments[:3]:
                content.append({"type": "image_url", "image_url": {"url": attachment.source}})

            response = await llm.ainvoke(
                [
                    SystemMessage(content="You turn multimodal attachments into a faithful image-generation prompt."),
                    HumanMessage(content=content),
                ]
            )
            prompt = response.content if isinstance(response.content, str) else _extract_message_text(response.content)
            if prompt:
                return _merge_prompt_with_grounding(prompt, grounding_block)
        except Exception as exc:
            logger.warning("Attachment-grounded image prompt generation failed: {}", exc)

    if text_attachments:
        prompt_result = await build_text_attachment_prompt(user_instruction, text_attachments, api_key=api_key)
        return _merge_prompt_with_grounding(prompt_result.prompt, grounding_block)

    if image_attachments:
        reference_note = "Use the uploaded image as the primary visual reference."
        if user_instruction:
            return _merge_prompt_with_grounding(f"{user_instruction}\n\n{reference_note}", grounding_block)
        return _merge_prompt_with_grounding(reference_note, grounding_block)

    return _merge_prompt_with_grounding(user_instruction or "", grounding_block)


async def _build_contextual_image_instruction(
    *,
    user_instruction: str,
    messages: List[Dict[str, Any]],
    api_key: Optional[str],
) -> str:
    instruction = (user_instruction or "").strip()
    if not instruction:
        return ""

    recent_context = _build_recent_conversation_context(messages)
    if not recent_context:
        return instruction

    should_rewrite = _looks_like_contextual_follow_up(instruction) or len(instruction) <= 32
    if should_rewrite and LANGCHAIN_ASSISTANT_AVAILABLE and HumanMessage is not None and SystemMessage is not None and _has_llm_credentials(api_key):
        try:
            llm = await _build_model(api_key=api_key, model=_get_default_planner_model())
            response = await llm.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You rewrite the user's latest request into one standalone image-generation brief. "
                            "Use the recent conversation context to resolve references like 'based on your analysis' "
                            "or 'use the above'. Keep only information useful for image generation. "
                            "Output only the standalone brief in the user's language."
                        )
                    ),
                    HumanMessage(
                        content=(
                            f"Recent conversation context:\n{recent_context}\n\n"
                            f"Latest user request:\n{instruction}"
                        )
                    ),
                ]
            )
            rewritten = response.content if isinstance(response.content, str) else _extract_message_text(response.content)
            rewritten = (rewritten or "").strip()
            if rewritten:
                return _trim_attachment_text(
                    rewritten,
                    limit=settings.assistant_attachment_text_limit or 12000,
                )
        except Exception as exc:
            logger.warning("Failed to rewrite contextual image instruction: {}", exc)

    if should_rewrite:
        return _trim_attachment_text(
            (
                "Create an image based on the latest request and the recent conversation context.\n\n"
                f"Latest request:\n{instruction}\n\n"
                f"Recent conversation context:\n{recent_context}"
            ),
            limit=settings.assistant_attachment_text_limit or 12000,
        )

    return instruction


def _flatten_pdf_page_items(attachments: List[AttachmentDescriptor]) -> List[Dict[str, Any]]:
    page_items: List[Dict[str, Any]] = []
    for attachment in attachments:
        if attachment.kind != "pdf":
            continue

        page_excerpts = list(attachment.page_excerpts or [])
        if not page_excerpts and attachment.text_excerpt:
            page_excerpts = [attachment.text_excerpt]

        for page_number, page_excerpt in enumerate(page_excerpts, start=1):
            page_items.append(
                {
                    "attachment_name": attachment.name,
                    "page_number": page_number,
                    "page_excerpt": (page_excerpt or "").strip(),
                }
            )
    return page_items


def _flatten_word_section_items(attachments: List[AttachmentDescriptor]) -> List[Dict[str, Any]]:
    section_items: List[Dict[str, Any]] = []
    for attachment in attachments:
        if attachment.kind not in {"docx", "doc"}:
            continue

        section_excerpts = list(attachment.page_excerpts or [])
        if not section_excerpts and attachment.text_excerpt:
            section_excerpts = [attachment.text_excerpt]

        for section_number, section_excerpt in enumerate(section_excerpts, start=1):
            section_items.append(
                {
                    "attachment_name": attachment.name,
                    "section_number": section_number,
                    "section_excerpt": (section_excerpt or "").strip(),
                    "kind": attachment.kind,
                }
            )
    return section_items


def _build_shared_non_pdf_grounding(attachments: List[AttachmentDescriptor]) -> str:
    blocks: List[str] = []
    for attachment in attachments:
        if attachment.kind == "pdf":
            continue
        excerpt = (attachment.text_excerpt or "").strip()
        if not excerpt:
            continue
        blocks.append(f"[Attachment: {attachment.name}]\n{_trim_attachment_text(excerpt, limit=1600)}")
    return "\n\n".join(blocks)


def _build_shared_non_word_grounding(attachments: List[AttachmentDescriptor]) -> str:
    blocks: List[str] = []
    for attachment in attachments:
        if attachment.kind in {"docx", "doc"}:
            continue
        excerpt = (attachment.text_excerpt or "").strip()
        if not excerpt:
            continue
        blocks.append(f"[Attachment: {attachment.name}]\n{_trim_attachment_text(excerpt, limit=1600)}")
    return "\n\n".join(blocks)


async def _build_pdf_page_matched_prompts(
    *,
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    requested_count: int,
    api_key: Optional[str],
) -> List[str]:
    page_items = _flatten_pdf_page_items(attachments)
    if not page_items:
        return []

    target_count = len(page_items)
    shared_text_attachments = [
        AttachmentDescriptor(
            name=attachment.name,
            kind=attachment.kind,
            source=attachment.source,
            text_excerpt=attachment.text_excerpt,
        )
        for attachment in attachments
        if attachment.kind != "pdf" and attachment.text_excerpt
    ]
    shared_grounding = _build_shared_non_pdf_grounding(attachments)

    prompts: List[str] = []
    for prompt_index in range(target_count):
        page_item = page_items[prompt_index]
        attachment_name = str(page_item["attachment_name"])
        page_number = int(page_item["page_number"])
        page_excerpt = str(page_item.get("page_excerpt") or "").strip()
        page_fallback_excerpt = (
            page_excerpt
            or f"第 {page_number} 页没有提取到可用文本，请尽量依据该页的版式、图示或结构线索生成与这一页对应的图像。"
        )
        page_instruction = (
            f"{user_instruction or 'Generate one image based on the uploaded PDF page.'}\n\n"
            f"Generate exactly one image that corresponds only to page {page_number} of the PDF "
            f"\"{attachment_name}\". Do not mix content from other PDF pages."
        )
        page_attachment = AttachmentDescriptor(
            name=f"{attachment_name} - Page {page_number}",
            kind="pdf",
            text_excerpt=page_fallback_excerpt,
        )

        try:
            prompt_result = await build_text_attachment_prompt(
                page_instruction,
                [page_attachment, *shared_text_attachments],
                api_key=api_key,
            )
            base_prompt = prompt_result.prompt
        except Exception as exc:
            logger.warning(
                "Failed to build page-matched PDF prompt for {} page {}: {}",
                attachment_name,
                page_number,
                exc,
            )
            base_prompt = page_instruction

        prompt_sections = [
            (base_prompt or page_instruction).strip(),
            (
                f"Must correspond only to page {page_number} of the PDF "
                f"\"{attachment_name}\". Do not use content from other PDF pages."
            ),
            (
                "Primary grounding content from the matched PDF page (must be reflected in the image):\n"
                f"[Attachment: {attachment_name} | Page {page_number}]\n"
                f"{_trim_attachment_text(page_fallback_excerpt, limit=1600)}"
            ),
        ]
        if shared_grounding:
            prompt_sections.append(
                "Shared grounding from other uploaded files:\n"
                f"{shared_grounding}"
            )
        prompts.append(
            _trim_attachment_text(
                "\n\n".join(section for section in prompt_sections if section),
                limit=settings.assistant_attachment_text_limit or 12000,
            )
        )

    return prompts


async def _build_word_section_matched_prompts(
    *,
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    requested_count: int,
    api_key: Optional[str],
) -> List[str]:
    section_items = _flatten_word_section_items(attachments)
    if not section_items:
        return []

    target_count = len(section_items)
    shared_text_attachments = [
        AttachmentDescriptor(
            name=attachment.name,
            kind=attachment.kind,
            source=attachment.source,
            text_excerpt=attachment.text_excerpt,
        )
        for attachment in attachments
        if attachment.kind not in {"docx", "doc"} and attachment.text_excerpt
    ]
    shared_grounding = _build_shared_non_word_grounding(attachments)

    prompts: List[str] = []
    for prompt_index in range(target_count):
        section_item = section_items[prompt_index]
        attachment_name = str(section_item["attachment_name"])
        section_number = int(section_item["section_number"])
        section_excerpt = str(section_item.get("section_excerpt") or "").strip()
        section_kind = str(section_item.get("kind") or "docx")
        section_fallback_excerpt = (
            section_excerpt
            or f"第 {section_number} 个章节没有提取到可用文本，请尽量依据该章节的标题、结构或关键信息生成对应图像。"
        )
        section_instruction = (
            f"{user_instruction or 'Generate one image based on the uploaded Word document section.'}\n\n"
            f"Generate exactly one image that corresponds only to section {section_number} of the Word document "
            f"\"{attachment_name}\". Do not mix content from other sections."
        )
        section_attachment = AttachmentDescriptor(
            name=f"{attachment_name} - Section {section_number}",
            kind=section_kind,
            text_excerpt=section_fallback_excerpt,
        )

        try:
            prompt_result = await build_text_attachment_prompt(
                section_instruction,
                [section_attachment, *shared_text_attachments],
                api_key=api_key,
            )
            base_prompt = prompt_result.prompt
        except Exception as exc:
            logger.warning(
                "Failed to build section-matched Word prompt for {} section {}: {}",
                attachment_name,
                section_number,
                exc,
            )
            base_prompt = section_instruction

        prompt_sections = [
            (base_prompt or section_instruction).strip(),
            (
                f"Must correspond only to section {section_number} of the Word document "
                f"\"{attachment_name}\". Do not use content from other sections."
            ),
            (
                "Primary grounding content from the matched Word document section (must be reflected in the image):\n"
                f"[Attachment: {attachment_name} | Section {section_number}]\n"
                f"{_trim_attachment_text(section_fallback_excerpt, limit=1600)}"
            ),
        ]
        if shared_grounding:
            prompt_sections.append(
                "Shared grounding from other uploaded files:\n"
                f"{shared_grounding}"
            )
        prompts.append(
            _trim_attachment_text(
                "\n\n".join(section for section in prompt_sections if section),
                limit=settings.assistant_attachment_text_limit or 12000,
            )
        )

    return prompts


async def _build_chat_plan(
    *,
    messages: List[Dict[str, Any]],
    attachments: List[AttachmentDescriptor],
    route_decision: RequestRouteDecision,
    request_model: Optional[str],
    request_model_type: Optional[str],
    app_state,
) -> AssistantExecutionPlan:
    return AssistantExecutionPlan(
        mode="chat",
        confidence=route_decision.confidence,
        reasoning=route_decision.reasoning,
        source=route_decision.source,
        effective_model=await _resolve_chat_model_name(request_model, request_model_type, app_state),
        messages=_apply_attachments_to_chat_messages(messages, attachments),
        intent_type="chat",
        batch_count=1,
        metadata={
            "attachment_route": "chat" if attachments else "none",
            "attachment_count": len(attachments),
            "planning_basis": route_decision.planning_basis,
        },
    )


async def _build_image_plan(
    *,
    user_instruction: str,
    messages: List[Dict[str, Any]],
    attachments: List[AttachmentDescriptor],
    route_decision: RequestRouteDecision,
    request_model: Optional[str],
    request_model_type: Optional[str],
    app_state,
    api_key: Optional[str],
) -> AssistantExecutionPlan:
    contextual_user_instruction = await _build_contextual_image_instruction(
        user_instruction=user_instruction,
        messages=messages,
        api_key=api_key,
    )
    recent_context = _build_recent_conversation_context(messages)
    latest_user_prompt = (user_instruction or contextual_user_instruction or "").strip()
    effective_model = await _resolve_image_model_name(request_model, request_model_type, app_state)
    effective_system_prompt = _build_effective_image_system_prompt(
        attachments=attachments,
        model_name=effective_model,
    )

    def _wrap_image_prompt(prompt_text: str) -> str:
        return _compose_image_model_prompt(
            system_prompt=effective_system_prompt,
            recent_context=recent_context,
            user_prompt=latest_user_prompt,
            planned_prompt=prompt_text,
        )

    requested_batch_count = max(1, route_decision.batch_count or 1)
    pdf_page_items = _flatten_pdf_page_items(attachments)
    pdf_page_prompts = await _build_pdf_page_matched_prompts(
        user_instruction=contextual_user_instruction,
        attachments=attachments,
        requested_count=requested_batch_count,
        api_key=api_key,
    )
    word_section_items = _flatten_word_section_items(attachments)
    reference_image_sources = [
        attachment.source
        for attachment in attachments
        if attachment.kind == "image" and attachment.source
    ]
    word_section_prompts: List[str] = []
    if not pdf_page_prompts:
        word_section_prompts = await _build_word_section_matched_prompts(
            user_instruction=contextual_user_instruction,
            attachments=attachments,
            requested_count=requested_batch_count,
            api_key=api_key,
        )
    wrapped_batch_prompts: List[str] = []
    if pdf_page_prompts:
        wrapped_batch_prompts = [_wrap_image_prompt(prompt) for prompt in pdf_page_prompts]
        final_prompt = wrapped_batch_prompts[0]
        effective_batch_count = len(wrapped_batch_prompts)
        effective_intent_type = "batch_generate" if effective_batch_count > 1 else "single_generate"
    elif word_section_prompts:
        wrapped_batch_prompts = [_wrap_image_prompt(prompt) for prompt in word_section_prompts]
        final_prompt = wrapped_batch_prompts[0]
        effective_batch_count = len(wrapped_batch_prompts)
        effective_intent_type = "batch_generate" if effective_batch_count > 1 else "single_generate"
    else:
        raw_prompt = await _build_image_prompt_from_attachments(
            contextual_user_instruction,
            attachments,
            api_key=api_key,
        )
        final_prompt = _wrap_image_prompt(raw_prompt)
        effective_batch_count = route_decision.batch_count
        effective_intent_type = route_decision.intent_type

    # Keep original Chinese prompts for display/records
    original_prompt = final_prompt
    original_batch_prompts = list(wrapped_batch_prompts) if wrapped_batch_prompts else None

    prompts_to_translate = wrapped_batch_prompts if wrapped_batch_prompts else [final_prompt]
    translated_prompts = await _translate_prompts_to_english(prompts_to_translate, api_key)
    translation_applied = translated_prompts != prompts_to_translate
    if wrapped_batch_prompts:
        wrapped_batch_prompts = translated_prompts
        final_prompt = wrapped_batch_prompts[0]
    else:
        final_prompt = translated_prompts[0]

    attachment_text_count = sum(1 for attachment in attachments if attachment.text_excerpt)
    reference_analysis_count = sum(1 for attachment in attachments if attachment.visual_analysis)
    reference_ocr_count = sum(1 for attachment in attachments if attachment.ocr_text)
    reference_system_context = _build_reference_image_system_context(attachments)
    logger.info(
        "Prepared grounded image prompt: chars={}, attachments={}, text_attachments={}",
        len(final_prompt or ""),
        len(attachments),
        attachment_text_count,
    )
    return AssistantExecutionPlan(
        mode="image",
        confidence=route_decision.confidence,
        reasoning=route_decision.reasoning,
        source=route_decision.source,
        effective_model=effective_model,
        prompt=final_prompt,
        intent_type=effective_intent_type,
        batch_count=effective_batch_count,
        metadata={
            "attachment_route": "image" if attachments else "none",
            "attachment_count": len(attachments),
            "attachment_text_count": attachment_text_count,
            "reference_analysis_count": reference_analysis_count,
            "reference_ocr_count": reference_ocr_count,
            "reference_image_count": len(reference_image_sources),
            "reference_image_sources": reference_image_sources,
            "planning_basis": route_decision.planning_basis,
            "conversation_context_used": contextual_user_instruction != (user_instruction or "").strip(),
            "image_prompt_system_prompt_included": True,
            "image_prompt_system_prompt_language": "en",
            "image_prompt_context_included": bool(recent_context),
            "image_prompt_translated_to_english": translation_applied,
            "original_prompt": original_prompt,
            "original_batch_prompts": original_batch_prompts,
            "gemini_reference_system_grounding_included": bool(
                reference_system_context and _is_gemini_native_image_model_name(effective_model)
            ),
            "pdf_page_match_enabled": bool(pdf_page_prompts),
            "pdf_total_pages": len(pdf_page_items),
            "pdf_page_match_count": len(pdf_page_prompts),
            "word_section_match_enabled": bool(word_section_prompts),
            "word_total_sections": len(word_section_items),
            "word_section_match_count": len(word_section_prompts),
            **({"_batch_prompts": wrapped_batch_prompts} if len(wrapped_batch_prompts) > 1 else {}),
        },
    )


async def _load_attachments_node(state: AssistantExecutionState) -> Dict[str, object]:
    db_manager = state.get("db_manager")
    if db_manager is None:
        raise ValueError("db_manager is required for attachment loading")
    attachments = await _load_attachment_descriptors(
        state.get("files"),
        db_manager,
        state.get("api_key"),
    )
    return {"attachments": [attachment.model_dump() for attachment in attachments]}


async def _route_request_node(state: AssistantExecutionState) -> Dict[str, object]:
    attachments = [AttachmentDescriptor.model_validate(item) for item in state.get("attachments", [])]
    decision = await _decide_execution_route(
        attachments=attachments,
        messages=state.get("messages", []),
        user_instruction=state.get("user_instruction", ""),
        request_model=state.get("request_model"),
        request_model_type=state.get("request_model_type"),
        requested_count=state.get("requested_count"),
        app_state=state.get("app_state"),
        api_key=state.get("api_key"),
    )
    return {"route_decision": decision.model_dump()}


def _select_branch(state: AssistantExecutionState) -> str:
    decision = state.get("route_decision") or {}
    return "prepare_image" if str(decision.get("route")) == "image" else "prepare_chat"


async def _prepare_chat_node(state: AssistantExecutionState) -> Dict[str, object]:
    attachments = [AttachmentDescriptor.model_validate(item) for item in state.get("attachments", [])]
    route_decision = RequestRouteDecision.model_validate(state.get("route_decision") or {})
    plan = await _build_chat_plan(
        messages=state.get("messages", []),
        attachments=attachments,
        route_decision=route_decision,
        request_model=state.get("request_model"),
        request_model_type=state.get("request_model_type"),
        app_state=state.get("app_state"),
    )
    return {"execution_plan": plan.model_dump()}


async def _prepare_image_node(state: AssistantExecutionState) -> Dict[str, object]:
    attachments = [AttachmentDescriptor.model_validate(item) for item in state.get("attachments", [])]
    route_decision = RequestRouteDecision.model_validate(state.get("route_decision") or {})
    plan = await _build_image_plan(
        user_instruction=state.get("user_instruction", ""),
        messages=state.get("messages", []),
        attachments=attachments,
        route_decision=route_decision,
        request_model=state.get("request_model"),
        request_model_type=state.get("request_model_type"),
        app_state=state.get("app_state"),
        api_key=state.get("api_key"),
    )
    return {"execution_plan": plan.model_dump()}


def _build_execution_graph():
    if not LANGCHAIN_ASSISTANT_AVAILABLE or StateGraph is None:
        return None

    builder = StateGraph(AssistantExecutionState)
    builder.add_node("load_attachments", _load_attachments_node)
    builder.add_node("route_request", _route_request_node)
    builder.add_node("prepare_chat", _prepare_chat_node)
    builder.add_node("prepare_image", _prepare_image_node)
    builder.add_edge(START, "load_attachments")
    builder.add_edge("load_attachments", "route_request")
    builder.add_conditional_edges(
        "route_request",
        _select_branch,
        {
            "prepare_chat": "prepare_chat",
            "prepare_image": "prepare_image",
        },
    )
    builder.add_edge("prepare_chat", END)
    builder.add_edge("prepare_image", END)
    return builder.compile()


_ASSISTANT_EXECUTION_GRAPH = _build_execution_graph()


async def _fallback_execution_plan(
    *,
    messages: List[Dict[str, Any]],
    files: Optional[List[str]],
    user_instruction: str,
    request_model: Optional[str],
    request_model_type: Optional[str],
    requested_count: Optional[int],
    db_manager,
    app_state,
    api_key: Optional[str],
) -> AssistantExecutionPlan:
    attachments = await _load_attachment_descriptors(files, db_manager, api_key)
    route_decision = await _decide_execution_route(
        attachments=attachments,
        messages=messages,
        user_instruction=user_instruction,
        request_model=request_model,
        request_model_type=request_model_type,
        requested_count=requested_count,
        app_state=app_state,
        api_key=api_key,
    )
    if route_decision.route == "image":
        return await _build_image_plan(
            user_instruction=user_instruction,
            messages=messages,
            attachments=attachments,
            route_decision=route_decision,
            request_model=request_model,
            request_model_type=request_model_type,
            app_state=app_state,
            api_key=api_key,
        )
    return await _build_chat_plan(
        messages=messages,
        attachments=attachments,
        route_decision=route_decision,
        request_model=request_model,
        request_model_type=request_model_type,
        app_state=app_state,
    )


async def plan_assistant_execution(
    *,
    messages: List[Dict[str, Any]],
    files: Optional[List[str]],
    user_instruction: str,
    request_model: Optional[str],
    request_model_type: Optional[str],
    requested_count: Optional[int],
    db_manager,
    app_state,
    api_key: Optional[str] = None,
) -> AssistantExecutionPlan:
    if _ASSISTANT_EXECUTION_GRAPH is None:
        return await _fallback_execution_plan(
            messages=messages,
            files=files,
            user_instruction=user_instruction,
            request_model=request_model,
            request_model_type=request_model_type,
            requested_count=requested_count,
            db_manager=db_manager,
            app_state=app_state,
            api_key=api_key,
        )

    try:
        result = await _ASSISTANT_EXECUTION_GRAPH.ainvoke(
            {
                "messages": messages,
                "files": files or [],
                "user_instruction": user_instruction or "",
                "request_model": request_model,
                "request_model_type": request_model_type,
                "requested_count": requested_count,
                "db_manager": db_manager,
                "app_state": app_state,
                "api_key": api_key,
            }
        )
        return AssistantExecutionPlan.model_validate(result["execution_plan"])
    except Exception as exc:
        logger.warning("Assistant execution graph failed, falling back to direct planner: {}", exc)
        return await _fallback_execution_plan(
            messages=messages,
            files=files,
            user_instruction=user_instruction,
            request_model=request_model,
            request_model_type=request_model_type,
            requested_count=requested_count,
            db_manager=db_manager,
            app_state=app_state,
            api_key=api_key,
        )
