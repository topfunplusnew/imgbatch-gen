from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.workflows import assistant_execution_graph as graph
from src.workflows.multimodal_attachment_graph import (
    AttachmentDescriptor,
    AttachmentRouteDecision,
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
