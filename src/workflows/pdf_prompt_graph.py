"""Convert PDF content into image-generation prompts with LangChain/LangGraph."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import pdfplumber
from pydantic import BaseModel, Field

from ..config.settings import settings

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph

    LANGCHAIN_GRAPH_AVAILABLE = True
except ImportError:
    PyPDFLoader = None  # type: ignore[assignment]
    ChatOpenAI = None  # type: ignore[assignment]
    StateGraph = None  # type: ignore[assignment]
    START = END = None  # type: ignore[assignment]
    LANGCHAIN_GRAPH_AVAILABLE = False


class PDFPageBrief(BaseModel):
    """Structured visual brief extracted from a PDF page."""

    page_number: int = Field(..., description="1-based page number.")
    summary: str = Field(..., description="Concise summary of the page.")
    image_prompt: str = Field(..., description="Visual prompt grounded in this page.")
    key_visuals: List[str] = Field(default_factory=list, description="Concrete visual elements.")
    style_cues: List[str] = Field(default_factory=list, description="Style/layout cues worth preserving.")
    constraints: List[str] = Field(default_factory=list, description="Grounding constraints from the page.")
    include_in_final: bool = Field(
        True,
        description="Whether this page should influence the final image prompt.",
    )


class PDFAggregatedPrompt(BaseModel):
    """Final prompt synthesized from page-level briefs."""

    document_summary: str = Field(..., description="High-level summary of the PDF for logging/debug.")
    final_prompt: str = Field(..., description="Final prompt to pass to the image model.")
    negative_prompt: Optional[str] = Field(
        None,
        description="Optional negative prompt that prevents unsupported details.",
    )
    style: Optional[str] = Field(None, description="Optional style hint.")


class PDFPromptResult(BaseModel):
    """Output produced by the PDF workflow."""

    prompt: str
    summary: str
    page_prompts: List[str] = Field(default_factory=list)
    page_count: int = 0
    negative_prompt: Optional[str] = None
    style: Optional[str] = None
    source: str = "fallback"


class PDFPromptState(dict):
    """Mutable graph state for PDF prompt generation."""


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "")).strip()


def _trim_text(text: str, limit: int) -> str:
    text = _normalize_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _build_model(api_key: Optional[str] = None) -> "ChatOpenAI":
    if not LANGCHAIN_GRAPH_AVAILABLE or ChatOpenAI is None:
        raise RuntimeError("LangChain/LangGraph is not installed.")

    base_url = settings.openai_base_url or settings.relay_base_url or None
    if base_url and not base_url.rstrip("/").endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"

    key = (api_key or "").strip()
    if not key:
        raise RuntimeError("Missing API key for LangChain PDF prompt workflow.")

    return ChatOpenAI(
        model=settings.langchain_pdf_prompt_model,
        temperature=0,
        api_key=key,
        base_url=base_url,
    )


def _load_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    max_pages = settings.langchain_pdf_max_pages
    char_limit = settings.langchain_pdf_page_char_limit

    pages: List[Dict[str, Any]] = []

    if LANGCHAIN_GRAPH_AVAILABLE and PyPDFLoader is not None:
        try:
            loader = PyPDFLoader(file_path, mode="page")
            docs = loader.load()
            for index, doc in enumerate(docs[:max_pages], start=1):
                text = _trim_text(getattr(doc, "page_content", ""), char_limit)
                if not text:
                    continue
                pages.append(
                    {
                        "page_number": index,
                        "page_content": text,
                        "metadata": dict(getattr(doc, "metadata", {}) or {}),
                    }
                )
        except Exception:
            pages = []

    if pages:
        return pages

    with pdfplumber.open(file_path) as pdf:
        for index, page in enumerate(pdf.pages[:max_pages], start=1):
            text = _trim_text(page.extract_text() or "", char_limit)
            if not text:
                continue
            pages.append(
                {
                    "page_number": index,
                    "page_content": text,
                    "metadata": {
                        "source": file_path,
                        "page": index - 1,
                        "total_pages": len(pdf.pages),
                    },
                }
            )

    return pages


def _fallback_result(pages: List[Dict[str, Any]], user_instruction: str = "") -> PDFPromptResult:
    snippets = [
        f"Page {page['page_number']}: {page['page_content']}"
        for page in pages[: max(1, min(3, len(pages)))]
    ]
    summary = "\n".join(snippets) if snippets else "Empty PDF or no extractable text."
    if user_instruction:
        prompt = (
            f"{user_instruction}\n\n"
            f"Base the image strictly on this PDF content: {summary}"
        )
    else:
        prompt = f"Create an image strictly grounded in this PDF content: {summary}"
    return PDFPromptResult(
        prompt=prompt,
        summary=summary,
        page_prompts=[page["page_content"] for page in pages],
        page_count=len(pages),
        source="fallback",
    )


async def _load_pages_node(state: PDFPromptState) -> Dict[str, Any]:
    pages = _load_pdf_pages(state["file_path"])
    return {"pages": pages}


async def _extract_page_briefs_node(state: PDFPromptState) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = state.get("pages", [])
    if not pages:
        return {"page_briefs": [], "page_prompts": []}

    if not LANGCHAIN_GRAPH_AVAILABLE:
        page_prompts = [page["page_content"] for page in pages]
        briefs = [
            PDFPageBrief(
                page_number=page["page_number"],
                summary=page["page_content"],
                image_prompt=page["page_content"],
                include_in_final=True,
            ).model_dump()
            for page in pages
        ]
        return {"page_briefs": briefs, "page_prompts": page_prompts}

    llm = _build_model(state.get("api_key"))
    structured = llm.with_structured_output(PDFPageBrief, method="json_schema")
    user_instruction = (state.get("user_instruction") or "").strip()

    page_briefs: List[Dict[str, Any]] = []
    page_prompts: List[str] = []

    system_prompt = (
        "You extract grounded visual briefs from PDF pages for downstream image generation. "
        "Keep only details supported by the page. Preserve concrete people, objects, products, "
        "actions, numbers, branding cues, spatial relationships, and design style. "
        "Do not invent missing facts. If a page is mostly boilerplate, legal text, or table data "
        "with weak visual value, set include_in_final to false."
    )

    for page in pages:
        human_prompt = (
            f"User instruction: {user_instruction or 'No extra instruction.'}\n"
            f"Page number: {page['page_number']}\n"
            f"PDF page text:\n{page['page_content']}"
        )
        brief = await structured.ainvoke(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        )
        page_briefs.append(brief.model_dump())
        if brief.include_in_final and brief.image_prompt:
            page_prompts.append(brief.image_prompt)

    return {"page_briefs": page_briefs, "page_prompts": page_prompts}


async def _synthesize_prompt_node(state: PDFPromptState) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = state.get("pages", [])
    page_briefs: List[Dict[str, Any]] = state.get("page_briefs", [])
    page_prompts: List[str] = state.get("page_prompts", [])

    if not pages:
        result = _fallback_result([], state.get("user_instruction", ""))
        return {"result": result.model_dump()}

    if not LANGCHAIN_GRAPH_AVAILABLE:
        result = _fallback_result(pages, state.get("user_instruction", ""))
        return {"result": result.model_dump()}

    llm = _build_model(state.get("api_key"))
    structured = llm.with_structured_output(PDFAggregatedPrompt, method="json_schema")
    user_instruction = (state.get("user_instruction") or "").strip()

    system_prompt = (
        "You combine PDF page briefs into one faithful image-generation prompt. "
        "The result must stay grounded in the PDF. Synthesize the most important subject, "
        "scene, composition, and design cues. If the PDF is mostly textual, convert the key "
        "ideas into a visual concept instead of copying paragraphs. Keep the final_prompt concise "
        "but specific enough for an image model."
    )
    human_prompt = (
        f"User instruction: {user_instruction or 'No extra instruction.'}\n"
        f"Page briefs:\n{page_briefs}\n\n"
        f"Page-level prompt candidates:\n{page_prompts}"
    )

    aggregated = await structured.ainvoke(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )

    result = PDFPromptResult(
        prompt=aggregated.final_prompt,
        summary=aggregated.document_summary,
        page_prompts=page_prompts,
        page_count=len(pages),
        negative_prompt=aggregated.negative_prompt,
        style=aggregated.style,
        source="langgraph",
    )
    return {"result": result.model_dump()}


def _build_graph():
    if not LANGCHAIN_GRAPH_AVAILABLE or StateGraph is None:
        return None

    builder = StateGraph(PDFPromptState)
    builder.add_node("load_pages", _load_pages_node)
    builder.add_node("extract_page_briefs", _extract_page_briefs_node)
    builder.add_node("synthesize_prompt", _synthesize_prompt_node)
    builder.add_edge(START, "load_pages")
    builder.add_edge("load_pages", "extract_page_briefs")
    builder.add_edge("extract_page_briefs", "synthesize_prompt")
    builder.add_edge("synthesize_prompt", END)
    return builder.compile()


_PDF_PROMPT_GRAPH = _build_graph()


async def build_pdf_prompt(
    file_path: str,
    user_instruction: str = "",
    api_key: Optional[str] = None,
) -> PDFPromptResult:
    """Generate a grounded image prompt from a PDF file."""

    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    if _PDF_PROMPT_GRAPH is None:
        return _fallback_result(_load_pdf_pages(file_path), user_instruction)

    result = await _PDF_PROMPT_GRAPH.ainvoke(
        {
            "file_path": file_path,
            "user_instruction": user_instruction or "",
            "api_key": api_key,
        }
    )
    return PDFPromptResult.model_validate(result["result"])
