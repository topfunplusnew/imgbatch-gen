from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.workflows import assistant_execution_graph as graph
from src.workflows.multimodal_attachment_graph import (
    AttachmentDescriptor,
    AttachmentRouteDecision,
    TextAttachmentPromptResult,
)


def test_normalize_messages_strips_placeholder_assistant_messages():
    messages = [
        {"role": "assistant", "content": "图像生成完成！"},
        {"role": "assistant", "content": "抱歉，对话请求失败，请稍后重试。"},
        {"role": "assistant", "content": "正在上传文件... (1/1) - 100%"},
        {"role": "assistant", "content": "正常回复"},
        {"role": "user", "content": "pdf里有什么内容？"},
    ]

    assert graph._normalize_messages(messages) == [
        {"role": "assistant", "content": "正常回复"},
        {"role": "user", "content": "pdf里有什么内容？"},
    ]


@pytest.mark.asyncio
async def test_plan_assistant_execution_uses_chat_model_for_attachment_chat(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="sample.pdf",
                kind="pdf",
                source="http://example.com/sample.pdf",
                text_excerpt="这是准考证内容。",
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="chat",
            confidence=0.93,
            reasoning="The request asks for document understanding.",
            source="langgraph",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)

    plan = await graph.plan_assistant_execution(
        messages=[
            {"role": "user", "content": "根据pdf内容生图"},
            {"role": "assistant", "content": "图像生成完成！"},
            {"role": "user", "content": "pdf里有什么内容？"},
            {"role": "assistant", "content": "正在上传文件... (1/1) - 100%"},
        ],
        files=["file-1"],
        user_instruction="pdf里有什么内容？",
        request_model="doubao-seedream-5-0-260128",
        request_model_type="image",
        requested_count=1,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    expected_chat_model = (
        settings.assistant_text_model
        or settings.langchain_pdf_prompt_model
        or settings.openai_model
        or "gpt-4o-mini"
    )

    assert plan.mode == "chat"
    assert plan.intent_type == "chat"
    assert plan.source == "langgraph"
    assert plan.effective_model == expected_chat_model
    assert all(message["content"] != "图像生成完成！" for message in plan.messages)
    assert all(not str(message["content"]).startswith("正在上传文件") for message in plan.messages)
    assert "[Attachment: sample.pdf]" in str(plan.messages[-1]["content"])


@pytest.mark.asyncio
async def test_plan_assistant_execution_builds_page_matched_pdf_prompts(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="catalog.pdf",
                kind="pdf",
                source="http://example.com/catalog.pdf",
                text_excerpt="[Page 1]\n第一页内容\n\n[Page 2]\n第二页内容\n\n[Page 3]\n第三页内容",
                page_excerpts=["第一页内容", "第二页内容", "第三页内容"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="image",
            confidence=0.91,
            reasoning="The request explicitly asks for image generation from the PDF.",
            source="langgraph",
        )

    async def fake_build_text_attachment_prompt(user_instruction, attachments, api_key=None):
        primary = attachments[0]
        return TextAttachmentPromptResult(
            prompt=f"Prompt for {primary.name}: {primary.text_excerpt}",
            summary=primary.text_excerpt or "",
            source="test",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)
    monkeypatch.setattr(graph, "build_text_attachment_prompt", fake_build_text_attachment_prompt)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "根据PDF生成2张图"}],
        files=["file-1"],
        user_instruction="根据PDF生成2张图",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=2,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    assert plan.mode == "image"
    assert plan.intent_type == "batch_generate"
    assert plan.batch_count == 2
    assert plan.metadata["pdf_page_match_enabled"] is True
    assert plan.metadata["pdf_total_pages"] == 3
    assert plan.metadata["pdf_page_match_count"] == 2
    assert len(plan.metadata["_batch_prompts"]) == 2
    assert "第一页内容" in plan.metadata["_batch_prompts"][0]
    assert "第二页内容" in plan.metadata["_batch_prompts"][1]
    assert "第三页内容" not in plan.metadata["_batch_prompts"][0]
    assert "第三页内容" not in plan.metadata["_batch_prompts"][1]


@pytest.mark.asyncio
async def test_plan_assistant_execution_matches_all_pdf_pages_when_count_is_equal(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="catalog.pdf",
                kind="pdf",
                source="http://example.com/catalog.pdf",
                text_excerpt="[Page 1]\n第一页内容\n\n[Page 2]\n第二页内容\n\n[Page 3]\n第三页内容",
                page_excerpts=["第一页内容", "第二页内容", "第三页内容"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="image",
            confidence=0.91,
            reasoning="The request explicitly asks for image generation from the PDF.",
            source="langgraph",
        )

    async def fake_build_text_attachment_prompt(user_instruction, attachments, api_key=None):
        primary = attachments[0]
        return TextAttachmentPromptResult(
            prompt=f"Prompt for {primary.name}: {primary.text_excerpt}",
            summary=primary.text_excerpt or "",
            source="test",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)
    monkeypatch.setattr(graph, "build_text_attachment_prompt", fake_build_text_attachment_prompt)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "根据PDF生成3张图"}],
        files=["file-1"],
        user_instruction="根据PDF生成3张图",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=3,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    assert plan.mode == "image"
    assert plan.intent_type == "batch_generate"
    assert plan.batch_count == 3
    assert plan.metadata["pdf_page_match_enabled"] is True
    assert plan.metadata["pdf_total_pages"] == 3
    assert plan.metadata["pdf_page_match_count"] == 3
    assert len(plan.metadata["_batch_prompts"]) == 3
    assert "第一页内容" in plan.metadata["_batch_prompts"][0]
    assert "第二页内容" in plan.metadata["_batch_prompts"][1]
    assert "第三页内容" in plan.metadata["_batch_prompts"][2]


@pytest.mark.asyncio
async def test_plan_assistant_execution_expands_pdf_page_matching_to_requested_count(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="catalog.pdf",
                kind="pdf",
                source="http://example.com/catalog.pdf",
                text_excerpt="[Page 1]\n第一页内容\n\n[Page 2]\n第二页内容",
                page_excerpts=["第一页内容", "第二页内容"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="image",
            confidence=0.91,
            reasoning="The request explicitly asks for image generation from the PDF.",
            source="langgraph",
        )

    async def fake_build_text_attachment_prompt(user_instruction, attachments, api_key=None):
        primary = attachments[0]
        return TextAttachmentPromptResult(
            prompt=f"Prompt for {primary.name}: {primary.text_excerpt}",
            summary=primary.text_excerpt or "",
            source="test",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)
    monkeypatch.setattr(graph, "build_text_attachment_prompt", fake_build_text_attachment_prompt)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "根据PDF生成5张图"}],
        files=["file-1"],
        user_instruction="根据PDF生成5张图",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=5,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    assert plan.mode == "image"
    assert plan.intent_type == "batch_generate"
    assert plan.batch_count == 5
    assert plan.metadata["pdf_page_match_count"] == 5
    assert len(plan.metadata["_batch_prompts"]) == 5
    assert "第一页内容" in plan.metadata["_batch_prompts"][0]
    assert "第二页内容" in plan.metadata["_batch_prompts"][1]
    assert "variation 2" in plan.metadata["_batch_prompts"][2]
    assert "variation 3" in plan.metadata["_batch_prompts"][4]


@pytest.mark.asyncio
async def test_plan_assistant_execution_uses_chat_model_for_word_attachment_chat(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="requirements.docx",
                kind="docx",
                source="http://example.com/requirements.docx",
                text_excerpt="[Section 1]\n品牌主色是森林绿。\n\n[Section 2]\n首页需要突出新品活动。",
                page_excerpts=["品牌主色是森林绿。", "首页需要突出新品活动。"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="chat",
            confidence=0.94,
            reasoning="The request asks for understanding the uploaded Word document.",
            source="langgraph",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "这个 Word 里讲了什么？"}],
        files=["file-1"],
        user_instruction="这个 Word 里讲了什么？",
        request_model="gpt-4o-mini",
        request_model_type="chat",
        requested_count=1,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    expected_chat_model = (
        settings.assistant_text_model
        or settings.langchain_pdf_prompt_model
        or settings.openai_model
        or "gpt-4o-mini"
    )

    assert plan.mode == "chat"
    assert plan.intent_type == "chat"
    assert plan.effective_model == expected_chat_model
    assert "[Attachment: requirements.docx]" in str(plan.messages[-1]["content"])
    assert "森林绿" in str(plan.messages[-1]["content"])


@pytest.mark.asyncio
async def test_plan_assistant_execution_builds_word_section_matched_prompts(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="requirements.docx",
                kind="docx",
                source="http://example.com/requirements.docx",
                text_excerpt="[Section 1]\n品牌主色是森林绿。\n\n[Section 2]\n首页需要突出新品活动。\n\n[Section 3]\n落地页强调会员权益。",
                page_excerpts=["品牌主色是森林绿。", "首页需要突出新品活动。", "落地页强调会员权益。"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="image",
            confidence=0.92,
            reasoning="The request explicitly asks to generate images from the uploaded Word document.",
            source="langgraph",
        )

    async def fake_build_text_attachment_prompt(user_instruction, attachments, api_key=None):
        primary = attachments[0]
        return TextAttachmentPromptResult(
            prompt=f"Prompt for {primary.name}: {primary.text_excerpt}",
            summary=primary.text_excerpt or "",
            source="test",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)
    monkeypatch.setattr(graph, "build_text_attachment_prompt", fake_build_text_attachment_prompt)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "根据这个 Word 生成 2 张图"}],
        files=["file-1"],
        user_instruction="根据这个 Word 生成 2 张图",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=2,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    assert plan.mode == "image"
    assert plan.intent_type == "batch_generate"
    assert plan.batch_count == 2
    assert plan.metadata["word_section_match_enabled"] is True
    assert plan.metadata["word_total_sections"] == 3
    assert plan.metadata["word_section_match_count"] == 2
    assert len(plan.metadata["_batch_prompts"]) == 2
    assert "森林绿" in plan.metadata["_batch_prompts"][0]
    assert "新品活动" in plan.metadata["_batch_prompts"][1]
    assert "会员权益" not in plan.metadata["_batch_prompts"][0]


@pytest.mark.asyncio
async def test_plan_assistant_execution_expands_word_section_matching_to_requested_count(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return [
            AttachmentDescriptor(
                name="requirements.docx",
                kind="docx",
                source="http://example.com/requirements.docx",
                text_excerpt="[Section 1]\n品牌主色是森林绿。\n\n[Section 2]\n首页需要突出新品活动。",
                page_excerpts=["品牌主色是森林绿。", "首页需要突出新品活动。"],
            )
        ]

    async def fake_build_attachment_route(user_instruction, attachments, api_key=None, model_hint=None):
        return AttachmentRouteDecision(
            route="image",
            confidence=0.92,
            reasoning="The request explicitly asks to generate images from the uploaded Word document.",
            source="langgraph",
        )

    async def fake_build_text_attachment_prompt(user_instruction, attachments, api_key=None):
        primary = attachments[0]
        return TextAttachmentPromptResult(
            prompt=f"Prompt for {primary.name}: {primary.text_excerpt}",
            summary=primary.text_excerpt or "",
            source="test",
        )

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)
    monkeypatch.setattr(graph, "build_attachment_route", fake_build_attachment_route)
    monkeypatch.setattr(graph, "build_text_attachment_prompt", fake_build_text_attachment_prompt)

    plan = await graph.plan_assistant_execution(
        messages=[{"role": "user", "content": "根据这个 Word 生成 4 张图"}],
        files=["file-1"],
        user_instruction="根据这个 Word 生成 4 张图",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=4,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key="test-key",
    )

    assert plan.mode == "image"
    assert plan.intent_type == "batch_generate"
    assert plan.batch_count == 4
    assert plan.metadata["word_section_match_enabled"] is True
    assert plan.metadata["word_total_sections"] == 2
    assert plan.metadata["word_section_match_count"] == 4
    assert len(plan.metadata["_batch_prompts"]) == 4
    assert "variation 2" in plan.metadata["_batch_prompts"][2]


@pytest.mark.asyncio
async def test_plan_assistant_execution_uses_context_for_referential_image_follow_up(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return []

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)

    plan = await graph.plan_assistant_execution(
        messages=[
            {"role": "user", "content": "帮我分析这个文章展示网站应该做成什么视觉方向"},
            {
                "role": "assistant",
                "content": "建议做成现代杂志风的文章展示首页，使用深蓝色导航、卡片式文章流和编辑感排版。",
            },
            {"role": "user", "content": "不错，根据你分析的内容生图吧"},
        ],
        files=[],
        user_instruction="不错，根据你分析的内容生图吧",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=1,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key=None,
    )

    assert plan.mode == "image"
    assert plan.intent_type == "single_generate"
    assert plan.effective_model == "gpt-image-1"
    assert plan.metadata["conversation_context_used"] is True
    assert "现代杂志风" in (plan.prompt or "")
    assert "卡片式文章流" in (plan.prompt or "")


@pytest.mark.asyncio
async def test_plan_assistant_execution_prefers_chat_for_contextual_summary_even_with_image_model(monkeypatch):
    async def fake_load_attachment_descriptors(files, db_manager, api_key=None):
        return []

    monkeypatch.setattr(graph, "_load_attachment_descriptors", fake_load_attachment_descriptors)

    plan = await graph.plan_assistant_execution(
        messages=[
            {"role": "user", "content": "帮我分析这个文章展示网站应该做成什么视觉方向"},
            {
                "role": "assistant",
                "content": "建议做成现代杂志风的文章展示首页，使用深蓝色导航、卡片式文章流和编辑感排版。",
            },
            {"role": "user", "content": "把上面的内容总结成三点"},
        ],
        files=[],
        user_instruction="把上面的内容总结成三点",
        request_model="gpt-image-1",
        request_model_type="image",
        requested_count=1,
        db_manager=object(),
        app_state=SimpleNamespace(model_registry=None),
        api_key=None,
    )

    expected_chat_model = (
        settings.assistant_text_model
        or settings.langchain_pdf_prompt_model
        or settings.openai_model
        or "gpt-4o-mini"
    )

    assert plan.mode == "chat"
    assert plan.intent_type == "chat"
    assert plan.effective_model == expected_chat_model
