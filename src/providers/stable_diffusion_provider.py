"""Stable Diffusion Provider"""

import httpx
from typing import Optional

from ..config.settings import settings
from ..config.providers import ProviderConfig
from ..models.image import ImageParams
from .base import BaseProvider


class StableDiffusionProvider(BaseProvider):
    """Stable Diffusion API Provider"""
    
    def __init__(self, config: dict = None):
        """初始化Stable Diffusion Provider"""
        if config is None:
            config = ProviderConfig.get_stable_diffusion_config()
        
        self.api_url = config.get("api_url") or settings.stable_diffusion_api_url
        self.api_key = config.get("api_key") or settings.stable_diffusion_api_key
        
        if not self.api_url:
            raise ValueError("Stable Diffusion API URL未配置")
    
    async def generate_image(self, params: ImageParams) -> bytes:
        """生成单张图片"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "prompt": params.prompt,
                    "width": params.width,
                    "height": params.height,
                    "steps": 20,
                    "cfg_scale": 7,
                }
                
                # 添加风格参数
                if params.style:
                    payload["prompt"] = f"{params.prompt}, {params.style} style"
                
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.post(
                    f"{self.api_url}/sdapi/v1/txt2img",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                # Stable Diffusion API返回base64编码的图片
                import base64
                image_data = result["images"][0]
                return base64.b64decode(image_data)
                
        except httpx.HTTPError as e:
            raise ValueError(f"Stable Diffusion请求失败: {str(e)}")
        except Exception as e:
            raise ValueError(f"Stable Diffusion生图失败: {str(e)}")
    
    async def generate_images(self, params: ImageParams) -> list[bytes]:
        """批量生成图片"""
        # Stable Diffusion API通常一次只能生成一张，需要多次调用
        import asyncio
        
        tasks = []
        for _ in range(params.n):
            tasks.append(self.generate_image(params))
        
        return await asyncio.gather(*tasks)


