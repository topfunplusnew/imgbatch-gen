"""Persistence operations for conversation history."""

from typing import Optional, Tuple

from sqlalchemy import and_, func, select

from .. import get_db_manager
from ..manager import DatabaseManager
from ..models import ChatConversation, ConversationSession, UploadedFile


class HistoryRepository:
    """Repository for conversation history data access."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or get_db_manager()

    async def create_session(
        self,
        session_id: str,
        title: str,
        model: str,
        provider: str,
        client_id: str,
    ) -> None:
        await self.db_manager.create_conversation_session(
            session_id=session_id,
            title=title,
            model=model,
            provider=provider,
            status="active",
            client_id=client_id,
        )

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str,
        provider: str,
        images: Optional[str],
        files: Optional[str],
        user_request_id: Optional[str],
    ) -> None:
        await self.db_manager.create_chat_message(
            session_id=session_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            images=images,
            files=files,
            user_request_id=user_request_id,
        )

    async def list_active_conversations(self, client_id: str, limit: int, offset: int):
        async with self.db_manager.get_session() as session:
            stmt = (
                select(
                    ConversationSession.session_id,
                    ConversationSession.title,
                    ConversationSession.created_at,
                    ConversationSession.updated_at,
                    ConversationSession.image_count,
                    func.count(ChatConversation.id).label("message_count"),
                )
                .outerjoin(
                    ChatConversation,
                    ChatConversation.session_id == ConversationSession.session_id,
                )
                .where(
                    and_(
                        ConversationSession.status == "active",
                        ConversationSession.client_id == client_id,
                    )
                )
                .group_by(
                    ConversationSession.session_id,
                    ConversationSession.title,
                    ConversationSession.created_at,
                    ConversationSession.updated_at,
                    ConversationSession.image_count,
                )
                .order_by(ConversationSession.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.all()

    async def get_conversation_detail(
        self, session_id: str
    ) -> Tuple[Optional[ConversationSession], list[ChatConversation], list[UploadedFile]]:
        async with self.db_manager.get_session() as session:
            session_stmt = select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
            session_result = await session.execute(session_stmt)
            session_obj = session_result.scalars().first()

            if not session_obj:
                return None, [], []

            msg_stmt = (
                select(ChatConversation)
                .where(ChatConversation.session_id == session_id)
                .order_by(ChatConversation.created_at.asc())
            )
            msg_result = await session.execute(msg_stmt)
            messages = list(msg_result.scalars().all())

            file_stmt = (
                select(UploadedFile)
                .where(UploadedFile.conversation_id == session_id)
                .where(UploadedFile.status == "active")
                .order_by(UploadedFile.created_at.asc())
            )
            file_result = await session.execute(file_stmt)
            files = list(file_result.scalars().all())

        return session_obj, messages, files

    async def delete_conversation(self, session_id: str) -> int:
        deleted_count = 0

        async with self.db_manager.get_session() as session:
            session_stmt = select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
            session_result = await session.execute(session_stmt)
            session_obj = session_result.scalars().first()

            msg_stmt = select(ChatConversation).where(ChatConversation.session_id == session_id)
            msg_result = await session.execute(msg_stmt)
            messages = list(msg_result.scalars().all())

            if session_obj:
                await session.delete(session_obj)
                deleted_count += 1

            for msg in messages:
                await session.delete(msg)
                deleted_count += 1

            await session.commit()

        return deleted_count

    async def get_chat_messages(self, session_id: str):
        return await self.db_manager.get_chat_messages(session_id)

    async def update_session_title(self, session_id: str, title: str) -> None:
        await self.db_manager.update_conversation_session(session_id, title=title)
