"""BFL异步Provider"""

from typing import Dict, Any
from loguru import logger

from .async_base_provider import AsyncBaseProvider
from ..models.image import ImageParams


class BFLProvider(AsyncBaseProvider):
    """BFL异步生图Provider"""

    def __init__(self, api_key: str, model: str = "flux-pro-1.1"):
        super().__init__(
            base_url="https://api.bfl.ai/v1",
            api_key=api_key,
            poll_interval=2.0,
            max_poll_time=300.0
        )
        self.model = model

    def build_request_params(self, params: ImageParams) -> Dict[str, Any]:
        """构建BFL请求参数"""
        request_params = {
            "prompt": params.prompt,
            "width": params.width,
            "height": params.height,
        }

        if params.seed:
            request_params["seed"] = params.seed

        return request_params

    async def submit_task(self, params: ImageParams) -> str:
        """提交任务到BFL"""
        # 使用OpenAI兼容格式
        endpoint = "/v1/images/generations"
        request_params = {
            "model": self.model,
            "prompt": params.prompt,
            "size": f"{params.width}x{params.height}",
            "n": 1
        }

        logger.info(f"提交到: {endpoint}, 参数: {request_params}")
        response = await self.client.post(endpoint, json=request_params)

        # 检查是否是异步任务
        task_id = response.get("id") or response.get("task_id")
        if task_id:
            logger.info(f"BFL任务已提交: {task_id}")
            return task_id

        # 如果是同步返回，直接返回URL
        if "data" in response and len(response["data"]) > 0:
            url = response["data"][0].get("url")
            if url:
                logger.info(f"同步返回图片URL")
                return url

        raise ValueError(f"未获取到任务ID或图片URL: {response}")

    async def poll_task(self, task_id: str) -> str:
        """轮询BFL任务状态"""
        # 如果task_id是URL，直接返回
        if task_id.startswith("http"):
            return task_id

        async def check_status(tid):
            response = await self.client.get(f"/v1/tasks/{tid}")
            status = response.get("status")

            if status == "succeeded" or status == "completed":
                url = response.get("output", {}).get("url") or response.get("result", {}).get("sample")
                return "completed", url, None
            elif status == "failed":
                return "failed", None, response.get("error", "任务失败")
            else:
                return "processing", None, None

        return await self._poll_with_timeout(task_id, check_status)
