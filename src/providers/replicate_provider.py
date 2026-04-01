"""Replicate Provider（通过中转站）"""

from typing import Optional
from ..models.image import ImageParams
from .async_relay_provider import AsyncRelayProvider
from .response_parser import ResponseParser


class ReplicateProvider(AsyncRelayProvider):
    """Replicate生图Provider（通过中转站）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化Replicate Provider"""
        super().__init__(base_url, api_key, poll_interval=2.0, max_poll_time=300.0)
        self.model_path = "black-forest-labs/flux-kontext-dev"
        self.parser = ResponseParser()

    def supports_parallel(self) -> bool:
        """Replicate不支持并行调用，需要串行处理"""
        return False
    
    async def submit_task(self, params: ImageParams) -> str:
        """创建预测任务"""
        import base64 as b64
        # 构建input参数
        input_data = {
            "prompt": params.prompt,
        }

        extra = params.extra_params or {}

        # 参考图片：支持bytes（转base64 data URI）或URL字符串
        if "image" in extra:
            img = extra["image"]
            if isinstance(img, bytes):
                input_data["input_image"] = "data:image/jpeg;base64," + b64.b64encode(img).decode()
            else:
                input_data["input_image"] = img
        elif "input_image" in extra:
            input_data["input_image"] = extra["input_image"]

        # aspect_ratio
        if "aspect_ratio" in extra:
            input_data["aspect_ratio"] = extra["aspect_ratio"]
        else:
            ratio = params.width / params.height
            if ratio > 1.5:
                input_data["aspect_ratio"] = "16:9"
            elif ratio > 1.2:
                input_data["aspect_ratio"] = "4:3"
            elif ratio > 0.8:
                input_data["aspect_ratio"] = "1:1"
            elif ratio > 0.7:
                input_data["aspect_ratio"] = "3:4"
            else:
                input_data["aspect_ratio"] = "9:16"

        # 质量映射到output_quality
        if params.quality:
            quality_mapping = {
                "720p": 60,      # 低质量
                "2k": 80,       # 中等质量
                "4k": 95,       # 高质量
                "hd": 95,       # 高质量
                "high": 95,     # 高质量
                "standard": 80,  # 标准质量
                "low": 60       # 低质量
            }
            output_quality = quality_mapping.get(params.quality.lower(), 80)
            input_data["output_quality"] = output_quality
            # 不要设置quality字段，因为Replicate不直接支持
            if "quality" in input_data:
                del input_data["quality"]

        for key in ["go_fast", "guidance", "output_format", "output_quality", "num_inference_steps"]:
            if key in extra:
                input_data[key] = extra[key]

        # 支持通过 extra_params 指定 model_path
        model_path = extra.get("model_path", self.model_path)

        payload = {"input": input_data}

        response = await self.client.post(
            f"/replicate/v1/models/{model_path}/predictions",
            json=payload
        )

        prediction_id = self.parser.extract_task_id(response, ["id"])
        if not prediction_id:
            raise ValueError("未获取到预测ID")

        return prediction_id
    
    async def poll_task_status(self, task_id: str) -> str:
        """轮询预测状态直到完成"""
        def status_checker(response: dict):
            status = response.get("status", "").upper()
            
            if status == "SUCCEEDED":
                urls = self.parser.extract_urls(response)
                if urls:
                    return (True, urls[0], None, None)
                return (True, None, None, "预测完成但未获取到输出URL")
            
            elif status in ("FAILED", "CANCELED"):
                error = response.get("error", "未知错误")
                return (False, None, None, f"预测失败: {error}")
            
            return (False, None, None, None)  # 继续轮询
        
        result = await self._poll_until_complete(
            task_id,
            status_checker,
            f"/replicate/v1/predictions/{task_id}"
        )
        return result if isinstance(result, str) else result[0]

