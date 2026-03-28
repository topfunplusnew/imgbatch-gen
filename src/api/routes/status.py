"""任务状态查询接口"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from ...models.task import ImageTask, BatchTask, TaskStatus
from ...engine import TaskManager

router = APIRouter(prefix="/api/v1", tags=["tasks"])


def get_task_manager(request: Request) -> TaskManager:
    """获取任务管理器（依赖注入）"""
    return request.app.state.task_manager


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """查询任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.to_response_dict()


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """获取任务结果"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task.status}")

    return task.to_response_dict()


@router.get("/batch/{batch_id}")
async def get_batch_task(
    batch_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """查询批量任务状态"""
    batch_task = task_manager.get_batch_task(batch_id)
    if not batch_task:
        raise HTTPException(status_code=404, detail="批量任务不存在")
    return batch_task.to_response_dict()


@router.get("/tasks")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """列出任务"""
    tasks = task_manager.list_tasks(status)
    return [task.to_response_dict() for task in tasks]
