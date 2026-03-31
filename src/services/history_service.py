"""Service layer for conversation history APIs."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from loguru import logger
from openai import AsyncOpenAI

from ..config.settings import settings
from ..database.repositories import HistoryRepository


def _serialize_utc_datetime(value: Optional[datetime]) -> Optional[str]:
    """Serialize datetimes to UTC ISO-8601 with `Z` suffix."""
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat().replace("+00:00", "Z")


def _safe_json_loads(value: Optional[str]) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


class HistoryService:
    """Business logic for conversation history."""

    def __init__(self, repository: Optional[HistoryRepository] = None):
        self.repository = repository or HistoryRepository()

    async def create_session(
        self, session_id: str, title: str, model: str, provider: Optional[str], client_id: str
    ) -> dict[str, Any]:
        try:
            normalized_title = title[:8] if len(title) > 8 else title
            await self.repository.create_session(
                session_id=session_id,
                title=normalized_title,
                model=model,
                provider=provider or "unknown",
                client_id=client_id,
            )
            logger.info(f"创建新对话会话: {session_id}")
            return {"status": "success", "session_id": session_id, "message": "对话会话创建成功"}
        except Exception as exc:
            logger.error(f"创建对话会话失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"创建失败: {str(exc)}") from exc

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: Optional[str],
        provider: Optional[str],
        images: Optional[list[str]],
        files: Optional[list[dict[str, Any]]],
        user_request_id: Optional[str],
    ) -> dict[str, Any]:
        try:
            await self.repository.create_message(
                session_id=session_id,
                role=role,
                content=content,
                model=model or "unknown",
                provider=provider or "unknown",
                images=json.dumps(images) if images else None,
                files=json.dumps(files) if files else None,
                user_request_id=user_request_id,
            )

            preview = (content or "")[:30]
            logger.info(f"保存消息: {role} - {preview}...")
            return {"status": "success", "session_id": session_id, "message": "消息保存成功"}
        except Exception as exc:
            logger.error(f"保存消息失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"保存失败: {str(exc)}") from exc

    async def list_conversations(self, client_id: str, limit: int, offset: int) -> dict[str, Any]:
        try:
            rows = await self.repository.list_active_conversations(
                client_id=client_id,
                limit=limit,
                offset=offset,
            )

            summaries = [
                {
                    "session_id": row.session_id,
                    "title": row.title,
                    "created_at": _serialize_utc_datetime(row.created_at),
                    "updated_at": _serialize_utc_datetime(row.updated_at),
                    "message_count": int(row.message_count or 0),
                    "image_count": row.image_count or 0,
                }
                for row in rows
            ]

            return {
                "total": len(summaries),
                "conversations": summaries,
                "limit": limit,
                "offset": offset,
            }
        except Exception as exc:
            logger.error(f"获取对话列表失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"获取失败: {str(exc)}") from exc

    async def get_conversation(self, session_id: str) -> dict[str, Any]:
        try:
            session_obj, messages, files = await self.repository.get_conversation_detail(session_id)

            if not session_obj:
                raise HTTPException(status_code=404, detail="对话不存在")

            formatted_messages = []
            for msg in messages:
                formatted_messages.append(
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "model": msg.model,
                        "provider": msg.provider,
                        "created_at": _serialize_utc_datetime(msg.created_at),
                        "images": _safe_json_loads(msg.images),
                        "files": _safe_json_loads(msg.files),
                    }
                )

            formatted_files = []
            for file in files:
                formatted_files.append(
                    {
                        "id": file.id,
                        "original_filename": file.original_filename,
                        "file_url": file.file_url,
                        "file_size": file.file_size,
                        "file_type": file.file_type,
                        "category": file.category,
                        "created_at": _serialize_utc_datetime(file.created_at),
                    }
                )

            return {
                "session_id": session_id,
                "title": session_obj.title,
                "created_at": _serialize_utc_datetime(session_obj.created_at),
                "updated_at": _serialize_utc_datetime(session_obj.updated_at),
                "message_count": len(messages),
                "image_count": session_obj.image_count or 0,
                "file_count": len(files),
                "messages": formatted_messages,
                "files": formatted_files,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"获取对话详情失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"获取失败: {str(exc)}") from exc

    async def delete_conversation(self, session_id: str) -> dict[str, Any]:
        try:
            logger.info(f"开始删除会话: {session_id}")
            deleted_count = await self.repository.delete_conversation(session_id)
            logger.info(f"提交删除，共删除 {deleted_count} 条记录")
            return {
                "status": "success",
                "session_id": session_id,
                "deleted_count": deleted_count,
            }
        except Exception as exc:
            logger.error(f"删除对话失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"删除失败: {str(exc)}") from exc

    async def summarize_conversation(
        self,
        session_id: str,
        client: AsyncOpenAI,
    ) -> dict[str, Any]:
        try:
            messages = await self.repository.get_chat_messages(session_id)
            if not messages:
                raise HTTPException(status_code=404, detail="会话不存在或没有消息")

            conversation_text = "\n".join(
                f"{msg.role}: {msg.content}" for msg in messages if msg.content
            )

            response = await client.chat.completions.create(
                model=settings.openai_model or "gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "你是标题生成器。严格要求：输出必须≤8个汉字，禁止标点符号，禁止解释，只输出标题本身。示例：智能客服系统设计、Python爬虫入门、图片生成测试",
                    },
                    {"role": "user", "content": f"请总结以下对话：\n\n{conversation_text}"},
                ],
                temperature=0.3,
            )

            summary = (response.choices[0].message.content or "").strip()
            if not summary:
                summary = "新对话"
            if len(summary) > 8:
                summary = summary[:8]

            await self.repository.update_session_title(session_id, summary)

            logger.info(f"生成会话总结: {session_id}")
            return {"status": "success", "session_id": session_id, "summary": summary}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"生成会话总结失败: {str(exc)}")
            raise HTTPException(status_code=500, detail=f"总结失败: {str(exc)}") from exc

