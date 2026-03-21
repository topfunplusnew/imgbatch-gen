"""后台任务调度器 - 基于asyncio的轻量级调度器"""

import asyncio
from typing import Callable, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


class BackgroundScheduler:
    """轻量级后台任务调度器"""

    def __init__(self):
        """初始化调度器"""
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        self.task_configs: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已经在运行中")
            return

        self.running = True
        logger.info("后台调度器已启动")

    async def stop(self):
        """停止调度器"""
        if not self.running:
            logger.warning("调度器未在运行")
            return

        logger.info("正在停止后台调度器...")
        self.running = False

        # 取消所有任务
        for task_name, task in self.tasks.items():
            if not task.done():
                logger.debug(f"取消任务: {task_name}")
                task.cancel()

        # 等待所有任务完成（或被取消）
        if self.tasks:
            results = await asyncio.gather(*self.tasks.values(), return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = list(self.tasks.keys())[i]
                    logger.warning(f"任务 {task_name} 停止时出现异常: {result}")

        self.tasks.clear()
        self.task_configs.clear()
        logger.info("后台调度器已停止")

    def schedule_periodic(
        self,
        name: str,
        interval_seconds: int,
        coroutine_func: Callable,
        *args,
        **kwargs
    ):
        """
        安排周期性任务

        Args:
            name: 任务名称
            interval_seconds: 执行间隔（秒）
            coroutine_func: 要执行的协程函数
            *args, **kwargs: 传递给协程函数的参数
        """
        if name in self.tasks:
            logger.warning(f"任务 {name} 已存在，将先取消旧任务")
            self.cancel_task(name)

        # 保存任务配置
        self.task_configs[name] = {
            "interval_seconds": interval_seconds,
            "last_run": None,
            "next_run": datetime.utcnow() + timedelta(seconds=interval_seconds)
        }

        # 创建周期性任务
        task = asyncio.create_task(
            self._periodic_wrapper(name, interval_seconds, coroutine_func, *args, **kwargs)
        )
        self.tasks[name] = task

        logger.info(
            f"已安排周期性任务: {name}, "
            f"间隔: {interval_seconds}秒, "
            f"下次运行: {self.task_configs[name]['next_run']}"
        )

    async def _periodic_wrapper(
        self,
        name: str,
        interval_seconds: int,
        coroutine_func: Callable,
        *args,
        **kwargs
    ):
        """周期性任务包装器"""
        logger.info(f"周期性任务 {name} 开始运行")

        while self.running:
            try:
                # 更新配置
                self.task_configs[name]["last_run"] = datetime.utcnow()
                self.task_configs[name]["next_run"] = datetime.utcnow() + timedelta(seconds=interval_seconds)

                # 执行任务
                logger.info(f"执行周期性任务: {name}")
                result = await coroutine_func(*args, **kwargs)

                # 记录结果
                if hasattr(result, 'status'):
                    logger.info(
                        f"任务 {name} 完成: "
                        f"状态={result.status}, "
                        f"耗时={result.duration_seconds:.2f}秒"
                    )
                else:
                    logger.info(f"任务 {name} 完成")

                # 等待下一次执行
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                logger.info(f"任务 {name} 被取消")
                break
            except Exception as e:
                logger.error(f"任务 {name} 执行失败: {str(e)}", exc_info=True)
                # 等待后重试
                await asyncio.sleep(interval_seconds)

        logger.info(f"周期性任务 {name} 已停止")

    def schedule_once(
        self,
        name: str,
        delay_seconds: int,
        coroutine_func: Callable,
        *args,
        **kwargs
    ):
        """
        安排一次性延迟任务

        Args:
            name: 任务名称
            delay_seconds: 延迟时间（秒）
            coroutine_func: 要执行的协程函数
            *args, **kwargs: 传递给协程函数的参数
        """
        if name in self.tasks:
            logger.warning(f"任务 {name} 已存在，将先取消旧任务")
            self.cancel_task(name)

        # 创建一次性任务
        async def once_wrapper():
            try:
                logger.info(f"等待 {delay_seconds} 秒后执行一次性任务: {name}")
                await asyncio.sleep(delay_seconds)
                logger.info(f"执行一次性任务: {name}")
                result = await coroutine_func(*args, **kwargs)
                logger.info(f"一次性任务 {name} 完成")
                # 从任务列表中移除
                self.tasks.pop(name, None)
                self.task_configs.pop(name, None)
                return result
            except asyncio.CancelledError:
                logger.info(f"一次性任务 {name} 被取消")
                self.tasks.pop(name, None)
                self.task_configs.pop(name, None)
            except Exception as e:
                logger.error(f"一次性任务 {name} 执行失败: {str(e)}")
                self.tasks.pop(name, None)
                self.task_configs.pop(name, None)

        task = asyncio.create_task(once_wrapper())
        self.tasks[name] = task

        logger.info(f"已安排一次性任务: {name}, 延迟: {delay_seconds}秒")

    def cancel_task(self, name: str):
        """取消指定任务"""
        if name in self.tasks:
            task = self.tasks[name]
            if not task.done():
                task.cancel()
                logger.info(f"已取消任务: {name}")
            self.tasks.pop(name, None)
            self.task_configs.pop(name, None)
        else:
            logger.warning(f"任务 {name} 不存在")

    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if name not in self.task_configs:
            return None

        config = self.task_configs[name].copy()
        task = self.tasks.get(name)

        if task:
            if task.done():
                if task.exception():
                    config["status"] = "failed"
                    config["error"] = str(task.exception())
                else:
                    config["status"] = "completed"
            else:
                config["status"] = "running"

        return config

    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        return {
            name: self.get_task_status(name)
            for name in self.task_configs.keys()
        }

    def get_next_run_time(self, name: str) -> Optional[datetime]:
        """获取指定任务的下次运行时间"""
        if name in self.task_configs:
            return self.task_configs[name].get("next_run")
        return None

    def get_last_run_time(self, name: str) -> Optional[datetime]:
        """获取指定任务的上次运行时间"""
        if name in self.task_configs:
            return self.task_configs[name].get("last_run")
        return None

    def is_running(self) -> bool:
        """检查调度器是否在运行"""
        return self.running

    def get_task_count(self) -> int:
        """获取当前任务数量"""
        return len(self.tasks)


# 全局调度器实例
_scheduler: Optional[BackgroundScheduler] = None


def get_background_scheduler() -> BackgroundScheduler:
    """获取全局后台调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler
