"""异步Provider基类 - 用于需要轮询的模型"""

import asyncio
from abc import abstractmethod
from typing import Optional, List, Dict, Any
from loguru import logger

from .base import BaseProvider
from .relay_client import RelayClient
from ..models.image import ImageParams


class AsyncBaseProvider(BaseProvider):
    """异步Provider基类"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        poll_interval: float = 3.0,
        max_poll_time: float = 300.0
    ):
        self.client = RelayClient(base_url, api_key)
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time

    def build_request_params(self, params: ImageParams) -> Dict[str, Any]:
        """构建请求参数（子类可重写以适配不同平台）"""
        return {
            "prompt": params.prompt,
            "width": params.width,
            "height": params.height,
            "seed": params.seed,
        }

    async def generate_image(self, params: ImageParams) -> bytes:
        """生成单张图片"""
        single_params = params.model_copy(update={"n": 1})
        return await self._generate_single(single_params)

    async def generate_images(self, params: ImageParams) -> List[bytes]:
        """批量生成"""
        if self.supports_parallel():
            tasks = [self._generate_single(params) for _ in range(params.n)]
            return await asyncio.gather(*tasks)
        else:
            return [await self._generate_single(params) for _ in range(params.n)]

    async def _generate_single(self, params: ImageParams) -> bytes:
        """生成单张图片流程"""
        task_id = await self.submit_task(params)
        image_url = await self.poll_task(task_id)
        return await self.client.download_image(image_url)

    @abstractmethod
    async def submit_task(self, params: ImageParams) -> str:
        """提交任务，返回任务ID"""
        pass

    @abstractmethod
    async def poll_task(self, task_id: str) -> str:
        """轮询任务，返回图片URL"""
        pass

    async def _poll_with_timeout(self, task_id: str, check_status) -> str:
        """通用轮询逻辑"""
        start = asyncio.get_event_loop().time()

        while True:
            if asyncio.get_event_loop().time() - start > self.max_poll_time:
                raise TimeoutError(f"任务超时: {task_id}")

            status, url, error = await check_status(task_id)

            if status == "completed" and url:
                return url
            if status == "failed":
                raise ValueError(error or "任务失败")

            await asyncio.sleep(self.poll_interval)
