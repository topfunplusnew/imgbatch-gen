"""数据库管理器"""

import asyncio
from datetime import timedelta
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, delete, and_, or_
from contextlib import asynccontextmanager
from loguru import logger

from .models import UserRequest, ImageGenerationRecord, ChatConversation, SystemLog, ConversationSession, UploadedFile, StoredCredential, UploadedFile
from .auth_models import User, UserAuth, LoginLog
from .billing_models import Account, Transaction, ConsumptionRecord, Withdrawal
from .payment_models import PaymentOrder
from .download_models import DownloadRecord
from .base import Base
from ..config.settings import settings
from ..utils.credential_crypto import encrypt_api_key, decrypt_api_key, mask_api_key


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str = None, echo: bool = False):
        """
        初始化数据库管理器

        Args:
            database_url: 数据库连接URL
                PostgreSQL格式: postgresql+asyncpg://user:password@host:port/database
            echo: 是否输出SQL日志
            """
        self.database_url = database_url or "postgresql+asyncpg://postgres:1234@localhost:5432/agent_db"
        self.echo = echo

        # PostgreSQL 连接池配置
        engine_kwargs = dict(
            echo=echo,
            pool_pre_ping=True,  # 在使用连接前测试连接
            pool_recycle=3600,  # 1小时后回收连接
            pool_size=5,  # 连接池大小
            max_overflow=10,  # 最大溢出连接数
        )

        # 创建异步引擎
        self.engine = create_async_engine(
            self.database_url,
            **engine_kwargs
        )

        # 创建会话工厂
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

        logger.info(f"数据库管理器初始化完成: {self.database_url}")

    @staticmethod
    def _merge_runtime_metadata(payload: Optional[Dict[str, Any]], metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Persist workflow metadata inside normal JSON columns."""
        merged = dict(payload or {})
        if metadata:
            runtime_metadata = dict(merged.get("_runtime_metadata") or {})
            runtime_metadata.update(metadata)
            merged["_runtime_metadata"] = runtime_metadata
        return merged

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """异步获取数据库会话（上下文管理器）"""
        async with self.async_session_factory() as session:
            yield session

    # ==================== 用户请求记录相关 ====================

    async def create_user_request(
        self,
        user_id: str,
        user_ip: str = None,
        user_agent: str = None,
        request_type: str = None,
        request_data: Dict[str, Any] = None,
        status: str = "pending",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserRequest:
        """创建用户请求记录"""
        async with self.get_session() as session:
            user_request = UserRequest(
                user_id=user_id,
                user_ip=user_ip,
                user_agent=user_agent,
                request_type=request_type,
                request_data=self._merge_runtime_metadata(request_data, metadata),
                status=status,
                error_message=error_message,
            )
            session.add(user_request)
            await session.flush()
            await session.commit()
            await session.refresh(user_request)
            logger.info(f"创建用户请求记录: {user_request.id}")
            return user_request

    async def update_user_request_status(
        self,
        user_request_id: str,
        status: str,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserRequest:
        """更新用户请求状态"""
        async with self.get_session() as session:
            result = await session.execute(
                select(UserRequest)
                .where(UserRequest.id == user_request_id)
            )
            user_request = result.scalar_one_or_none()
            if user_request:
                user_request.status = status
                if error_message is not None:
                    user_request.error_message = error_message
                if metadata is not None:
                    user_request.request_data = self._merge_runtime_metadata(
                        user_request.request_data,
                        metadata,
                    )
                await session.flush()
                await session.commit()
                logger.info(f"更新用户请求状态: {user_request.id} -> {status}")
                return user_request
            else:
                logger.warning(f"未找到用户请求记录: {user_request_id}")
                return None

    async def get_user_requests(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserRequest]:
        """获取用户请求列表"""
        async with self.get_session() as session:
            stmt = (
                select(UserRequest)
                .where(UserRequest.user_id == user_id)
                .order_by(UserRequest.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_request_by_id(self, user_request_id: str) -> Optional[UserRequest]:
        """根据ID获取用户请求"""
        async with self.get_session() as session:
            stmt = select(UserRequest).where(UserRequest.id == user_request_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def store_api_credential(
        self,
        api_key: str,
        provider: str = "relay",
        base_url: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_hours: Optional[int] = None,
    ) -> StoredCredential:
        """Persist an encrypted API credential for out-of-request work."""
        expiry_hours = ttl_hours if ttl_hours is not None else settings.credential_ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours) if expiry_hours > 0 else None

        async with self.get_session() as session:
            credential = StoredCredential(
                provider=provider,
                base_url=base_url,
                user_id=user_id,
                session_id=session_id,
                encrypted_api_key=encrypt_api_key(api_key),
                key_hint=mask_api_key(api_key),
                status="active",
                expires_at=expires_at,
                last_used_at=datetime.utcnow(),
            )
            session.add(credential)
            await session.commit()
            await session.refresh(credential)
            logger.info(f"Stored encrypted credential: {credential.id} ({credential.key_hint})")
            return credential

    async def resolve_api_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt a stored API credential."""
        async with self.get_session() as session:
            result = await session.execute(
                select(StoredCredential)
                .where(StoredCredential.id == credential_id)
            )
            credential = result.scalar_one_or_none()
            if not credential:
                return None

            if credential.status != "active":
                return None

            now = datetime.utcnow()
            if credential.expires_at and credential.expires_at < now:
                credential.status = "expired"
                await session.commit()
                return None

            credential.last_used_at = now
            await session.commit()

            return {
                "credential_id": credential.id,
                "provider": credential.provider,
                "base_url": credential.base_url,
                "api_key": decrypt_api_key(credential.encrypted_api_key),
                "key_hint": credential.key_hint,
                "session_id": credential.session_id,
                "user_id": credential.user_id,
            }

    # ==================== 图片生成记录相关 ====================

    async def create_image_generation_record(
        self,
        user_request_id: str,
        provider: str,
        model: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        n: int = 1,
        style: Optional[str] = None,
        quality: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        image_urls: Optional[List[str]] = None,
        image_paths: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        call_mode: str = "serial",
    ) -> ImageGenerationRecord:
        """创建图片生成记录"""
        async with self.get_session() as session:
            record = ImageGenerationRecord(
                user_request_id=user_request_id,
                provider=provider,
                model=model,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                n=n,
                style=style,
                quality=quality,
                extra_params=extra_params or {},
                status=status,
                image_urls=image_urls,
                image_paths=image_paths,
                processing_time=processing_time,
                start_time=start_time,
                end_time=end_time,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                call_mode=call_mode
            )
            session.add(record)
            await session.flush()
            await session.commit()
            await session.refresh(record)
            logger.info(f"创建图片生成记录: {record.id}")
            return record

    async def update_image_generation_record(
        self,
        record_id: str,
        status: str,
        image_urls: Optional[List[str]] = None,
        image_paths: Optional[List[str]] = None,
        processing_time: Optional[float] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ImageGenerationRecord]:
        """更新图片生成记录状态"""
        async with self.get_session() as session:
            result = await session.execute(
                select(ImageGenerationRecord)
                .where(ImageGenerationRecord.id == record_id)
            )
            record = result.scalar_one_or_none()
            if record:
                if status is not None:
                    record.status = status
                if image_urls is not None:
                    record.image_urls = image_urls
                if image_paths is not None:
                    record.image_paths = image_paths
                if processing_time is not None:
                    record.processing_time = processing_time
                if start_time is not None:
                    record.start_time = start_time
                if end_time is not None:
                    record.end_time = end_time
                if prompt_tokens is not None:
                    record.prompt_tokens = prompt_tokens
                if completion_tokens is not None:
                    record.completion_tokens = completion_tokens
                if total_tokens is not None:
                    record.total_tokens = total_tokens
                if metadata is not None:
                    record.extra_params = self._merge_runtime_metadata(
                        record.extra_params,
                        metadata,
                    )
                await session.flush()
                await session.commit()
                await session.refresh(record)
                logger.info(f"更新图片生成记录状态: {record_id} -> {status}")
                return record
            else:
                logger.warning(f"未找到图片生成记录: {record_id}")
                return None

    async def get_user_image_generations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGenerationRecord]:
        """获取用户图片生成记录"""
        async with self.get_session() as session:
            # 关联查询用户请求
            image_gen_stmt = (
                select(ImageGenerationRecord)
                .join(UserRequest)
                .where(UserRequest.user_id == user_id)
            )
            image_gen_result = await session.execute(image_gen_stmt)
            image_gen_count = len(image_gen_result.scalars().all())

            # 对话数
            chat_stmt = (
                select(ChatConversation)
                .join(UserRequest)
                .where(UserRequest.user_id == user_id)
            )
            chat_result = await session.execute(chat_stmt)
            chat_count = len(chat_result.scalars().all())

            # 总请求数
            total_requests_stmt = (
                select(UserRequest)
                .where(UserRequest.user_id == user_id)
            )
            total_requests_result = await session.execute(total_requests_stmt)
            total_requests_count = len(total_requests_result.scalars().all())

            return {
                "total_requests": total_requests_count,
                "image_generations": image_gen_count,
                "chat_conversations": chat_count
            }

    async def get_image_generation_records(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ImageGenerationRecord]:
        """获取所有图片生成记录（分页）"""
        async with self.get_session() as session:
            stmt = (
                select(ImageGenerationRecord)
                .join(UserRequest)
                .order_by(ImageGenerationRecord.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ============ 对话记录相关 ============

    async def create_chat_conversation(
        self,
        user_request_id: str,
        session_id: str,
        role: str,
        content: str,
        model: str,
        **kwargs
    ) -> ChatConversation:
        """创建对话记录"""
        async with self.get_session() as session:
            conversation = ChatConversation(
                user_request_id=user_request_id,
                session_id=session_id,
                role=role,
                content=content,
                model=model,
                **kwargs
            )
            session.add(conversation)
            await session.flush()
            await session.refresh(conversation)
            logger.info(f"创建对话记录: {conversation.id}")
            return conversation

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ChatConversation]:
        """获取对话历史"""
        async with self.get_session() as session:
            stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
                .order_by(ChatConversation.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        获取对话列表（按session_id分组）

        返回每个对话的摘要信息，包括对话ID、标题（第一条用户消息）、创建时间等。
        """
        async with self.get_session() as session:
            # 获取所有对话记录
            stmt = (
                select(ChatConversation)
                .order_by(ChatConversation.created_at.desc())
            )
            result = await session.execute(stmt)
            all_conversations = list(result.scalars().all())

            # 按session_id分组
            conversations_dict = {}
            for conv in all_conversations:
                if conv.session_id not in conversations_dict:
                    conversations_dict[conv.session_id] = {
                        "conversation_id": conv.session_id,
                        "title": conv.content[:50] if conv.content else "空对话",
                        "created_at": conv.created_at,
                        "message_count": 0,
                        "last_message": conv.content if conv.content else None,
                        "model": conv.model,
                        "provider": conv.provider
                    }
                conv_data = conversations_dict[conv.session_id]
                conv_data["message_count"] += 1

            # 转换为列表并分页
            conversations_list = list(conversations_dict.values())
            return conversations_list[offset:offset + limit]

    async def delete_conversation(self, session_id: str) -> int:
        """删除特定对话及其所有消息记录"""
        async with self.get_session() as session:
            # 删除所有匹配的对话记录
            stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
            )
            result = await session.execute(stmt)
            conversations = result.scalars().all()

            deleted_count = 0
            for conv in conversations:
                await session.delete(conv)
                deleted_count += 1

            logger.info(f"删除对话 {session_id}，删除了 {deleted_count} 条记录")
            return deleted_count

    # ============ 系统日志相关 ============

    async def create_system_log(
        self,
        level: str,
        module: str,
        function: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: str = None,
        request_id: str = None,
    ) -> SystemLog:
        """创建系统日志"""
        async with self.get_session() as session:
            system_log = SystemLog(
                level=level,
                module=module,
                function=function,
                message=message,
                details=details or {},
                user_id=user_id,
                request_id=request_id
            )
            session.add(system_log)
            await session.flush()
            await session.refresh(system_log)
            logger.info(f"创建系统日志: {system_log.id}")
            return system_log

    async def get_system_logs(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SystemLog]:
        """获取系统日志"""
        async with self.get_session() as session:
            stmt = select(SystemLog)
            if level:
                stmt = stmt.where(SystemLog.level == level)
            if module:
                stmt = stmt.where(SystemLog.module == module)
            stmt = stmt.order_by(SystemLog.created_at.desc()).offset(offset).limit(limit)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ============ 数据库清理相关 ============

    async def cleanup_old_records(self, days: int = 30):
        """清理旧记录"""
        async with self.get_session() as session:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # 清理旧的图片生成记录
            image_gen_stmt = (
                select(ImageGenerationRecord)
                .where(ImageGenerationRecord.created_at < cutoff_date)
            )
            image_gen_result = await session.execute(image_gen_stmt)
            for record in image_gen_result.scalars():
                await session.delete(record)
            image_gen_deleted = len(image_gen_result.scalars().all())

            # 清理旧的对话记录
            chat_conv_stmt = (
                select(ChatConversation)
                .where(ChatConversation.created_at < cutoff_date)
            )
            chat_conv_result = await session.execute(chat_conv_stmt)
            for record in chat_conv_result.scalars():
                await session.delete(record)
            chat_conv_deleted = len(chat_conv_result.scalars().all())

            # 清理旧的系统日志
            system_log_stmt = (
                select(SystemLog)
                .where(SystemLog.created_at < cutoff_date)
            )
            system_log_result = await session.execute(system_log_stmt)
            for record in system_log_result.scalars():
                await session.delete(record)
            system_log_deleted = len(system_log_result.scalars().all())

            logger.info(f"清理旧记录完成: 图片生成={image_gen_deleted}, 对话={chat_conv_deleted}, 系统日志={system_log_deleted}")

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        async with self.get_session() as session:
            # 获取用户请求数
            user_req_stmt = (
                select(UserRequest)
                .where(UserRequest.user_id == user_id)
            )
            user_req_result = await session.execute(user_req_stmt)

        # 获取图片生成记录数
        image_gen_stmt = (
            select(ImageGenerationRecord)
            .join(UserRequest)
            .where(UserRequest.user_id == user_id)
        )
        image_gen_result = await session.execute(image_gen_stmt)
        image_gen_count = len(image_gen_result.scalars().all())

        # 获取对话数
        chat_stmt = (
            select(ChatConversation)
            .join(UserRequest)
            .where(UserRequest.user_id == user_id)
        )
        chat_result = await session.execute(chat_stmt)
        chat_count = len(chat_result.scalars().all())

        return {
            "total_requests": len(user_req_result.scalars().all()),
            "image_generations": image_gen_count,
            "chat_conversations": chat_count
        }

    async def close(self):
        """关闭数据库连接"""
        await self.engine.dispose()
        logger.info("数据库连接已关闭")

    # ==================== 对话会话管理相关 ====================

    async def create_conversation_session(
        self,
        session_id: str,
        title: str,
        model: str,
        provider: str = "unknown",
        status: str = "active",
        client_id: str = "anonymous"
    ):
        """创建对话会话（如果已存在则直接返回）"""
        async with self.get_session() as session:
            # 检查是否已存在
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            session_obj = ConversationSession(
                session_id=session_id,
                client_id=client_id,
                title=title,
                model=model,
                provider=provider,
                status=status,
                message_count=0,
                image_count=0,
                file_count=0
            )
            session.add(session_obj)
            await session.commit()
            await session.refresh(session_obj)
            logger.info(f"创建对话会话: {session_id}")
            return session_obj

    async def get_conversation_sessions(
        self,
        status: str = "active",
        limit: int = 20,
        offset: int = 0
    ):
        """获取对话会话列表"""
        async with self.get_session() as session:
            stmt = (
                select(ConversationSession)
                .where(ConversationSession.status == status)
                .order_by(ConversationSession.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_conversation_session(self, session_id: str):
        """获取特定对话会话"""
        async with self.get_session() as session:
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update_conversation_session(
        self,
        session_id: str,
        title: str = None,
        image_count: int = None
    ):
        """更新对话会话"""
        async with self.get_session() as session:
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            session_obj = result.scalars().first()

            if session_obj:
                if title is not None:
                    session_obj.title = title
                if image_count is not None:
                    session_obj.image_count = image_count
                session_obj.updated_at = datetime.utcnow()

                await session.commit()
                logger.info(f"更新对话会话: {session_id}")
                return session_obj
            return None

    async def delete_conversation_session(self, session_id: str):
        """删除对话会话"""
        async with self.get_session() as session:
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            session_obj = result.scalars().first()

            if session_obj:
                await session.delete(session_obj)
                await session.commit()
                logger.info(f"删除对话会话: {session_id}")
                return True
            return False

    async def update_session_stats(self, session_id: str, image_increment: int = 0):
        """更新会话统计信息"""
        async with self.get_session() as session:
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            session_obj = result.scalars().first()

            if session_obj:
                session_obj.image_count = (session_obj.image_count or 0) + image_increment
                session_obj.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"更新会话统计: {session_id}, 图片数量: {session_obj.image_count}")

    # ==================== 对话消息管理相关 ====================

    async def create_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str = "unknown",
        provider: str = "unknown",
        user_request_id: str = "",
        images: str = None,
        files: str = None
    ):
        """创建对话消息"""
        async with self.get_session() as session:
            message = ChatConversation(
                session_id=session_id,
                role=role,
                content=content,
                model=model,
                provider=provider,
                user_request_id=user_request_id,
                images=images,
                files=files
            )
            session.add(message)
            await session.commit()
            await session.flush()
            await session.refresh(message)

            # 更新会话的消息计数
            await self.update_session_message_count(session_id)

            logger.info(f"创建对话消息: {role} - {content[:30]}...")
            return message

    async def get_chat_messages(
        self,
        session_id: str,
        limit: int = 100
    ):
        """获取对话消息列表"""
        async with self.get_session() as session:
            stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
                .order_by(ChatConversation.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_chat_message_count(self, session_id: str):
        """获取对话消息数量"""
        async with self.get_session() as session:
            from sqlalchemy import func
            stmt = (
                select(func.count())
                .select_from(ChatConversation)
                .where(ChatConversation.session_id == session_id)
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def update_session_message_count(self, session_id: str):
        """更新会话的消息数量"""
        async with self.get_session() as session:
            stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
            result = await session.execute(stmt)
            session_obj = result.scalars().first()

            if session_obj:
                new_count = await self.get_chat_message_count(session_id)
                session_obj.message_count = new_count
                session_obj.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"更新会话消息数量: {session_id}, 消息数量: {new_count}")

    # ==================== 文件管理相关 ====================

    async def create_uploaded_file(
        self,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_url: str,
        file_size: int,
        file_type: str,
        file_extension: str,
        category: str = "general",
        conversation_id: str = None,
        message_id: int = None,
        is_public: bool = False
    ) -> UploadedFile:
        """创建上传文件记录"""
        async with self.get_session() as session:
            uploaded_file = UploadedFile(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_url=file_url,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                category=category,
                conversation_id=conversation_id,
                message_id=message_id,
                is_public=is_public
            )
            session.add(uploaded_file)
            await session.flush()
            await session.refresh(uploaded_file)
            logger.info(f"创建上传文件记录: {uploaded_file.id} - {original_filename}")
            return uploaded_file

    async def get_uploaded_file(self, file_id: int) -> Optional[UploadedFile]:
        """获取上传文件记录"""
        async with self.get_session() as session:
            stmt = select(UploadedFile).where(UploadedFile.id == file_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_files_by_conversation(self, conversation_id: str) -> List[UploadedFile]:
        """获取指定对话的所有文件"""
        async with self.get_session() as session:
            stmt = (
                select(UploadedFile)
                .where(UploadedFile.conversation_id == conversation_id)
                .where(UploadedFile.status == "active")
                .order_by(UploadedFile.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_files_by_message(self, message_id: int) -> List[UploadedFile]:
        """获取指定消息的所有文件"""
        async with self.get_session() as session:
            stmt = (
                select(UploadedFile)
                .where(UploadedFile.message_id == message_id)
                .where(UploadedFile.status == "active")
                .order_by(UploadedFile.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_file_by_id(self, file_id: str) -> Optional[UploadedFile]:
        """根据文件ID获取文件信息"""
        async with self.get_session() as session:
            stmt = select(UploadedFile).where(UploadedFile.id == file_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def delete_uploaded_file(self, file_id: int) -> bool:
        """删除上传文件记录（软删除）"""
        async with self.get_session() as session:
            stmt = select(UploadedFile).where(UploadedFile.id == file_id)
            result = await session.execute(stmt)
            uploaded_file = result.scalar_one_or_none()

            if uploaded_file:
                uploaded_file.status = "deleted"
                await session.flush()
                logger.info(f"删除上传文件记录: {file_id}")
                return True
            return False

    async def update_file_conversation(self, file_id: int, conversation_id: str, message_id: int = None):
        """更新文件的关联对话和消息"""
        async with self.get_session() as session:
            stmt = select(UploadedFile).where(UploadedFile.id == file_id)
            result = await session.execute(stmt)
            uploaded_file = result.scalar_one_or_none()

            if uploaded_file:
                uploaded_file.conversation_id = conversation_id
                if message_id is not None:
                    uploaded_file.message_id = message_id
                await session.flush()
                logger.info(f"更新文件关联: {file_id} -> conversation {conversation_id}")
                return True
            return False

    async def save_images_to_conversation(self, session_id: str, image_urls: List[str], task_id: str):
        """
        将图片保存到对话中

        Args:
            session_id: 对话会话ID
            image_urls: 图片URL列表
            task_id: 任务ID
        """
        try:
            for i, image_url in enumerate(image_urls):
                # 创建一个简单的文件记录
                await self.create_uploaded_file(
                    original_filename=f"generated_image_{task_id}_{i+1}.png",
                    stored_filename=f"gen_img_{task_id}_{i+1}",
                    file_path="",  # 实际路径可能需要根据存储方式调整
                    file_url=image_url,
                    file_size=0,  # 可以尝试获取实际大小
                    file_type="image/png",
                    file_extension="png",
                    category="generated",
                    conversation_id=session_id
                )

            logger.info(f"保存了 {len(image_urls)} 张图片到对话 {session_id}")
            return True

        except Exception as e:
            logger.error(f"保存图片到对话失败: {str(e)}")
            return False

    # ==================== 用户认证相关 ====================

    async def create_user(self, user: User) -> User:
        """创建用户"""
        async with self.get_session() as session:
            session.add(user)
            await session.flush()
            await session.commit()
            await session.refresh(user)
            logger.info(f"创建用户: {user.id}")
            return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        async with self.get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        async with self.get_session() as session:
            stmt = select(User).where(User.phone == phone)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        async with self.get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_user(self, user: User) -> User:
        """更新用户"""
        async with self.get_session() as session:
            await session.merge(user)
            await session.commit()
            logger.info(f"更新用户: {user.id}")
            return user

    async def create_user_auth(self, auth: UserAuth) -> UserAuth:
        """创建用户认证记录"""
        async with self.get_session() as session:
            session.add(auth)
            await session.flush()
            await session.commit()
            await session.refresh(auth)
            logger.info(f"创建用户认证记录: {auth.id}")
            return auth

    async def get_user_auth(self, identifier: str, auth_type: str) -> Optional[UserAuth]:
        """获取用户认证记录"""
        async with self.get_session() as session:
            stmt = select(UserAuth).where(
                and_(
                    UserAuth.auth_identifier == identifier,
                    UserAuth.auth_type == auth_type
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_verify_code(
        self, identifier: str, auth_type: str, code: str, expiry: datetime
    ) -> bool:
        """更新验证码"""
        async with self.get_session() as session:
            stmt = select(UserAuth).where(
                and_(
                    UserAuth.auth_identifier == identifier,
                    UserAuth.auth_type == auth_type
                )
            )
            result = await session.execute(stmt)
            auth = result.scalar_one_or_none()
            if auth:
                auth.verify_code = code
                auth.verify_code_expiry = expiry
                await session.commit()
                return True
            return False

    async def create_login_log(self, log: LoginLog) -> LoginLog:
        """创建登录日志"""
        async with self.get_session() as session:
            session.add(log)
            await session.flush()
            await session.commit()
            await session.refresh(log)
            return log

    # ==================== 账户计费相关 ====================

    async def create_user_account(self, user_id: str) -> Account:
        """创建用户账户"""
        async with self.get_session() as session:
            account = Account(user_id=user_id)
            session.add(account)
            await session.flush()
            await session.commit()
            await session.refresh(account)
            logger.info(f"创建用户账户: {account.id}, user_id: {user_id}")
            return account

    async def get_account_by_user(self, user_id: str) -> Optional[Account]:
        """获取用户账户"""
        async with self.get_session() as session:
            stmt = select(Account).where(Account.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_account(self, account: Account) -> Account:
        """更新账户"""
        async with self.get_session() as session:
            await session.merge(account)
            await session.commit()
            return account

    async def get_account_by_invite_code(self, invite_code: str) -> Optional[Account]:
        """根据邀请码获取账户"""
        async with self.get_session() as session:
            stmt = select(Account).where(Account.invite_code == invite_code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def add_transaction(
        self,
        user_id: str,
        transaction_type: str,
        amount: int = 0,
        points_change: int = 0,
        description: str = "",
        related_order_id: str = None,
        related_request_id: str = None,
        metadata: Dict = None,
    ) -> Transaction:
        """添加交易记录"""
        async with self.get_session() as session:
            # 获取当前账户
            account = await self.get_account_by_user(user_id)
            if not account:
                raise ValueError(f"用户账户不存在: {user_id}")

            # 计算交易后状态
            balance_after = account.balance + amount
            points_after = account.points + points_change

            transaction = Transaction(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                points_change=points_change,
                balance_after=balance_after,
                points_after=points_after,
                related_order_id=related_order_id,
                related_request_id=related_request_id,
                description=description,
                metadata=metadata,
            )
            session.add(transaction)

            # 更新账户
            account.balance = balance_after
            account.points = points_after

            await session.flush()
            await session.commit()
            await session.refresh(transaction)
            logger.info(f"添加交易记录: {transaction.id}, type={transaction_type}, amount={amount}")
            return transaction

    async def get_user_transactions(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Transaction]:
        """获取用户交易记录"""
        async with self.get_session() as session:
            stmt = (
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_consumption_record(
        self,
        user_id: str,
        model_name: str,
        provider: str,
        cost_type: str,
        points_used: int = 0,
        amount: int = 0,
        request_id: str = None,
        prompt: str = None,
        image_count: int = 1,
        image_urls: List[str] = None,
        status: str = "success",
        error_reason: str = None,
    ) -> ConsumptionRecord:
        """创建消费记录"""
        async with self.get_session() as session:
            record = ConsumptionRecord(
                user_id=user_id,
                request_id=request_id,
                model_name=model_name,
                provider=provider,
                cost_type=cost_type,
                points_used=points_used,
                amount=amount,
                prompt=prompt,
                image_count=image_count,
                image_urls=image_urls,
                status=status,
                error_reason=error_reason,
            )
            session.add(record)
            await session.flush()
            await session.commit()
            await session.refresh(record)
            logger.info(f"创建消费记录: {record.id}, user={user_id}, model={model_name}, status={status}")
            return record

    async def get_user_consumption_records(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ConsumptionRecord]:
        """获取用户消费记录"""
        async with self.get_session() as session:
            stmt = (
                select(ConsumptionRecord)
                .where(ConsumptionRecord.user_id == user_id)
                .order_by(ConsumptionRecord.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ==================== 提现相关 ====================

    async def create_withdrawal(self, withdrawal: Withdrawal) -> Withdrawal:
        """创建提现申请"""
        async with self.get_session() as session:
            session.add(withdrawal)
            await session.flush()
            await session.commit()
            await session.refresh(withdrawal)
            logger.info(f"创建提现申请: {withdrawal.withdrawal_id}, user_id={withdrawal.user_id}, amount={withdrawal.amount}")
            return withdrawal

    async def get_withdrawal_by_id(self, withdrawal_id: str) -> Optional[Withdrawal]:
        """根据提现单号获取提现记录"""
        async with self.get_session() as session:
            stmt = select(Withdrawal).where(Withdrawal.withdrawal_id == withdrawal_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_withdrawals(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Withdrawal]:
        """获取用户提现记录"""
        async with self.get_session() as session:
            stmt = (
                select(Withdrawal)
                .where(Withdrawal.user_id == user_id)
                .order_by(Withdrawal.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_withdrawals(
        self, status: str = None, limit: int = 50, offset: int = 0
    ) -> List[Withdrawal]:
        """获取所有提现记录（管理员用）"""
        async with self.get_session() as session:
            stmt = select(Withdrawal)
            if status:
                stmt = stmt.where(Withdrawal.status == status)
            stmt = stmt.order_by(Withdrawal.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_withdrawals_count(self, status: str = None) -> int:
        """获取提现记录总数"""
        async with self.get_session() as session:
            from sqlalchemy import func
            stmt = select(func.count(Withdrawal.id))
            if status:
                stmt = stmt.where(Withdrawal.status == status)
            result = await session.execute(stmt)
            return result.scalar()

    async def update_withdrawal(self, withdrawal: Withdrawal) -> Withdrawal:
        """更新提现记录"""
        async with self.get_session() as session:
            await session.merge(withdrawal)
            await session.commit()
            logger.info(f"更新提现记录: {withdrawal.withdrawal_id}, status={withdrawal.status}")
            return withdrawal

    # ==================== 下载记录相关 ====================

    async def create_download_record(self, record: DownloadRecord) -> DownloadRecord:
        """创建下载记录"""
        async with self.get_session() as session:
            session.add(record)
            await session.flush()
            await session.commit()
            await session.refresh(record)
            logger.info(f"创建下载记录: {record.id}, user_id={record.user_id}")
            return record

    async def get_user_download_records(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[DownloadRecord]:
        """获取用户下载记录"""
        async with self.get_session() as session:
            stmt = (
                select(DownloadRecord)
                .where(DownloadRecord.user_id == user_id)
                .order_by(DownloadRecord.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_download_records_count(self, user_id: str) -> int:
        """获取用户下载记录总数"""
        from sqlalchemy import func
        async with self.get_session() as session:
            stmt = select(func.count(DownloadRecord.id)).where(DownloadRecord.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_user_generation_records(
        self, user_id: str, limit: int = 20, offset: int = 0, status: str = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户的图片生成记录

        Args:
            user_id: 用户ID
            limit: 返回记录数量
            offset: 偏移量
            status: 状态筛选 (completed, failed)

        Returns:
            生成记录列表
        """
        async with self.get_session() as session:
            # 构建查询语句
            stmt = (
                select(ImageGenerationRecord, UserRequest)
                .join(UserRequest, ImageGenerationRecord.user_request_id == UserRequest.id)
                .where(UserRequest.user_id == user_id)
            )

            # 添加状态筛选
            if status:
                stmt = stmt.where(ImageGenerationRecord.status == status)

            # 按创建时间倒序排列
            stmt = stmt.order_by(ImageGenerationRecord.created_at.desc())
            stmt = stmt.offset(offset).limit(limit)

            result = await session.execute(stmt)
            records = result.all()

            # 构建返回数据
            record_list = []
            for gen_record, user_request in records:
                # 从request_data中获取prompt
                prompt = gen_record.prompt
                if not prompt and user_request.request_data:
                    prompt = user_request.request_data.get("prompt", "")

                record_list.append({
                    "id": gen_record.id,
                    "user_request_id": gen_record.user_request_id,
                    "provider": gen_record.provider or "unknown",
                    "model": gen_record.model or "unknown",
                    "prompt": prompt or "",
                    "negative_prompt": gen_record.negative_prompt or "",
                    "width": gen_record.width or 1024,
                    "height": gen_record.height or 1024,
                    "n": gen_record.n or 1,
                    "style": gen_record.style,
                    "quality": gen_record.quality,
                    "status": gen_record.status or "unknown",
                    "image_urls": gen_record.image_urls or [],
                    "image_paths": gen_record.image_paths or [],
                    "processing_time": gen_record.processing_time,
                    "start_time": gen_record.start_time.isoformat() if gen_record.start_time else None,
                    "end_time": gen_record.end_time.isoformat() if gen_record.end_time else None,
                    "created_at": gen_record.created_at.isoformat() if gen_record.created_at else None,
                    "extra_params": gen_record.extra_params or {},
                })

            return record_list

    async def get_user_generation_records_count(self, user_id: str, status: str = None) -> int:
        """
        获取用户的图片生成记录总数

        Args:
            user_id: 用户ID
            status: 状态筛选 (completed, failed)

        Returns:
            记录总数
        """
        from sqlalchemy import func
        async with self.get_session() as session:
            stmt = (
                select(func.count(ImageGenerationRecord.id))
                .join(UserRequest, ImageGenerationRecord.user_request_id == UserRequest.id)
                .where(UserRequest.user_id == user_id)
            )

            if status:
                stmt = stmt.where(ImageGenerationRecord.status == status)

            result = await session.execute(stmt)
            return result.scalar() or 0

    # ==================== 管理员相关 ====================

    async def get_users_list(
        self,
        keyword: str = None,
        status: str = None,
        role: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[User]:
        """获取用户列表（支持角色筛选）"""
        from sqlalchemy.orm import selectinload
        async with self.get_session() as session:
            stmt = select(User).options(selectinload(User.account))

            # 筛选条件
            conditions = []
            if keyword:
                conditions.append(
                    or_(
                        User.phone.like(f"%{keyword}%"),
                        User.username.like(f"%{keyword}%"),
                    )
                )
            if status:
                conditions.append(User.status == status)
            if role:
                conditions.append(User.role == role)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_users_count(self, keyword: str = None, status: str = None, role: str = None) -> int:
        """获取用户总数（支持角色筛选）"""
        from sqlalchemy import func
        async with self.get_session() as session:
            stmt = select(func.count(User.id))

            # 筛选条件
            conditions = []
            if keyword:
                conditions.append(
                    or_(
                        User.phone.like(f"%{keyword}%"),
                        User.username.like(f"%{keyword}%"),
                    )
                )
            if status:
                conditions.append(User.status == status)
            if role:
                conditions.append(User.role == role)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_platform_statistics(self) -> Dict[str, Any]:
        """获取平台统计数据"""
        from sqlalchemy import func, select
        from datetime import date, datetime, timedelta

        async with self.get_session() as session:
            # 总用户数
            total_users_stmt = select(func.count(User.id))
            total_users = (await session.execute(total_users_stmt)).scalar() or 0

            # 活跃用户数（最近30天有登录记录）
            active_users_stmt = select(func.count(User.id)).where(
                User.last_login_at >= datetime.now() - timedelta(days=30)
            )
            active_users = (await session.execute(active_users_stmt)).scalar() or 0

            # 今日新增用户
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_users_stmt = select(func.count(User.id)).where(User.created_at >= today_start)
            today_users = (await session.execute(today_users_stmt)).scalar() or 0

            # 账户统计
            accounts_stmt = select(
                func.sum(Account.total_generated).label("total_generated"),
                func.sum(Account.total_spent).label("total_revenue"),
            )
            accounts_result = await session.execute(accounts_stmt)
            row = accounts_result.first()
            total_generated = row.total_generated or 0
            total_revenue = row.total_revenue or 0

            # 今日生成次数和收入（从交易表统计）
            today_transactions_stmt = select(
                func.sum(Transaction.amount).label("today_revenue")
            ).where(
                and_(
                    Transaction.transaction_type == "consumption",
                    Transaction.created_at >= today_start,
                )
            )
            today_revenue_result = await session.execute(today_transactions_stmt)
            today_revenue = abs(today_revenue_result.scalar() or 0)

            # 今日生成次数
            today_generation_stmt = select(func.count(ConsumptionRecord.id)).where(
                and_(
                    ConsumptionRecord.status == "success",
                    ConsumptionRecord.created_at >= today_start,
                )
            )
            today_generated = (await session.execute(today_generation_stmt)).scalar() or 0

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_generated": total_generated,
                "total_revenue": total_revenue,  # 分
                "today_users": today_users,
                "today_generated": today_generated,
                "today_revenue": today_revenue,  # 分
            }


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(database_url: str = None, echo: bool = False) -> DatabaseManager:
    """
    获取数据库管理器实例（单例模式）

    Args:
        database_url: 数据库连接URL
        echo: 是否输出SQL日志

    Returns:
        DatabaseManager实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url=database_url, echo=echo)
    return _db_manager


async def init_db(database_url: str = None, echo: bool = False):
    """
    初始化数据库

    Args:
        database_url: 数据库连接URL
        echo: 是否输出SQL日志
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url=database_url, echo=echo)
    # 自动创建所有表
    async with _db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None
