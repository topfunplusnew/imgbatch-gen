"""Tencent VOD Provider（通过中转站）"""

from typing import Optional
from ..models.image import ImageParams
from .async_relay_provider import AsyncRelayProvider
from .response_parser import ResponseParser


class TencentProvider(AsyncRelayProvider):
    """腾讯云VOD生图Provider（通过中转站）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化Tencent Provider"""
        super().__init__(base_url, api_key, poll_interval=3.0, max_poll_time=300.0)
        self.parser = ResponseParser()
    
    async def submit_task(self, params: ImageParams) -> str:
        """提交任务"""
        import base64 as b64
        extra = params.extra_params or {}

        payload = {
            "model_name": extra.get("model_name", "GEM"),
            "model_version": extra.get("model_version", "2.5"),
            "prompt": params.prompt,
        }

        # 参考图片：转base64后放入 file_infos
        if "image" in extra:
            img = extra["image"]
            if isinstance(img, bytes):
                img_b64 = b64.b64encode(img).decode()
                payload["file_infos"] = [{"file_type": "image", "file_base64": img_b64}]
            elif isinstance(img, str):
                payload["file_infos"] = [{"file_type": "image", "file_url": img}]
        elif "file_infos" in extra:
            payload["file_infos"] = extra["file_infos"]

        for key in ["negative_prompt", "enhance_prompt"]:
            if key in extra:
                payload[key] = extra[key]

        resolution = f"{params.width}x{params.height}"
        output_config = {"resolution": resolution, "storage_mode": "Temporary"}
        if "aspect_ratio" in extra:
            output_config["aspect_ratio"] = extra["aspect_ratio"]
        if "storage_mode" in extra:
            output_config["storage_mode"] = extra["storage_mode"]
        payload["output_config"] = output_config

        response = await self.client.post("/tencent-vod/v1/aigc-image", json=payload)

        task_id = self.parser.extract_task_id(response, ["TaskId"])
        if not task_id:
            raise ValueError("未获取到任务ID")

        return task_id
    
    async def poll_task_status(self, task_id: str) -> str:
        """轮询任务状态直到完成"""
        def status_checker(response: dict):
            status = response.get("Status", "").upper()
            
            if status == "SUCCESS":
                urls = self.parser.extract_urls(response)
                if urls:
                    return (True, urls[0], None, None)
                return (True, None, None, "任务完成但未获取到图片URL")
            
            elif status in ("FAILED", "ERROR"):
                error_msg = response.get("ErrorMsg", "未知错误")
                return (False, None, None, f"任务失败: {error_msg}")
            
            return (False, None, None, None)  # 继续轮询
        
        result = await self._poll_until_complete(
            task_id,
            status_checker,
            f"/tencent-vod/v1/query/{task_id}"
        )
        return result if isinstance(result, str) else result[0]

