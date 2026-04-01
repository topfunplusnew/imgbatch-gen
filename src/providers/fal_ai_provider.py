"""Fal.ai Provider（通过中转站）"""

from typing import Optional, List
import httpx

from ..models.image import ImageParams
from .async_relay_provider import AsyncRelayProvider
from .response_parser import ResponseParser


class FalAIProvider(AsyncRelayProvider):
    """Fal.ai生图Provider（通过中转站）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model_name: str = "nano-banana"):
        """初始化Fal.ai Provider"""
        super().__init__(base_url, api_key, poll_interval=2.0, max_poll_time=300.0)
        self.model_name = model_name
        self.parser = ResponseParser()
    
    def supports_batch(self) -> bool:
        """Fal.ai支持批量生成"""
        return True
    
    async def _generate_batch(self, params: ImageParams) -> List[bytes]:
        """批量生成（Fal.ai支持一次生成多张）"""
        num_images = min(params.n, 4)  # Fal.ai最多支持4张
        
        # 1. 提交任务（使用临时参数）
        request_id = await self._submit_task_with_num(params, num_images)
        
        # 2. 轮询任务状态
        image_urls = await self.poll_task_status(request_id)
        
        # 3. 下载所有图片
        images = []
        for url in image_urls:
            image_data = await self.client.download_image(url)
            images.append(image_data)
        
        return images
    
    async def submit_task(self, params: ImageParams) -> str:
        """提交请求（默认单张）"""
        return await self._submit_task_with_num(params, 1)
    
    async def _submit_task_with_num(self, params: ImageParams, num_images: int) -> str:
        """提交请求（指定数量）"""
        import base64 as b64
        from loguru import logger
        extra = params.extra_params or {}

        # 注意：Fal AI的API不支持width、height、quality参数
        # 这些参数需要在prompt中体现，或者使用模型的其他特定参数

        # 有参考图片时走 edit 接口
        if "image" in extra:
            img = extra["image"]
            if isinstance(img, bytes):
                image_url = "data:image/jpeg;base64," + b64.b64encode(img).decode()
            else:
                image_url = str(img)

            payload = {
                "prompt": params.prompt,
                "image_urls": [image_url],
                "num_images": num_images,
            }
            logger.info(f"[FalAI] Edit接口提交任务，payload: {payload}")
            response = await self.client.post(
                f"/fal-ai/{self.model_name}/edit",
                json=payload
            )
        else:
            # 构建增强的prompt，包含质量和尺寸信息
            enhanced_prompt = params.prompt

            # 在prompt中添加尺寸建议
            if params.width and params.height:
                ratio = params.width / params.height
                if ratio > 1.5:
                    size_desc = "wide 16:9 aspect ratio"
                elif ratio > 1.2:
                    size_desc = "landscape 4:3 aspect ratio"
                elif ratio > 0.8:
                    size_desc = "square 1:1 aspect ratio"
                elif ratio > 0.7:
                    size_desc = "portrait 3:4 aspect ratio"
                else:
                    size_desc = "tall 9:16 aspect ratio"
                enhanced_prompt = f"{enhanced_prompt}, {size_desc}"
                logger.info(f"[FalAI] Generate接口添加尺寸描述: {size_desc}")

            # 在prompt中添加质量描述
            if params.quality:
                quality_desc = {
                    "720p": "standard quality",
                    "2k": "high quality, detailed",
                    "4k": "ultra high quality, highly detailed, sharp",
                    "hd": "high quality",
                    "high": "high quality",
                    "standard": "standard quality",
                    "low": "lower quality"
                }
                quality_text = quality_desc.get(params.quality.lower(), "high quality")
                enhanced_prompt = f"{enhanced_prompt}, {quality_text}"
                logger.info(f"[FalAI] Generate接口添加质量描述: {quality_text}")

            payload = {
                "prompt": enhanced_prompt,
                "num_images": num_images,
            }
            logger.info(f"[FalAI] Generate接口提交任务，payload: {payload}")
            response = await self.client.post(
                f"/fal-ai/{self.model_name}",
                json=payload
            )

        logger.info(f"[FalAI] 中转站响应: {response}")
        request_id = self.parser.extract_task_id(response, ["request_id"])
        if not request_id:
            raise ValueError("未获取到请求ID")

        logger.info(f"[FalAI] 获取请求ID: {request_id}")
        return request_id
    
    async def poll_task_status(self, request_id: str) -> List[str]:
        """轮询请求状态直到完成"""
        def status_checker(response: dict):
            status = response.get("status", "").upper()
            
            if status == "COMPLETED":
                # 先从响应中提取URL
                urls = self.parser.extract_urls(response)
                if urls:
                    return (True, None, urls, None)
                
                # 如果响应中没有，尝试从response_url获取
                response_url = response.get("response_url")
                if response_url:
                    return (True, None, None, None)  # 标记为完成，但需要额外处理
                
                return (True, None, None, "请求完成但未获取到图片URL")
            
            elif status in ("FAILED", "CANCELED"):
                error = response.get("error", "未知错误")
                return (False, None, None, f"请求失败: {error}")
            
            return (False, None, None, None)  # 继续轮询
        
        result = await self._poll_until_complete(
            request_id,
            status_checker,
            f"/fal-ai/{self.model_name}/requests/{request_id}"
        )
        
        # 如果result是None或空列表，说明需要从response_url获取
        if not result or (isinstance(result, list) and len(result) == 0):
            # 重新获取一次响应，尝试从response_url获取
            response = await self.client.get(f"/fal-ai/{self.model_name}/requests/{request_id}")
            response_url = response.get("response_url")
            if response_url:
                try:
                    if response_url.startswith("http"):
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            result_response = await client.get(response_url)
                            result_response.raise_for_status()
                            result_data = result_response.json()
                    else:
                        result_data = await self.client.get(response_url)
                    
                    urls = self.parser.extract_urls(result_data)
                    if urls:
                        return urls
                except Exception:
                    pass
            
            raise ValueError("请求完成但未获取到图片URL")
        
        return result if isinstance(result, list) else [result]
    
    async def edit_image(
        self,
        image_urls: list[str],
        prompt: str,
        num_images: Optional[int] = None
    ) -> str:
        """
        编辑图片（使用 Fal AI nano-banana/edit 接口）
        
        Args:
            image_urls: 需要编辑的图片URL列表
            prompt: 图像编辑的提示词
            num_images: 生成图片数量（1-4，默认1）
            
        Returns:
            请求ID（request_id），需要轮询获取结果
        """
        payload = {
            "prompt": prompt,
            "image_urls": image_urls,
        }
        
        if num_images:
            payload["num_images"] = min(num_images, 4)  # Fal AI最多支持4张
        
        response = await self.client.post(
            f"/fal-ai/{self.model_name}/edit",
            json=payload
        )
        
        request_id = self.parser.extract_task_id(response, ["request_id"])
        if not request_id:
            raise ValueError("未获取到请求ID")
        
        return request_id
    
    async def edit_image_and_wait(
        self,
        image_urls: list[str],
        prompt: str,
        num_images: Optional[int] = None
    ) -> list[str]:
        """
        编辑图片并等待完成（自动轮询）
        
        Args:
            image_urls: 需要编辑的图片URL列表
            prompt: 图像编辑的提示词
            num_images: 生成图片数量（1-4，默认1）
            
        Returns:
            编辑后的图片URL列表
        """
        request_id = await self.edit_image(image_urls, prompt, num_images)
        image_urls = await self.poll_task_status(request_id)
        return image_urls if isinstance(image_urls, list) else [image_urls]

