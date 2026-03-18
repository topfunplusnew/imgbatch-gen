"""异步任务数据库管理器"""

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from .async_task_models import AsyncTask
from ..config.settings import settings


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        # 使用独立的数据库
        db_url = "sqlite+aiosqlite:///./data/async_tasks.db"
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """初始化数据库"""
        from .async_task_models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("异步任务数据库初始化完成")

    async def create_task(
        self,
        platform: str,
        model: str,
        prompt: str,
        params: dict,
        platform_task_id: Optional[str] = None
    ) -> AsyncTask:
        """创建任务"""
        async with self.async_session() as session:
            task = AsyncTask(
                id=str(uuid.uuid4()),
                platform_task_id=platform_task_id,
                platform=platform,
                model=model,
                prompt=prompt,
                params=params,
                status="pending",
                submit_time=datetime.now()
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """获取任务"""
        async with self.async_session() as session:
            result = await session.execute(
                select(AsyncTask).where(AsyncTask.id == task_id)
            )
            return result.scalar_one_or_none()

    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result_urls: Optional[List[str]] = None,
        error: Optional[str] = None
    ):
        """更新任务"""
        async with self.async_session() as session:
            result = await session.execute(
                select(AsyncTask).where(AsyncTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task:
                return

            if status:
                task.status = status
                if status == "processing" and not task.start_time:
                    task.start_time = datetime.now()
                elif status in ["completed", "failed"]:
                    task.end_time = datetime.now()

            if progress is not None:
                task.progress = progress
            if result_urls is not None:
                task.result_urls = result_urls
            if error is not None:
                task.error = error

            await session.commit()

    async def list_tasks(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[AsyncTask]:
        """获取任务列表"""
        async with self.async_session() as session:
            query = select(AsyncTask).order_by(AsyncTask.created_at.desc())

            if status:
                query = query.where(AsyncTask.status == status)
            if platform:
                query = query.where(AsyncTask.platform == platform)

            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())


_manager: Optional[AsyncTaskManager] = None

def get_async_task_manager() -> AsyncTaskManager:
    """获取全局管理器实例"""
    global _manager
    if _manager is None:
        _manager = AsyncTaskManager()
    return _manager
