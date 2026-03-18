"""异步中转站Provider基类（封装轮询逻辑）"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, List, Callable, Dict, Any

from ..models.image import ImageParams
from .base import BaseProvider
from .relay_client import RelayClient


class AsyncRelayProvider(BaseProvider):
    """异步中转站Provider基类（需要轮询的Provider继承此类）"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        poll_interval: float = 2.0,
        max_poll_time: float = 300.0
    ):
        """初始化异步Provider"""
        self.client = RelayClient(base_url, api_key)
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time
    
    async def generate_image(self, params: ImageParams) -> bytes:
        """生成单张图片（异步任务，需要轮询）"""
        # 强制 n=1 避免循环调用时重复生成
        single_params = params.model_copy(update={"n": 1})
        return await self._generate_single(single_params)
    
    async def generate_images(self, params: ImageParams) -> List[bytes]:
        """批量生成图片"""
        # 子类可以重写此方法以实现批量生成优化
        if self.supports_batch():
            return await self._generate_batch(params)
        else:
            # 不支持批量，根据是否支持并行调用决定处理方式
            if self.supports_parallel():
                # 支持并行，使用asyncio.gather并行调用
                tasks = []
                for _ in range(params.n):
                    tasks.append(self._generate_single(params))
                return await asyncio.gather(*tasks)
            else:
                # 不支持并行，串行调用等待所有结果
                images = []
                for _ in range(params.n):
                    image = await self._generate_single(params)
                    images.append(image)
                return images
    
    async def _generate_single(self, params: ImageParams) -> bytes:
        """生成单张图片的通用流程"""
        # 1. 提交任务
        task_id = await self.submit_task(params)
        
        # 2. 轮询任务状态
        image_urls = await self.poll_task_status(task_id)
        
        # 3. 下载图片（如果返回多个URL，取第一个）
        if isinstance(image_urls, list):
            image_url = image_urls[0]
        else:
            image_url = image_urls
        return await self.client.download_image(image_url)
    
    async def _generate_batch(self, params: ImageParams) -> List[bytes]:
        """批量生成（如果Provider支持）"""
        # 默认实现：多次调用单次生成
        return await self.generate_images(params)
    
    def supports_batch(self) -> bool:
        """是否支持批量生成（一次请求生成多张）"""
        return False

    def supports_parallel(self) -> bool:
        """是否支持并行调用（同时发起多个请求）

        默认为True（支持并行）。
        对于某些API（如Midjourney、Replicate），可能需要限制为False（串行调用）。
        """
        return True
    
    @abstractmethod
    async def submit_task(self, params: ImageParams) -> str:
        """提交任务，返回任务ID（子类必须实现）"""
        pass
    
    @abstractmethod
    async def poll_task_status(self, task_id: str) -> str | List[str]:
        """轮询任务状态，返回图片URL或URL列表（子类必须实现）"""
        pass
    
    async def _poll_until_complete(
        self,
        task_id: str,
        status_checker: Callable[[Dict[str, Any]], tuple[bool, Optional[str], Optional[List[str]], Optional[str]]],
        status_endpoint: str
    ) -> str | List[str]:
        """
        通用轮询方法
        
        Args:
            task_id: 任务ID
            status_checker: 状态检查函数，返回 (is_complete, image_urls, error_msg)
            status_endpoint: 状态查询端点（可以使用 {task_id} 占位符）
        
        Returns:
            图片URL或URL列表
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > self.max_poll_time:
                raise ValueError(f"任务轮询超时: {task_id}")
            
            # 查询任务状态
            endpoint = status_endpoint.format(task_id=task_id)
            response = await self.client.get(endpoint)
            
            # 检查状态
            is_complete, image_url, image_urls, error_msg = status_checker(response)
            
            if is_complete:
                if image_url:
                    return image_url
                elif image_urls:
                    return image_urls
                else:
                    raise ValueError(error_msg or "任务完成但未获取到图片URL")
            
            if error_msg:
                raise ValueError(error_msg)
            
            # 等待后继续轮询
            await asyncio.sleep(self.poll_interval)

