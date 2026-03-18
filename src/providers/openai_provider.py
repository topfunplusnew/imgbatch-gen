"""OpenAI DALL-E Provider"""

import base64
from typing import Optional
from openai import AsyncOpenAI

from ..config.settings import settings
from ..config.providers import ProviderConfig
from ..models.image import ImageParams
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI DALL-E生图Provider"""
    
    def __init__(self, config: dict = None):
        """初始化OpenAI Provider"""
        if config is None:
            config = ProviderConfig.get_openai_config()
        
        self.api_key = config.get("api_key") or settings.openai_api_key
        self.base_url = config.get("base_url") or settings.openai_base_url
        self.image_model = config.get("image_model") or settings.openai_image_model
        
        if not self.api_key:
            raise ValueError("OpenAI API Key未配置")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def generate_image(self, params: ImageParams) -> bytes:
        """生成单张图片"""
        try:
            # DALL-E参数映射
            size = f"{params.width}x{params.height}"
            quality = params.quality if params.quality in ["standard", "hd"] else "standard"
            
            response = await self.client.images.generate(
                model=self.image_model,
                prompt=params.prompt,
                size=size,
                quality=quality,
                n=1,
                response_format="b64_json"
            )
            
            # 提取base64图片数据
            image_data = response.data[0].b64_json
            return base64.b64decode(image_data)
            
        except Exception as e:
            raise ValueError(f"OpenAI生图失败: {str(e)}")
    
    async def generate_images(self, params: ImageParams) -> list[bytes]:
        """批量生成图片"""
        try:
            size = f"{params.width}x{params.height}"
            quality = params.quality if params.quality in ["standard", "hd"] else "standard"
            
            response = await self.client.images.generate(
                model=self.image_model,
                prompt=params.prompt,
                size=size,
                quality=quality,
                n=min(params.n, 10),  # DALL-E最多支持10张
                response_format="b64_json"
            )
            
            images = []
            for item in response.data:
                image_data = item.b64_json
                images.append(base64.b64decode(image_data))
            
            return images
            
        except Exception as e:
            raise ValueError(f"OpenAI批量生图失败: {str(e)}")


