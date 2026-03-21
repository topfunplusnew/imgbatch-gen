"""任务管理器"""

import asyncio
import uuid
from typing import Dict, Optional, List, Any
from datetime import datetime
from loguru import logger

from ..models.task import ImageTask, TaskStatus, BatchTask
from ..models.image import ImageParams
from ..config.settings import settings
from .queue import TaskQueue
from .worker import Worker
from ..storage import get_storage, MetadataManager


class TaskManager:
    """任务管理器"""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        extractor_provider: Optional[str] = None,
        matcher_provider: Optional[str] = None,
    ):
        """初始化任务管理器"""
        self.max_workers = max_workers or settings.max_concurrent_tasks
        self.queue = TaskQueue()
        self.workers: List[Worker] = []
        self.tasks: Dict[str, ImageTask] = {}
        self.batch_tasks: Dict[str, BatchTask] = {}
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # 初始化存储
        self.storage = get_storage()

        # 初始化元数据管理器，使用配置的存储类型
        self.metadata_manager = MetadataManager(storage_type=settings.storage_type)
        
        # Provider配置
        self.extractor_provider = extractor_provider
        self.matcher_provider = matcher_provider
    
    async def start(self):
        """启动任务管理器"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"启动任务管理器，工作协程数: {self.max_workers}")
        
        # 创建工作协程
        for i in range(self.max_workers):
            worker = Worker(
                worker_id=i,
                storage=self.storage,
                metadata_manager=self.metadata_manager,
                extractor_provider=self.extractor_provider,
                matcher_provider=self.matcher_provider,
            )
            self.workers.append(worker)
            # 启动工作协程
            task = asyncio.create_task(self._worker_loop(worker))
            self.worker_tasks.append(task)
    
    async def stop(self):
        """停止任务管理器"""
        self.running = False
        logger.info("停止任务管理器")
        
        # 取消所有工作协程任务
        for task in self.worker_tasks:
            if not task.done():
                task.cancel()
        
        # 等待所有工作协程完成（包括被取消的）
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        self.workers.clear()
        logger.info("任务管理器已停止")
    
    async def _worker_loop(self, worker: Worker):
        """工作协程循环"""
        while self.running:
            try:
                # 使用超时机制，定期检查 running 状态
                try:
                    task = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    # 超时后检查是否还在运行
                    if not self.running:
                        break
                    continue
                
                if task is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # 处理任务
                result = await worker.process_task(task)
                
                # 更新任务状态
                self.tasks[result.task_id] = result
                
                # 更新批量任务进度
                if result.task_id in [t.task_id for batch in self.batch_tasks.values() for t in batch.tasks]:
                    for batch in self.batch_tasks.values():
                        if any(t.task_id == result.task_id for t in batch.tasks):
                            batch.update_progress()
                            break
                
            except Exception as e:
                logger.error(f"工作协程 {worker.worker_id} 错误: {str(e)}")
                await asyncio.sleep(1)
    
    def create_task(self, params: ImageParams, user_input: Optional[str] = None, user_request_id: Optional[str] = None, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ImageTask:
        """创建任务"""
        from loguru import logger
        task_id = str(uuid.uuid4())

        logger.info(f"[TaskManager] 创建任务 {task_id}")
        logger.info(f"[TaskManager] 参数: width={params.width}, height={params.height}, quality={params.quality}, n={params.n}")
        logger.info(f"[TaskManager] prompt: {params.prompt[:50]}...")
        logger.info(f"[TaskManager] provider: {params.provider}")

        # 合并默认元数据和传入的元数据
        default_metadata = {
            "user_input": user_input or params.prompt,
            "created_by": "task_manager",
        }
        if metadata:
            default_metadata.update(metadata)

        task = ImageTask(
            task_id=task_id,
            user_id=user_id,
            user_request_id=user_request_id,
            status=TaskStatus.PENDING,
            params=params,
            metadata=default_metadata
        )

        self.tasks[task_id] = task
        logger.info(f"[TaskManager] 任务 {task_id} 创建完成，当前任务数: {len(self.tasks)}")
        return task
    
    async def submit_task(self, task: ImageTask, priority: int = 0):
        """提交任务到队列"""
        await self.queue.put(task, priority=priority)
        logger.info(f"提交任务 {task.task_id} 到队列")
    
    def get_task(self, task_id: str) -> Optional[ImageTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    async def create_batch_task(
        self,
        params_list: List[ImageParams],
        user_inputs: Optional[List[str]] = None,
        user_request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BatchTask:
        """创建批量任务"""
        batch_id = str(uuid.uuid4())
        tasks = []

        for i, params in enumerate(params_list):
            user_input = user_inputs[i] if user_inputs and i < len(user_inputs) else None
            # 为每个子任务添加 metadata
            task_metadata = metadata.copy() if metadata else {}
            task_metadata["batch_id"] = batch_id
            task_metadata["task_index"] = i

            task = self.create_task(params, user_input, user_request_id, user_id, task_metadata)
            tasks.append(task)

        batch_task = BatchTask(
            batch_id=batch_id,
            user_request_id=user_request_id,
            tasks=tasks,
            total=len(tasks),
        )

        self.batch_tasks[batch_id] = batch_task

        # 提交所有子任务
        for task in tasks:
            await self.submit_task(task)

        logger.info(f"创建批量任务 {batch_id}，包含 {len(tasks)} 个子任务")
        return batch_task
    
    def get_batch_task(self, batch_id: str) -> Optional[BatchTask]:
        """获取批量任务"""
        return self.batch_tasks.get(batch_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[ImageTask]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

