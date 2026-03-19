"""Async task API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel, Field

from ...config.settings import settings
from ...database import get_db_manager
from ...database.async_task_manager import get_async_task_manager
from .chat import _require_api_key

router = APIRouter(prefix="/api/async", tags=["async"])


class SubmitTaskRequest(BaseModel):
    """Async image task submission request."""

    prompt: str = Field(..., description="提示词")
    model: str = Field(..., description="模型名称")
    width: Optional[int] = Field(1024, description="宽度")
    height: Optional[int] = Field(1024, description="高度")
    n: Optional[int] = Field(1, description="生成数量")
    quality: Optional[str] = Field("standard", description="质量")


class SubmitTaskResponse(BaseModel):
    """Async task submission response."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")


class TaskStatusResponse(BaseModel):
    """Async task status response."""

    task_id: str
    status: str
    progress: float
    result_urls: Optional[List[str]] = None
    error: Optional[str] = None
    submit_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@router.post("/submit", response_model=SubmitTaskResponse)
async def submit_task(request: SubmitTaskRequest, http_request: Request):
    """Submit an async image generation task."""
    try:
        manager = get_async_task_manager()
        db_manager = get_db_manager()

        api_key = _require_api_key(http_request)
        credential_id = None
        credential = await db_manager.store_api_credential(
            api_key=api_key,
            provider="relay",
            base_url=settings.relay_base_url,
            user_id="async-api",
        )
        credential_id = credential.id

        params = {
            "width": request.width,
            "height": request.height,
            "n": request.n,
            "quality": request.quality,
            "credential_id": credential_id,
            "relay_base_url": settings.relay_base_url,
        }

        task = await manager.create_task(
            platform=request.model.split("/")[0] if "/" in request.model else "relay",
            model=request.model,
            prompt=request.prompt,
            params=params,
        )

        logger.info(f"异步任务已提交: {task.id}")

        return SubmitTaskResponse(
            task_id=task.id,
            status=task.status,
        )
    except Exception as exc:
        logger.error(f"提交任务失败: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Query async task status."""
    try:
        manager = get_async_task_manager()
        task = await manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return TaskStatusResponse(
            task_id=task.id,
            status=task.status,
            progress=task.progress or 0.0,
            result_urls=task.result_urls,
            error=task.error,
            submit_time=task.submit_time,
            end_time=task.end_time,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"查询任务状态失败: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
):
    """List async tasks."""
    try:
        manager = get_async_task_manager()
        tasks = await manager.list_tasks(
            status=status,
            platform=platform,
            limit=limit,
        )

        return {
            "tasks": [
                {
                    "task_id": t.id,
                    "status": t.status,
                    "progress": t.progress or 0.0,
                    "prompt": t.prompt[:100] if t.prompt else "",
                    "model": t.model,
                    "platform": t.platform,
                    "submit_time": t.submit_time,
                    "end_time": t.end_time,
                    "result_urls": t.result_urls,
                }
                for t in tasks
            ]
        }
    except Exception as exc:
        logger.error(f"获取任务列表失败: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
