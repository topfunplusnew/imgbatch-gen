"""维护和清理管理API路由"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from loguru import logger

from ...models.cleanup import CleanupReport, CleanupStatus
from ...services.retention_cleanup import get_cleanup_service
from ...scheduler.background_scheduler import get_background_scheduler
from ...config.settings import settings
from ...database.cleanup_models import CleanupHistory
from ...database import get_db_manager
from sqlalchemy import select, desc

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/cleanup/trigger", response_model=CleanupReport)
async def trigger_cleanup(
    retention_days: Optional[int] = Query(None, description="保留天数（默认使用配置值）", ge=1, le=365),
    dry_run: bool = Query(True, description="是否为dry-run模式（仅报告不删除）"),
    batch_size: int = Query(100, description="批次大小", ge=10, le=1000)
):
    """
    手动触发清理任务

    需要管理员权限。

    Args:
        retention_days: 保留天数（默认使用配置值）
        dry_run: 是否为dry-run模式（仅报告不删除）
        batch_size: 批次大小

    Returns:
        CleanupReport: 清理报告
    """
    try:
        # 使用配置值或传入值
        actual_retention_days = retention_days or settings.retention_days

        logger.info(
            f"手动触发清理任务: "
            f"保留期={actual_retention_days}天, "
            f"dry_run={dry_run}, "
            f"批次大小={batch_size}"
        )

        # 获取清理服务
        cleanup_service = get_cleanup_service()

        # 执行清理
        report = await cleanup_service.cleanup_expired_records(
            retention_days=actual_retention_days,
            batch_size=batch_size,
            dry_run=dry_run
        )

        # 标记为手动触发
        report.triggered_by = "manual"

        # 保存到历史记录
        await _save_cleanup_history(report)

        return report

    except Exception as e:
        logger.error(f"手动触发清理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@router.get("/cleanup/status", response_model=CleanupStatus)
async def get_cleanup_status():
    """
    获取清理任务状态

    Returns:
        CleanupStatus: 清理状态信息
    """
    try:
        # 获取调度器状态
        scheduler = get_background_scheduler()

        # 获取最近一次清理历史
        last_cleanup = await _get_last_cleanup_history()

        # 构建状态响应
        status = CleanupStatus(
            scheduler_running=scheduler.is_running(),
            cleanup_interval_hours=settings.cleanup_interval_hours,
            retention_days=settings.retention_days,
            cleanup_dry_run=settings.cleanup_dry_run,
            cleanup_on_startup=settings.cleanup_on_startup
        )

        # 填充最近一次清理信息
        if last_cleanup:
            status.last_cleanup_time = last_cleanup.started_at
            status.last_cleanup_status = last_cleanup.status
            status.last_cleanup_records_deleted = (
                last_cleanup.total_image_records_deleted +
                last_cleanup.total_chat_records_deleted +
                last_cleanup.total_user_requests_deleted
            )
            status.last_cleanup_storage_freed = last_cleanup.total_storage_freed_bytes

        # 填充下一次清理时间
        if scheduler.is_running():
            next_run = scheduler.get_next_run_time("retention_cleanup")
            if next_run:
                status.next_cleanup_time = next_run

        return status

    except Exception as e:
        logger.error(f"获取清理状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/cleanup/history")
async def get_cleanup_history(
    limit: int = Query(10, description="返回记录数", ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="状态过滤: running/completed/failed")
):
    """
    获取清理历史记录

    Args:
        limit: 返回记录数
        status_filter: 状态过滤

    Returns:
        List[CleanupHistory]: 清理历史记录列表
    """
    try:
        db_manager = await get_db_manager()

        async with db_manager.get_session() as session:
            query = select(CleanupHistory)

            # 应用状态过滤
            if status_filter:
                query = query.where(CleanupHistory.status == status_filter)

            # 排序和限制
            query = query.order_by(desc(CleanupHistory.started_at)).limit(limit)

            result = await session.execute(query)
            history_records = result.scalars().all()

            # 转换为字典列表
            return [record.to_dict() for record in history_records]

    except Exception as e:
        logger.error(f"获取清理历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.post("/cleanup/scheduler/start")
async def start_scheduler():
    """启动清理调度器"""
    try:
        scheduler = get_background_scheduler()

        if scheduler.is_running():
            return {"message": "调度器已在运行中", "running": True}

        await scheduler.start()

        # 重新安排清理任务
        cleanup_service = get_cleanup_service()
        interval_seconds = settings.cleanup_interval_hours * 3600
        scheduler.schedule_periodic(
            name="retention_cleanup",
            interval_seconds=interval_seconds,
            coroutine_func=cleanup_service.cleanup_expired_records,
            retention_days=settings.retention_days,
            batch_size=settings.cleanup_batch_size,
            dry_run=settings.cleanup_dry_run
        )

        return {"message": "调度器已启动", "running": True}

    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/cleanup/scheduler/stop")
async def stop_scheduler():
    """停止清理调度器"""
    try:
        scheduler = get_background_scheduler()

        if not scheduler.is_running():
            return {"message": "调度器未在运行", "running": False}

        await scheduler.stop()

        return {"message": "调度器已停止", "running": False}

    except Exception as e:
        logger.error(f"停止调度器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")


async def _save_cleanup_history(report: CleanupReport):
    """保存清理历史记录"""
    try:
        db_manager = await get_db_manager()

        async with db_manager.get_session() as session:
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


async def _get_last_cleanup_history() -> Optional[CleanupHistory]:
    """获取最近一次清理历史"""
    try:
        db_manager = await get_db_manager()

        async with db_manager.get_session() as session:
            query = select(CleanupHistory).order_by(desc(CleanupHistory.started_at)).limit(1)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    except Exception as e:
        logger.error(f"获取清理历史失败: {str(e)}")
        return None
