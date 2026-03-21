"""数据保留清理服务 - 自动清理过期记录和文件"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
from loguru import logger

from ..models.cleanup import CleanupReport
from ..database.manager import DatabaseManager
from ..database.models import ImageGenerationRecord, ChatConversation, UserRequest
from ..database.cleanup_models import CleanupHistory
from ..storage.local_storage import LocalStorage
from ..storage.minio_storage import MinioStorage
from ..config.settings import settings


class RetentionCleanupService:
    """数据保留清理服务 - 自动清理过期记录和关联文件"""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        storage_type: Optional[str] = None
    ):
        """
        初始化清理服务

        Args:
            db_manager: 数据库管理器（可选，默认使用全局实例）
            storage_type: 存储类型（可选，默认从配置读取）
        """
        self.db_manager = db_manager
        self.storage_type = storage_type or settings.storage_type

        # 存储实例（延迟初始化）
        self._local_storage = None
        self._minio_storage = None

    def _get_local_storage(self) -> LocalStorage:
        """获取本地存储实例"""
        if self._local_storage is None:
            self._local_storage = LocalStorage()
        return self._local_storage

    def _get_minio_storage(self) -> MinioStorage:
        """获取MinIO存储实例"""
        if self._minio_storage is None:
            self._minio_storage = MinioStorage()
        return self._minio_storage

    async def cleanup_expired_records(
        self,
        retention_days: int = 90,
        batch_size: int = 100,
        dry_run: bool = False
    ) -> CleanupReport:
        """
        清理过期记录

        Args:
            retention_days: 保留天数（默认90天）
            batch_size: 批次大小（每次处理的记录数）
            dry_run: 是否为dry-run模式（仅报告不删除）

        Returns:
            CleanupReport: 清理报告
        """
        report = CleanupReport(
            retention_days=retention_days,
            cutoff_date=datetime.utcnow() - timedelta(days=retention_days),
            dry_run=dry_run,
            triggered_by="manual"
        )

        logger.info(f"开始清理过期记录，保留期: {retention_days}天，截止日期: {report.cutoff_date}")

        try:
            # 如果没有传入db_manager，使用全局实例
            if self.db_manager is None:
                from ..database import get_db_manager
                self.db_manager = await get_db_manager()

            # 第一步：查询所有过期的图片生成记录
            expired_image_records = await self._get_expired_image_records(
                report.cutoff_date,
                batch_size
            )

            logger.info(f"找到 {len(expired_image_records)} 条过期图片记录")

            if dry_run:
                logger.info("DRY-RUN模式：仅报告不删除")

            # 第二步：处理每条过期记录
            for record in expired_image_records:
                try:
                    await self._cleanup_single_record(record, report, dry_run)
                except Exception as e:
                    error_msg = f"清理记录 {record.id} 失败: {str(e)}"
                    logger.error(error_msg)
                    report.add_error(error_msg)

            # 第三步：清理孤立的用户请求和对话记录
            await self._cleanup_orphaned_records(report, dry_run)

            # 标记完成
            report.mark_completed()

            logger.info(
                f"清理完成: "
                f"图片记录={report.total_image_records_deleted}, "
                f"对话记录={report.total_chat_records_deleted}, "
                f"用户请求={report.total_user_requests_deleted}, "
                f"图片文件={report.total_image_files_deleted}, "
                f"释放空间={report.get_storage_freed_mb():.2f}MB"
            )

        except Exception as e:
            error_msg = f"清理任务失败: {str(e)}"
            logger.error(error_msg)
            report.mark_failed(error_msg)

        # 保存清理历史到数据库
        await self._save_cleanup_history(report)

        return report

    async def _save_cleanup_history(self, report: CleanupReport):
        """保存清理历史到数据库"""
        try:
            async with self.db_manager.get_session() as session:
                history = CleanupHistory(
                    retention_days=report.retention_days,
                    cutoff_date=report.cutoff_date,
                    dry_run=report.dry_run,
                    total_image_records_deleted=report.total_image_records_deleted,
                    total_chat_records_deleted=report.total_chat_records_deleted,
                    total_user_requests_deleted=report.total_user_requests_deleted,
                    total_image_files_deleted=report.total_image_files_deleted,
                    total_storage_freed_bytes=report.total_storage_freed_bytes,
                    error_count=len(report.errors),
                    errors=report.errors,
                    failed_image_deletions=report.failed_image_deletions,
                    triggered_by=report.triggered_by,
                    started_at=report.started_at,
                    completed_at=report.completed_at,
                    duration_seconds=report.duration_seconds,
                    status=report.status
                )

                session.add(history)
                await session.commit()

                logger.info(f"已保存清理历史记录: {history.id}")

        except Exception as e:
            logger.error(f"保存清理历史失败: {str(e)}")

    async def _get_expired_image_records(
        self,
        cutoff_date: datetime,
        batch_size: int
    ) -> List[ImageGenerationRecord]:
        """获取过期的图片生成记录"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select

            stmt = select(ImageGenerationRecord).where(
                ImageGenerationRecord.created_at < cutoff_date
            ).limit(batch_size)

            result = await session.execute(stmt)
            records = result.scalars().all()

            # 转换为列表，避免会话关闭后无法访问
            return list(records)

    async def _cleanup_single_record(
        self,
        record: ImageGenerationRecord,
        report: CleanupReport,
        dry_run: bool
    ):
        """清理单条记录"""
        # 收集需要删除的图片路径
        image_paths_to_delete = self._collect_image_paths(record)

        # 删除图片文件
        for image_path in image_paths_to_delete:
            try:
                file_size = await self._delete_image_file(image_path, dry_run)
                if file_size and file_size > 0:
                    report.total_image_files_deleted += 1
                    report.total_storage_freed_bytes += file_size
            except Exception as e:
                report.add_failed_deletion(image_path, str(e), self.storage_type)

        # 删除数据库记录
        if not dry_run:
            async with self.db_manager.get_session() as session:
                from sqlalchemy import delete

                # 删除图片记录
                stmt = delete(ImageGenerationRecord).where(
                    ImageGenerationRecord.id == record.id
                )
                await session.execute(stmt)
                await session.commit()

                report.total_image_records_deleted += 1

                logger.debug(f"已删除图片记录: {record.id}")
        else:
            report.total_image_records_deleted += 1

    def _collect_image_paths(self, record: ImageGenerationRecord) -> Set[str]:
        """从记录中收集所有图片路径"""
        paths = set()

        # 从image_paths字段收集
        if record.image_paths:
            if isinstance(record.image_paths, list):
                paths.update(record.image_paths)
            elif isinstance(record.image_paths, str):
                paths.add(record.image_paths)

        # 从image_urls字段提取路径（如果是本地路径）
        if record.image_urls:
            if isinstance(record.image_urls, list):
                for url in record.image_urls:
                    # 提取URL中的路径部分
                    if '/storage/' in url:
                        path = url.split('/storage/', 1)[1]
                        paths.add(path)
                    elif url.startswith('/'):
                        paths.add(url.lstrip('/'))
            elif isinstance(record.image_urls, str):
                if '/storage/' in record.image_urls:
                    path = record.image_urls.split('/storage/', 1)[1]
                    paths.add(path)

        return paths

    async def _delete_image_file(
        self,
        image_path: str,
        dry_run: bool
    ) -> Optional[int]:
        """
        删除图片文件

        Returns:
            文件大小（字节），如果文件不存在或删除失败则返回None
        """
        if dry_run:
            # Dry-run模式：仅检查文件是否存在
            if self.storage_type == "local":
                full_path = Path(settings.storage_path) / image_path
                if full_path.exists():
                    return full_path.stat().st_size
            elif self.storage_type == "minio":
                # MinIO无法在dry-run模式下获取文件大小，返回0
                return 0
            return None

        # 实际删除
        if self.storage_type == "local":
            return await self._delete_local_image(image_path)
        elif self.storage_type == "minio":
            return await self._delete_minio_image(image_path)
        else:
            logger.warning(f"未知的存储类型: {self.storage_type}")
            return None

    async def _delete_local_image(self, image_path: str) -> Optional[int]:
        """删除本地图片"""
        full_path = Path(settings.storage_path) / image_path

        if full_path.exists():
            file_size = full_path.stat().st_size
            full_path.unlink()

            # 同时删除缩略图（如果存在）
            thumb_path = full_path.parent / (full_path.stem + "_thumb.jpg")
            if thumb_path.exists():
                thumb_path.unlink()

            logger.debug(f"已删除本地图片: {image_path}")
            return file_size
        else:
            logger.debug(f"本地图片不存在: {image_path}")
            return None

    async def _delete_minio_image(self, image_path: str) -> Optional[int]:
        """删除MinIO图片"""
        try:
            minio_storage = self._get_minio_storage()

            # 提取对象名称（image_path可能包含完整路径）
            # 假设image_path格式为: YYYY-MM-DD/task_id/timestamp_uuid.ext
            object_name = image_path.lstrip('/')

            # 获取对象信息以获取文件大小
            try:
                from minio.error import S3Error
                stat = minio_storage.client.stat_object(
                    minio_storage.bucket_name,
                    object_name
                )
                file_size = stat.size
            except S3Error:
                # 对象不存在
                logger.debug(f"MinIO对象不存在: {object_name}")
                return None

            # 删除对象
            minio_storage.client.remove_object(
                minio_storage.bucket_name,
                object_name
            )

            # 同时删除缩略图（如果存在）
            thumb_object_name = object_name.rsplit('.', 1)[0] + '_thumb.jpg'
            try:
                minio_storage.client.remove_object(
                    minio_storage.bucket_name,
                    thumb_object_name
                )
            except S3Error:
                pass  # 缩略图不存在，忽略

            logger.debug(f"已删除MinIO对象: {object_name}")
            return file_size

        except Exception as e:
            logger.error(f"删除MinIO图片失败: {image_path}, 错误: {str(e)}")
            return None

    async def _cleanup_orphaned_records(
        self,
        report: CleanupReport,
        dry_run: bool
    ):
        """清理孤立的用户请求和对话记录"""
        # 清理没有关联生成记录的用户请求
        await self._cleanup_orphaned_user_requests(report, dry_run)

        # 清理没有关联会话的对话记录
        await self._cleanup_orphaned_chat_conversations(report, dry_run)

    async def _cleanup_orphaned_user_requests(
        self,
        report: CleanupReport,
        dry_run: bool
    ):
        """清理孤立的用户请求"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select, delete, func
            from sqlalchemy.orm import aliased

            # 查找没有关联生成记录的用户请求
            subquery = select(ImageGenerationRecord.user_request_id).where(
                ImageGenerationRecord.user_request_id.isnot(None)
            )

            stmt = select(UserRequest).where(
                UserRequest.created_at < report.cutoff_date,
                ~UserRequest.id.in_(subquery)
            )

            result = await session.execute(stmt)
            orphaned_requests = result.scalars().all()

            for request in orphaned_requests:
                if not dry_run:
                    await session.execute(
                        delete(UserRequest).where(UserRequest.id == request.id)
                    )
                    await session.commit()

                report.total_user_requests_deleted += 1

            logger.debug(f"清理了 {len(orphaned_requests)} 条孤立用户请求")

    async def _cleanup_orphaned_chat_conversations(
        self,
        report: CleanupReport,
        dry_run: bool
    ):
        """清理孤立的对话记录"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select, delete

            # 查找没有关联会话的对话记录
            stmt = select(ChatConversation).where(
                ChatConversation.created_at < report.cutoff_date,
                ChatConversation.session_id.is_(None)
            )

            result = await session.execute(stmt)
            orphaned_conversations = result.scalars().all()

            for conversation in orphaned_conversations:
                if not dry_run:
                    await session.execute(
                        delete(ChatConversation).where(
                            ChatConversation.id == conversation.id
                        )
                    )
                    await session.commit()

                report.total_chat_records_deleted += 1

            logger.debug(f"清理了 {len(orphaned_conversations)} 条孤立对话记录")


# 全局清理服务实例
_cleanup_service: Optional[RetentionCleanupService] = None


def get_cleanup_service() -> RetentionCleanupService:
    """获取全局清理服务实例"""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = RetentionCleanupService()
    return _cleanup_service
