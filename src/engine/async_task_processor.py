"""Async task background processor."""

import asyncio

from loguru import logger

from ..config.settings import settings
from ..database import get_db_manager
from ..database.async_task_manager import get_async_task_manager
from ..providers.relay_client import RelayClient
from ..utils.config_helper import require_relay_api_key, resolve_relay_config


class AsyncTaskProcessor:
    """Poll and complete provider-side async image tasks."""

    def __init__(self):
        self.manager = get_async_task_manager()
        self.running = False
        self.default_base_url = settings.relay_base_url

        if not self.default_base_url:
            logger.warning("Async task processor has no default relay base URL configured.")

    async def start(self):
        self.running = True
        logger.info("异步任务处理器已启动")
        asyncio.create_task(self._process_loop())

    async def stop(self):
        self.running = False
        logger.info("异步任务处理器已停止")

    async def _process_loop(self):
        while self.running:
            try:
                await self._process_pending_tasks()
                await asyncio.sleep(3)
            except Exception as exc:
                logger.error(f"处理任务出错: {exc}")
                await asyncio.sleep(5)

    async def _process_pending_tasks(self):
        tasks = await self.manager.list_tasks(status="pending", limit=10)

        for task in tasks:
            try:
                await self._process_task(task.id)
            except Exception as exc:
                logger.error(f"处理任务 {task.id} 失败: {exc}")
                await self.manager.update_task(
                    task.id,
                    status="failed",
                    error=str(exc),
                )

    async def _process_task(self, task_id: str):
        task = await self.manager.get_task(task_id)
        if not task or task.status != "pending":
            return

        await self.manager.update_task(task_id, status="processing", progress=10)

        model_path = task.model.replace("fal-ai/", "")
        num_images = task.params.get("n", 1) if task.params else 1
        client = await self._build_client_for_task(task)

        response = await client.post(
            f"/fal-ai/{model_path}",
            json={
                "prompt": task.prompt,
                "num_images": num_images,
            },
        )

        platform_task_id = response.get("request_id")
        if not platform_task_id:
            raise ValueError("未获取到 request_id")

        logger.info(f"任务 {task_id} 已提交: {platform_task_id}")
        task.platform_task_id = platform_task_id
        await self.manager.update_task(task_id, progress=30)

        asyncio.create_task(self._poll_task(task_id, platform_task_id, model_path, client))

    async def _poll_task(self, task_id: str, platform_task_id: str, model_path: str, client: RelayClient):
        max_attempts = 100
        for i in range(max_attempts):
            try:
                response = await client.get(f"/fal-ai/{model_path}/requests/{platform_task_id}")
                status = response.get("status", "").upper()

                logger.info(f"轮询任务 {task_id}: status={status}, response={response}")

                if status == "COMPLETED" or "images" in response:
                    urls = []
                    if "images" in response:
                        urls = [img.get("url") for img in response["images"] if img.get("url")]
                    elif "output" in response and "images" in response["output"]:
                        urls = [img.get("url") for img in response["output"]["images"] if img.get("url")]

                    logger.info(f"提取到的URLs: {urls}")

                    await self.manager.update_task(
                        task_id,
                        status="completed",
                        progress=100,
                        result_urls=urls,
                    )
                    logger.success(f"任务 {task_id} 完成, URLs: {urls}")
                    return

                if status in ["FAILED", "CANCELED"]:
                    error = response.get("error", "未知错误")
                    await self.manager.update_task(task_id, status="failed", error=error)
                    logger.error(f"任务 {task_id} 失败: {error}")
                    return

                progress = 30 + (i / max_attempts) * 60
                await self.manager.update_task(task_id, progress=progress)

            except Exception as exc:
                logger.error(f"轮询任务 {task_id} 出错: {exc}")

            await asyncio.sleep(3)

        await self.manager.update_task(task_id, status="failed", error="轮询超时")

    async def _build_client_for_task(self, task) -> RelayClient:
        params = task.params or {}
        credential_id = params.get("credential_id")
        base_url = self.default_base_url
        api_key = None

        if credential_id:
            db_manager = get_db_manager()
            credential = await db_manager.resolve_api_credential(credential_id)
            if not credential:
                raise ValueError("Async task is missing a usable API credential.")
            api_key = credential["api_key"]

        if not credential_id:
            base_url, _ = await resolve_relay_config()
            api_key = await require_relay_api_key()

        if not base_url:
            raise ValueError("Relay base URL is not configured for the async task.")
        if not api_key:
            raise ValueError("Async task is missing an API key.")

        return RelayClient(
            base_url,
            api_key,
            retry_base_delay=settings.generation_retry_base_delay,
            retry_max_delay=settings.generation_retry_max_delay,
        )
