"""OpenAI格式的异步Provider - 支持返回task_id的模型"""

from typing import Optional, List
from loguru import logger

from ..models.image import ImageParams
from .async_relay_provider import AsyncRelayProvider
from .response_parser import ResponseParser


class OpenAIAsyncProvider(AsyncRelayProvider):
    """OpenAI格式的异步生图Provider"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "fal-ai/flux-1/schnell"
    ):
        super().__init__(base_url, api_key, poll_interval=2.0, max_poll_time=300.0)
        self.model_name = model_name
        self.parser = ResponseParser()

    async def submit_task(self, params: ImageParams) -> str:
        """提交任务到中转站"""
        payload = {
            "model": self.model_name,
            "prompt": params.prompt,
            "size": f"{params.width}x{params.height}",
            "n": 1
        }

        logger.info(f"[OpenAIAsync] 提交任务: {payload}")
        response = await self.client.post("/v1/images/generations", json=payload)
        logger.info(f"[OpenAIAsync] 响应: {response}")

        # 提取任务ID
        task_id = response.get("id") or response.get("task_id") or response.get("request_id")
        if not task_id:
            raise ValueError(f"未获取到任务ID: {response}")

        logger.info(f"[OpenAIAsync] 任务ID: {task_id}")
        return task_id

    async def poll_task_status(self, task_id: str) -> str:
        """轮询任务状态"""
        def status_checker(response: dict):
            status = response.get("status", "").lower()

            if status in ["completed", "succeeded"]:
                # 提取图片URL
                urls = self.parser.extract_urls(response)
                if urls:
                    return (True, urls[0], None, None)
                return (True, None, None, "任务完成但未获取到图片URL")

            elif status in ["failed", "error"]:
                error = response.get("error", "未知错误")
                return (False, None, None, f"任务失败: {error}")

            return (False, None, None, None)

        return await self._poll_until_complete(
            task_id,
            status_checker,
            f"/v1/tasks/{task_id}"
        )
