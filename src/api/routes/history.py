"""对话历史接口"""

import json
import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy import select, and_, desc, func

from ...database import get_db_manager
from ...models.task import ImageTask
from ...database.models import ConversationSession, ChatConversation, UploadedFile
from ...engine import TaskManager
from ...config.settings import settings
from .chat import _extract_api_key, _get_openai_client
from ..auth import OptionalAuthDependency


router = APIRouter(prefix="/api/v1", tags=["history"])

_MINIO_INTERNAL_RE = re.compile(r'^https?://[^/]*minio[^/]*(?::\d+)?/[^/]+/(.+)$')
_LOCALHOST_MINIO_RE = re.compile(r'^https?://(?:localhost|127\.0\.0\.1):\d+/[^/]+/(.+)$')


def _normalize_image_url(url: str) -> str:
    """将 MinIO 内部 URL 转为前端可访问的 /storage/ 路径"""
    if not url:
        return url
    m = _MINIO_INTERNAL_RE.match(url)
    if m:
        return f"/storage/{m.group(1)}"
    m = _LOCALHOST_MINIO_RE.match(url)
    if m:
        return f"/storage/{m.group(1)}"
    return url


# ==================== 请求/响应模型 ====================

class ConversationMessage(BaseModel):
    """对话消息模型"""
    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")
    created_at: Optional[str] = Field(None, description="创建时间")


class ConversationInfo(BaseModel):
    """对话信息模型"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    message_count: int = Field(..., description="消息数量")
    image_count: int = Field(..., description="图片数量")


class ConversationSummary(BaseModel):
    """对话摘要模型"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题（第一条用户消息）")
    created_at: str = Field(..., description="创建时间")
    message_count: int = Field(..., description="消息数量")
    last_message: Optional[str] = Field(None, description="最后一条消息")


class CreateSessionRequest(BaseModel):
    """创建对话会话请求"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="对话标题")
    model: str = Field(..., description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")


class SaveMessageRequest(BaseModel):
    """保存消息请求"""
    session_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    model: Optional[str] = Field(None, description="使用的模型")
    provider: Optional[str] = Field(None, description="Provider名称")
    timestamp: Optional[str] = Field(None, description="时间戳")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    files: Optional[List[dict]] = Field(None, description="文件信息列表")
    user_request_id: Optional[str] = Field(None, description="关联的用户请求ID")


# ==================== 路由 ====================

def _get_client_id(http_request: Request) -> str:
    """从 Cookie 中获取客户端 ID"""
    return http_request.cookies.get("client_id", "anonymous")


def _get_owner_id(http_request: Request, user: Optional[dict] = None) -> tuple:
    """获取数据隔离标识：登录用户用 user_id，未登录用 client_id。
    Returns: (user_id_or_none, client_id)
    """
    user_id = user.get("id") if user else None
    client_id = _get_client_id(http_request)
    return user_id, client_id


def _serialize_utc_datetime(value: Optional[datetime]) -> Optional[str]:
    """将数据库中的 UTC 时间统一序列化为带 Z 的 ISO 字符串。"""
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat().replace("+00:00", "Z")


@router.post("/history/create_session")
async def create_session(
    request: CreateSessionRequest,
    http_request: Request,
    user: Optional[dict] = Depends(OptionalAuthDependency()),
):
    """
    创建新的对话会话

    当用户开启新对话时调用此接口创建一个新的会话记录。
    """
    try:
        db_manager = get_db_manager()
        user_id, client_id = _get_owner_id(http_request, user)

        # 强制限制标题长度为8个字符
        title = request.title[:8] if len(request.title) > 8 else request.title

        # 使用数据库管理器的会话创建方法
        await db_manager.create_conversation_session(
            session_id=request.session_id,
            title=title,
            model=request.model,
            provider=request.provider or "unknown",
            status="active",
            client_id=client_id,
            user_id=user_id,
        )

        logger.info(f"创建新对话会话: {request.session_id}")

        return {
            "status": "success",
            "session_id": request.session_id,
            "message": "对话会话创建成功"
        }

    except Exception as e:
        logger.error(f"创建对话会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/history/save_message")
async def save_message(request: SaveMessageRequest):
    """
    保存单条消息

    保存用户的单条消息到对话消息表中，关联到对应的会话ID。
    自动去重：同一会话中相同角色+相同内容的消息在5秒内不重复保存。
    """
    try:
        db_manager = get_db_manager()

        # 去重检查：查询最近是否已有相同消息
        async with db_manager.get_session() as session:
            recent = await session.scalar(
                select(ChatConversation)
                .where(
                    and_(
                        ChatConversation.session_id == request.session_id,
                        ChatConversation.role == request.role,
                        ChatConversation.content == request.content,
                    )
                )
                .order_by(desc(ChatConversation.created_at))
                .limit(1)
            )
            if recent:
                from datetime import timedelta
                now = datetime.now(timezone.utc)
                created = recent.created_at.replace(tzinfo=timezone.utc) if recent.created_at.tzinfo is None else recent.created_at
                if (now - created) < timedelta(seconds=5):
                    logger.debug(f"跳过重复消息: {request.role} - {request.content[:30]}...")
                    return {
                        "status": "success",
                        "session_id": request.session_id,
                        "message": "消息已存在，跳过"
                    }

        # 使用数据库管理器的消息创建方法
        await db_manager.create_chat_message(
            session_id=request.session_id,
            role=request.role,
            content=request.content,
            model=request.model or "unknown",
            provider=request.provider or "unknown",
            images=json.dumps(request.images) if request.images else None,
            files=json.dumps(request.files) if request.files else None,
            user_request_id=request.user_request_id
        )

        logger.info(f"保存消息: {request.role} - {request.content[:30]}...")

        return {
            "status": "success",
            "session_id": request.session_id,
            "message": "消息保存成功"
        }

    except Exception as e:
        logger.error(f"保存消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/history/list")
async def list_conversations(
    http_request: Request,
    limit: int = 20,
    offset: int = 0,
    user: Optional[dict] = Depends(OptionalAuthDependency()),
):
    """
    获取对话列表

    返回当前用户的对话摘要信息，按创建时间倒序排列。
    已登录用户按 user_id 过滤，未登录用户按 client_id 过滤。
    """
    try:
        db_manager = get_db_manager()
        user_id, client_id = _get_owner_id(http_request, user)

        # 查询对话会话列表（优先按 user_id 过滤，未登录按 client_id）
        async with db_manager.get_session() as session:
            owner_filter = (
                ConversationSession.user_id == user_id
                if user_id
                else ConversationSession.client_id == client_id
            )
            stmt = (
                select(ConversationSession)
                .where(ConversationSession.status == "active")
                .where(owner_filter)
                .order_by(ConversationSession.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            sessions = result.scalars().all()

        # 转换为摘要信息
        summaries = []
        for session in sessions:
            # 获取消息数量
            async with db_manager.get_session() as msg_session:
                msg_count_stmt = (
                    select(func.count())
                    .select_from(ChatConversation)
                    .where(ChatConversation.session_id == session.session_id)
                )
                msg_count_result = await msg_session.execute(msg_count_stmt)
                message_count = msg_count_result.scalar() or 0

            summaries.append({
                "session_id": session.session_id,
                "title": session.title,
                "created_at": _serialize_utc_datetime(session.created_at),
                "updated_at": _serialize_utc_datetime(session.updated_at),
                "message_count": message_count,
                "image_count": session.image_count or 0
            })

        return {
            "total": len(summaries),
            "conversations": summaries,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_conversation(
    session_id: str
):
    """
    获取特定对话的详细信息

    根据session_id获取对话的所有消息和文件信息。
    消息按创建时间升序排列。
    """
    try:
        db_manager = get_db_manager()

        # 获取对话会话信息
        async with db_manager.get_session() as session:
            session_stmt = (
                select(ConversationSession)
                .where(ConversationSession.session_id == session_id)
            )
            session_result = await session.execute(session_stmt)
            session_obj = session_result.scalars().first()

            if not session_obj:
                raise HTTPException(status_code=404, detail="对话不存在")

            # 获取对话消息
            msg_stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
                .order_by(ChatConversation.created_at.asc())
            )
            msg_result = await session.execute(msg_stmt)
            messages = msg_result.scalars().all()

            # 获取对话文件
            file_stmt = (
                select(UploadedFile)
                .where(UploadedFile.conversation_id == session_id)
                .where(UploadedFile.status == "active")
                .order_by(UploadedFile.created_at.asc())
            )
            file_result = await session.execute(file_stmt)
            files = file_result.scalars().all()

        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            msg_data = {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "model": msg.model,
                "provider": msg.provider,
                "created_at": _serialize_utc_datetime(msg.created_at)
            }
            if msg.images:
                try:
                    raw_images = json.loads(msg.images)
                    msg_data["images"] = [_normalize_image_url(u) for u in raw_images if u]
                except Exception:
                    msg_data["images"] = []
            if msg.files:
                try:
                    msg_data["files"] = json.loads(msg.files)
                except Exception:
                    msg_data["files"] = []
            formatted_messages.append(msg_data)

        # 转换文件格式
        formatted_files = []
        for file in files:
            formatted_files.append({
                "id": file.id,
                "original_filename": file.original_filename,
                "file_url": file.file_url,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "category": file.category,
                "created_at": _serialize_utc_datetime(file.created_at)
            })

        return {
            "session_id": session_id,
            "title": session_obj.title,
            "created_at": _serialize_utc_datetime(session_obj.created_at),
            "updated_at": _serialize_utc_datetime(session_obj.updated_at),
            "message_count": len(messages),
            "image_count": session_obj.image_count or 0,
            "file_count": len(files),
            "messages": formatted_messages,
            "files": formatted_files
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete("/history/{session_id}")
async def delete_conversation(
    session_id: str
):
    """
    删除特定对话

    根据session_id删除对话会话及其所有相关消息。
    """
    try:
        db_manager = get_db_manager()
        logger.info(f"开始删除会话: {session_id}")

        deleted_count = 0

        async with db_manager.get_session() as db_session:
            # 删除对话会话
            session_stmt = (
                select(ConversationSession)
                .where(ConversationSession.session_id == session_id)
            )
            session_result = await db_session.execute(session_stmt)
            session_obj = session_result.scalars().first()

            logger.info(f"查询到会话对象: {session_obj}")

            if session_obj:
                await db_session.delete(session_obj)
                deleted_count += 1
                logger.info(f"已删除会话对象")

            # 删除所有相关消息
            msg_stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
            )
            msg_result = await db_session.execute(msg_stmt)
            messages = msg_result.scalars().all()

            logger.info(f"查询到 {len(messages)} 条消息")

            for msg in messages:
                await db_session.delete(msg)
                deleted_count += 1

            await db_session.commit()
            logger.info(f"提交删除，共删除 {deleted_count} 条记录")

        return {
            "status": "success",
            "session_id": session_id,
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/history/update_session")
async def update_session(
    session_id: str,
    title: Optional[str] = None,
    image_count: Optional[int] = None
):
    """
    更新对话信息

    更新对话的标题、图片数量等信息。
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            # 获取对话会话
            session_stmt = (
                select(ConversationSession)
                .where(ConversationSession.session_id == session_id)
            )
            session_result = await session.execute(session_stmt)
            session_obj = session_result.scalars().first()

            if not session_obj:
                raise HTTPException(status_code=404, detail="对话不存在")

            # 更新字段
            if title is not None:
                session_obj.title = title
            if image_count is not None:
                session_obj.image_count = image_count
            session_obj.updated_at = datetime.utcnow()

            await session.commit()

        logger.info(f"更新对话信息: {session_id}")

        return {
            "status": "success",
            "session_id": session_id,
            "message": "更新成功"
        }

    except Exception as e:
        logger.error(f"更新对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/history/{session_id}/summary")
async def summarize_conversation(session_id: str, http_request: Request):
    """
    使用 ChatGPT 对当前会话生成总结
    """
    try:
        db_manager = get_db_manager()

        # 获取会话消息
        messages = await db_manager.get_chat_messages(session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="会话不存在或没有消息")

        # 构建对话内容
        conversation_text = "\n".join(
            f"{msg.role}: {msg.content}" for msg in messages if msg.content
        )

        # 使用 OpenAI 生成总结（API Key 可选，使用管理员统一配置）
        api_key = _extract_api_key(http_request)
        client = await _get_openai_client(api_key)

        response = await client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是标题生成器。严格要求：输出必须≤8个汉字，禁止标点符号，禁止解释，只输出标题本身。示例：智能客服系统设计、Python爬虫入门、图片生成测试"},
                {"role": "user", "content": f"请总结以下对话：\n\n{conversation_text}"}
            ],
            temperature=0.3
        )

        summary = response.choices[0].message.content.strip()

        # 强制限制标题长度为8个字符
        if len(summary) > 8:
            summary = summary[:8]

        # 更新会话标题为总结
        await db_manager.update_conversation_session(session_id, title=summary)

        logger.info(f"生成会话总结: {session_id}")

        return {
            "status": "success",
            "session_id": session_id,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成会话总结失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"总结失败: {str(e)}")
