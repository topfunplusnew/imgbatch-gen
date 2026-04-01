"""任务队列"""

import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import itertools

from ..models.task import ImageTask, TaskStatus


@dataclass
class QueueItem:
    """队列项"""
    task: ImageTask
    priority: int = 0  # 优先级，数字越大优先级越高
    created_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """任务队列"""
    
    def __init__(self):
        """初始化队列"""
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._task_map: dict[str, ImageTask] = {}
        # PriorityQueue 在优先级/时间戳相同的情况下会继续比较后续元素；
        # 加一个递增序号作为稳定的 tie-breaker，避免比较 QueueItem 本身导致 TypeError
        self._seq = itertools.count()
    
    async def put(self, task: ImageTask, priority: int = 0):
        """添加任务到队列"""
        item = QueueItem(task=task, priority=priority)
        # PriorityQueue使用元组排序，负数实现大数优先
        await self._queue.put((-priority, item.created_at.timestamp(), next(self._seq), item))
        self._task_map[task.task_id] = task
    
    async def get(self) -> Optional[ImageTask]:
        """从队列获取任务"""
        try:
            _, _, _, item = await self._queue.get()
            return item.task
        except asyncio.CancelledError:
            # 任务被取消时，重新抛出异常
            raise
        except Exception:
            return None
    
    def get_task(self, task_id: str) -> Optional[ImageTask]:
        """根据task_id获取任务"""
        return self._task_map.get(task_id)
    
    def remove_task(self, task_id: str):
        """从队列中移除任务"""
        if task_id in self._task_map:
            del self._task_map[task_id]
    
    def size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()

