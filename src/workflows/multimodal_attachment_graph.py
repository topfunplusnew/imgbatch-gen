"""LangChain/LangGraph helpers for attachment routing and grounded prompts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from loguru import logger
from pydantic import BaseModel, Field

from ..config.settings import settings

try:
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph

    LANGCHAIN_MULTIMODAL_AVAILABLE = True
except ImportError:
    ChatOpenAI = None  # type: ignore[assignment]
    StateGraph = None  # type: ignore[assignment]
    START = END = None  # type: ignore[assignment]
    LANGCHAIN_MULTIMODAL_AVAILABLE = False


class AttachmentDescriptor(BaseModel):
    name: str
    kind: str = Field(..., description="pdf/docx/doc/image/unknown")
    source: Optional[str] = None
    text_excerpt: Optional[str] = None


class AttachmentRouteDecision(BaseModel):
    route: str = Field(..., description="chat or image")
    confidence: float = Field(0.0, description="0-1 confidence")
    reasoning: str = Field("", description="Why this route was selected")
    source: str = Field("fallback", description="Workflow source")


class TextAttachmentPromptResult(BaseModel):
    prompt: str
    summary: str
    source: str = "fallback"


class AttachmentRouteState(TypedDict, total=False):
    """Mutable graph state for attachment routing."""

    user_instruction: str
    attachments: List[Dict[str, Any]]
    api_key: Optional[str]
    model_hint: Optional[str]
    route_decision: Dict[str, Any]
    prompt_result: Dict[str, Any]


def _has_llm_credentials(api_key: Optional[str] = None) -> bool:
    return bool(api_key or settings.relay_api_key or settings.openai_api_key)


def _get_default_planner_model() -> str:
    return settings.assistant_planner_model or settings.langchain_pdf_prompt_model or settings.assistant_text_model or "gpt-4o-mini"


def _build_model(api_key: Optional[str] = None) -> "ChatOpenAI":
    if not LANGCHAIN_MULTIMODAL_AVAILABLE or ChatOpenAI is None:
        raise RuntimeError("LangChain/LangGraph is not installed.")

    base_url = settings.openai_base_url or settings.relay_base_url or None
    if base_url and not base_url.rstrip("/").endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    key = api_key or settings.relay_api_key or settings.openai_api_key
    if not key:
        raise RuntimeError("Missing API key for attachment workflow.")

    return ChatOpenAI(
        model=_get_default_planner_model(),
        temperature=0,
        api_key=key,
        base_url=base_url,
    )


def _fallback_route(
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    model_hint: Optional[str] = None,
) -> AttachmentRouteDecision:
    text = (user_instruction or "").lower()
    kinds = {attachment.kind for attachment in attachments}

    chat_keywords = [
        "总结", "摘要", "概括", "解释", "解读", "分析", "提取", "翻译", "问答",
        "阅读", "看看", "帮我看", "内容", "要点", "关键信息", "讲了什么", "什么意思",
        "梳理", "整理", "review", "summarize", "summary", "explain", "analyze",
        "describe", "what is in",
    ]
    image_keywords = [
        "生图", "生成图", "生成图片", "生成图像", "画", "绘制", "插画", "海报", "封面",
        "配图", "视觉稿", "效果图", "渲染", "render", "draw", "image", "poster",
        "illustration", "convert to image", "转成图", "转图片", "每页转成图",
        "类似", "风格图", "配一张图",
    ]

    chat_score = sum(1 for keyword in chat_keywords if keyword in text)
    image_score = sum(1 for keyword in image_keywords if keyword in text)

    if model_hint == "chat":
        chat_score += 1
    elif model_hint == "image":
        image_score += 1

    if "image" in kinds and not {"pdf", "docx", "doc"} & kinds and image_score > 0:
        image_score += 1

    if image_score > chat_score and image_score >= 2:
        return AttachmentRouteDecision(
            route="image",
            confidence=min(0.95, 0.55 + image_score * 0.1),
            reasoning="Fallback rules detected explicit image-generation intent from the request.",
            source="fallback",
        )

    return AttachmentRouteDecision(
        route="chat",
        confidence=min(0.98, 0.72 + chat_score * 0.08),
        reasoning="Fallback rules defaulted to document/image understanding instead of generation.",
        source="fallback",
    )


def _fallback_prompt(
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
) -> TextAttachmentPromptResult:
    excerpts = [
        f"{attachment.name}: {attachment.text_excerpt}"
        for attachment in attachments
        if attachment.text_excerpt
    ]
    summary = "\n".join(excerpts[:3]) if excerpts else "No extractable text was available."
    if user_instruction:
        prompt = (
            f"{user_instruction}\n\n"
            f"Base the image strictly on these attachment details: {summary}"
        )
    else:
        prompt = f"Create an image strictly grounded in these attachment details: {summary}"
    return TextAttachmentPromptResult(prompt=prompt, summary=summary, source="fallback")


async def _route_request_node(state: AttachmentRouteState) -> Dict[str, object]:
    attachments = [AttachmentDescriptor.model_validate(item) for item in state.get("attachments", [])]
    if not attachments:
        return {
            "route_decision": AttachmentRouteDecision(
                route="chat",
                confidence=1.0,
                reasoning="No attachments were provided.",
                source="fallback",
            ).model_dump()
        }

    if not LANGCHAIN_MULTIMODAL_AVAILABLE:
        return {
            "route_decision": _fallback_route(
                state.get("user_instruction", ""),
                attachments,
                state.get("model_hint"),
            ).model_dump()
        }

    llm = _build_model(state.get("api_key"))
    structured = llm.with_structured_output(AttachmentRouteDecision, method="function_calling")
    attachment_lines = []
    for attachment in attachments:
        excerpt = (attachment.text_excerpt or "").strip()
        attachment_lines.append(
            f"- name={attachment.name}, kind={attachment.kind}, excerpt={excerpt[:800] or 'n/a'}"
        )

    decision = await structured.ainvoke(
        [
            (
                "system",
                "You route attachment-based requests. "
                "Choose route=chat when the user wants explanation, summary, QA, extraction, or interpretation of attachments. "
                "Choose route=image only when the user explicitly asks to generate, draw, render, illustrate, or create images based on attachments. "
                "When the request is ambiguous, prefer chat.",
            ),
            (
                "human",
                f"User instruction: {state.get('user_instruction', '') or 'None'}\n"
                f"Model hint: {state.get('model_hint', '') or 'none'}\n"
                f"Attachments:\n" + "\n".join(attachment_lines),
            ),
        ]
    )
    decision.source = "langgraph"
    return {"route_decision": decision.model_dump()}


async def _build_prompt_node(state: AttachmentRouteState) -> Dict[str, object]:
    attachments = [AttachmentDescriptor.model_validate(item) for item in state.get("attachments", [])]
    if not attachments:
        return {"prompt_result": _fallback_prompt(state.get("user_instruction", ""), attachments).model_dump()}

    text_attachments = [attachment for attachment in attachments if attachment.text_excerpt]
    if not text_attachments:
        return {"prompt_result": _fallback_prompt(state.get("user_instruction", ""), attachments).model_dump()}

    if not LANGCHAIN_MULTIMODAL_AVAILABLE:
        return {"prompt_result": _fallback_prompt(state.get("user_instruction", ""), text_attachments).model_dump()}

    llm = _build_model(state.get("api_key"))
    structured = llm.with_structured_output(TextAttachmentPromptResult, method="function_calling")
    attachment_lines = []
    for attachment in text_attachments:
        attachment_lines.append(
            f"- name={attachment.name}, kind={attachment.kind}, excerpt={attachment.text_excerpt[:1600]}"
        )

    result = await structured.ainvoke(
        [
            (
                "system",
                "You convert text-heavy attachments into a grounded image-generation prompt. "
                "Use only facts supported by the attachments. Preserve important entities, products, numbers, "
                "layout cues, and style signals. Do not invent missing details.",
            ),
            (
                "human",
                f"User instruction: {state.get('user_instruction', '') or 'None'}\n"
                f"Attachments:\n" + "\n".join(attachment_lines),
            ),
        ]
    )
    result.source = "langgraph"
    return {"prompt_result": result.model_dump()}


def _route_graph():
    if not LANGCHAIN_MULTIMODAL_AVAILABLE or StateGraph is None:
        return None

    builder = StateGraph(AttachmentRouteState)
    builder.add_node("route_request", _route_request_node)
    builder.add_edge(START, "route_request")
    builder.add_edge("route_request", END)
    return builder.compile()


def _prompt_graph():
    if not LANGCHAIN_MULTIMODAL_AVAILABLE or StateGraph is None:
        return None

    builder = StateGraph(AttachmentRouteState)
    builder.add_node("build_prompt", _build_prompt_node)
    builder.add_edge(START, "build_prompt")
    builder.add_edge("build_prompt", END)
    return builder.compile()


_ATTACHMENT_ROUTE_GRAPH = _route_graph()
_ATTACHMENT_PROMPT_GRAPH = _prompt_graph()


async def build_attachment_route(
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    api_key: Optional[str] = None,
    model_hint: Optional[str] = None,
) -> AttachmentRouteDecision:
    if _ATTACHMENT_ROUTE_GRAPH is None or not _has_llm_credentials(api_key):
        return _fallback_route(user_instruction, attachments, model_hint)
    try:
        result = await _ATTACHMENT_ROUTE_GRAPH.ainvoke(
            {
                "user_instruction": user_instruction or "",
                "attachments": [attachment.model_dump() for attachment in attachments],
                "api_key": api_key,
                "model_hint": model_hint,
            }
        )
        return AttachmentRouteDecision.model_validate(result["route_decision"])
    except Exception as exc:
        logger.warning("Attachment route graph failed, falling back to rules: {}", exc)
        return _fallback_route(user_instruction, attachments, model_hint)


async def build_text_attachment_prompt(
    user_instruction: str,
    attachments: List[AttachmentDescriptor],
    api_key: Optional[str] = None,
) -> TextAttachmentPromptResult:
    if _ATTACHMENT_PROMPT_GRAPH is None or not _has_llm_credentials(api_key):
        return _fallback_prompt(user_instruction, attachments)
    try:
        result = await _ATTACHMENT_PROMPT_GRAPH.ainvoke(
            {
                "user_instruction": user_instruction or "",
                "attachments": [attachment.model_dump() for attachment in attachments],
                "api_key": api_key,
            }
        )
        return TextAttachmentPromptResult.model_validate(result["prompt_result"])
    except Exception as exc:
        logger.warning("Attachment prompt graph failed, falling back to heuristic prompt: {}", exc)
        return _fallback_prompt(user_instruction, attachments)
