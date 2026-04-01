"""Midjourney Provider（通过中转站）"""

from typing import Optional, List, Dict, Any
from ..models.image import ImageParams
from .async_relay_provider import AsyncRelayProvider
from .response_parser import ResponseParser


class MidjourneyProvider(AsyncRelayProvider):
    """Midjourney生图Provider（通过中转站）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化Midjourney Provider"""
        super().__init__(base_url, api_key, poll_interval=2.0, max_poll_time=300.0)
        self.parser = ResponseParser()

    def supports_parallel(self) -> bool:
        """Midjourney不支持并行调用，需要串行处理"""
        return False
    
    async def submit_task(self, params: ImageParams) -> str:
        """提交Imagine任务"""
        from loguru import logger

        # 构建完整的prompt，包含比例和质量参数
        enhanced_prompt = params.prompt

        # 根据宽高比添加--ar参数
        if params.width and params.height:
            ratio = params.width / params.height
            if abs(ratio - 1.78) < 0.1:  # 16:9 ≈ 1.78
                enhanced_prompt += " --ar 16:9"
            elif abs(ratio - 1.33) < 0.1:  # 4:3 ≈ 1.33
                enhanced_prompt += " --ar 4:3"
            elif abs(ratio - 0.67) < 0.1:  # 9:16 ≈ 0.67
                enhanced_prompt += " --ar 9:16"
            elif abs(ratio - 0.75) < 0.1:  # 3:4 ≈ 0.75
                enhanced_prompt += " --ar 3:4"
            elif abs(ratio - 1.0) < 0.1:  # 1:1
                enhanced_prompt += " --ar 1:1"
            elif abs(ratio - 1.5) < 0.1:  # 3:2 ≈ 1.5
                enhanced_prompt += " --ar 3:2"
            elif abs(ratio - 0.8) < 0.1:  # 4:5 ≈ 0.8
                enhanced_prompt += " --ar 4:5"
            elif abs(ratio - 1.25) < 0.1:  # 5:4 ≈ 1.25
                enhanced_prompt += " --ar 5:4"
            elif abs(ratio - 2.33) < 0.1:  # 21:9 ≈ 2.33
                enhanced_prompt += " --ar 21:9"
            else:
                # 计算最接近的标准比例
                if ratio > 1.5:
                    enhanced_prompt += " --ar 16:9"
                elif ratio > 1.2:
                    enhanced_prompt += " --ar 4:3"
                elif ratio > 0.8:
                    enhanced_prompt += " --ar 1:1"
                elif ratio > 0.7:
                    enhanced_prompt += " --ar 3:4"
                else:
                    enhanced_prompt += " --ar 9:16"

            logger.info(f"[Midjourney] 根据{params.width}x{params.height}添加--ar参数，ratio={ratio:.2f}")

        # 根据质量添加--quality参数
        if params.quality:
            quality_mapping = {
                "720p": "1",   # 低质量
                "2k": "2",     # 中等质量
                "4k": "2",     # 高质量（Midjourney只有1和2两个等级）
                "hd": "2",     # 高质量
                "high": "2",   # 高质量
                "standard": "1",  # 标准质量
                "low": "1"     # 低质量
            }
            quality_value = quality_mapping.get(params.quality.lower(), "2")
            enhanced_prompt += f" --quality {quality_value}"
            logger.info(f"[Midjourney] 添加--quality参数: {params.quality} -> {quality_value}")

        payload = {
            "botType": "MID_JOURNEY",
            "prompt": enhanced_prompt,
        }

        # 添加可选参数
        if params.extra_params:
            for key in ["base64Array", "notifyHook", "state"]:
                if key in params.extra_params:
                    payload[key] = params.extra_params[key]
                    logger.info(f"[Midjourney] 添加extra参数 {key}")

        logger.info(f"[Midjourney] 原始prompt: {params.prompt[:50]}...")
        logger.info(f"[Midjourney] 增强prompt: {enhanced_prompt[:50]}...")
        logger.info(f"[Midjourney] 提交任务，完整payload: {payload}")
        response = await self.client.post("/mj/submit/imagine", json=payload)
        logger.info(f"[Midjourney] 中转站响应: {response}")

        if response.get("code") != 1:
            raise ValueError(f"提交任务失败: {response.get('description', '未知错误')}")

        task_id = self.parser.extract_task_id(response, ["result"])
        if not task_id:
            raise ValueError("未获取到任务ID")

        logger.info(f"[Midjourney] 获取任务ID: {task_id}")
        return task_id
    
    async def poll_task_status(self, task_id: str) -> str:
        """轮询任务状态直到完成"""
        def status_checker(response: dict):
            status = response.get("status", "").upper()
            
            if status == "SUCCESS":
                urls = self.parser.extract_urls(response)
                if urls:
                    return (True, urls[0], None, None)
                return (True, None, None, "任务完成但未获取到图片URL")
            
            elif status == "FAILURE":
                error_msg = response.get("failReason", "未知错误")
                return (False, None, None, f"任务失败: {error_msg}")
            
            return (False, None, None, None)  # 继续轮询
        
        result = await self._poll_until_complete(
            task_id,
            status_checker,
            f"/mj/task/{task_id}/fetch"
        )
        return result if isinstance(result, str) else result[0]
    
    async def upload_discord_images(self, base64_array: List[str]) -> Dict[str, Any]:
        """
        上传图片到 Discord
        
        Args:
            base64_array: base64 编码的图片数组
            
        Returns:
            上传结果
        """
        payload = {
            "base64Array": base64_array
        }
        response = await self.client.post("/mj/submit/upload-discord-images", json=payload)
        return response
    
    async def list_tasks_by_condition(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据ID列表查询任务
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            任务列表
        """
        payload = {
            "ids": task_ids
        }
        response = await self.client.post("/mj/task/list-by-condition", json=payload)
        # 根据 OpenAPI 文档，返回可能是数组或对象
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and "data" in response:
            return response["data"]
        return response
    
    async def get_image_seed(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务图片的seed
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含 seed 信息的响应
        """
        response = await self.client.get(f"/mj/task/{task_id}/image-seed")
        return response
    
    async def submit_action(
        self,
        custom_id: str,
        task_id: str,
        choose_same_channel: bool = True,
        notify_hook: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行Action动作（如放大、变换等）
        
        Args:
            custom_id: 动作标识，例如 "MJ::JOB::upsample::2::3dbbd469-36af-4a0f-8f02-df6c579e7011"
            task_id: 任务ID
            choose_same_channel: 是否选择同一频道下的账号
            notify_hook: 回调地址
            state: 自定义参数
            
        Returns:
            提交结果
        """
        payload = {
            "chooseSameChannel": choose_same_channel,
            "customId": custom_id,
            "taskId": task_id,
        }
        if notify_hook:
            payload["notifyHook"] = notify_hook
        if state:
            payload["state"] = state
        
        response = await self.client.post("/mj/submit/action", json=payload)
        return response
    
    async def submit_blend(
        self,
        base64_array: List[str],
        bot_type: str = "MID_JOURNEY",
        dimensions: Optional[str] = None,
        quality: Optional[str] = None,
        notify_hook: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """
        提交Blend任务（混合图片）
        
        Args:
            base64_array: 图片base64数组
            bot_type: bot类型，MID_JOURNEY 或 NIJI_JOURNEY
            dimensions: 比例，PORTRAIT(2:3)、SQUARE(1:1)、LANDSCAPE(3:2)
            quality: 质量参数
            notify_hook: 回调地址
            state: 自定义参数
            
        Returns:
            任务ID
        """
        payload = {
            "botType": bot_type,
            "base64Array": base64_array,
        }
        if dimensions:
            payload["dimensions"] = dimensions
        if quality:
            payload["quality"] = quality
        if notify_hook:
            payload["notifyHook"] = notify_hook
        if state:
            payload["state"] = state
        
        response = await self.client.post("/mj/submit/blend", json=payload)
        
        if response.get("code") != 1:
            raise ValueError(f"提交Blend任务失败: {response.get('description', '未知错误')}")
        
        task_id = self.parser.extract_task_id(response, ["result"])
        if not task_id:
            raise ValueError("未获取到任务ID")
        
        return task_id
    
    async def submit_describe(
        self,
        base64: Optional[str] = None,
        base64_array: Optional[List[str]] = None,
        bot_type: str = "MID_JOURNEY",
        notify_hook: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """
        提交Describe任务（图片描述）
        
        Args:
            base64: 图片base64（单张）
            base64_array: 图片base64数组
            bot_type: bot类型，MID_JOURNEY 或 NIJI_JOURNEY
            notify_hook: 回调地址
            state: 自定义参数
            
        Returns:
            任务ID
        """
        payload = {
            "botType": bot_type,
        }
        if base64:
            payload["base64"] = base64
        if base64_array:
            payload["base64Array"] = base64_array
        
        if not base64 and not base64_array:
            raise ValueError("必须提供 base64 或 base64Array")
        
        if notify_hook:
            payload["notifyHook"] = notify_hook
        if state:
            payload["state"] = state
        
        response = await self.client.post("/mj/submit/describe", json=payload)
        
        if response.get("code") != 1:
            raise ValueError(f"提交Describe任务失败: {response.get('description', '未知错误')}")
        
        task_id = self.parser.extract_task_id(response, ["result"])
        if not task_id:
            raise ValueError("未获取到任务ID")
        
        return task_id
    
    async def submit_modal(
        self,
        mask_base64: str,
        task_id: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交Modal任务（局部重绘）
        
        Args:
            mask_base64: 局部重绘的蒙版base64
            task_id: 任务ID
            prompt: 提示词
            
        Returns:
            提交结果
        """
        payload = {
            "maskBase64": mask_base64,
            "taskId": task_id,
        }
        if prompt:
            payload["prompt"] = prompt
        
        response = await self.client.post("/mj/submit/modal", json=payload)
        return response

