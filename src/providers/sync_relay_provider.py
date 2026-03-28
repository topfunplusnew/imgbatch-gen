"""同步中转站Provider基类（直接返回结果的Provider继承此类）"""

from typing import Optional, List
from abc import abstractmethod

from ..config.settings import settings
from ..models.image import ImageParams
from .base import BaseProvider
from .relay_client import RelayClient
from .response_parser import ResponseParser


class SyncRelayProvider(BaseProvider):
    """同步中转站Provider基类（直接返回结果的Provider继承此类）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化同步Provider"""
        self.client = RelayClient(
            base_url,
            api_key,
            retry_base_delay=settings.generation_retry_base_delay,
            retry_max_delay=settings.generation_retry_max_delay,
        )
        self.parser = ResponseParser()
    
    async def generate_image(self, params: ImageParams) -> bytes:
        """生成单张图片（同步）"""
        # 强制 n=1 避免循环调用时重复生成
        single_params = params.model_copy(update={"n": 1})
        # 构建请求参数
        payload = self.build_payload(single_params)

        # 根据模型类型选择端点（子类可通过重写 _is_image_generation_model 控制）
        endpoint = self.get_endpoint()
        if hasattr(self, '_is_image_generation_model'):
            model = (params.model or getattr(self, 'model', '') or '')
            if self._is_image_generation_model(model):
                endpoint = "/v1/images/generations"

        # 调用API
        response = await self.client.post(
            endpoint,
            json=payload,
            timeout=self.get_timeout()
        )

        # 检查错误
        self.check_error(response)

        # 提取图片URL
        image_urls = self.extract_image_urls(response)

        if not image_urls:
            raise ValueError("未获取到生成的图片URL")

        # 下载第一张图片
        return await self.client.download_image(image_urls[0])
    
    async def generate_images(self, params: ImageParams) -> List[bytes]:
        """批量生成图片"""
        # 构建请求参数
        payload = self.build_payload(params)
        
        # 调用API
        response = await self.client.post(
            self.get_endpoint(),
            json=payload,
            timeout=self.get_timeout()
        )
        
        # 检查错误
        self.check_error(response)
        
        # 提取图片URL
        image_urls = self.extract_image_urls(response)
        
        if not image_urls:
            raise ValueError("未获取到生成的图片URL")
        
        # 下载所有图片
        images = []
        for url in image_urls:
            image_data = await self.client.download_image(url)
            images.append(image_data)
        
        return images
    
    @abstractmethod
    def get_endpoint(self) -> str:
        """获取API端点（子类必须实现）"""
        pass
    
    @abstractmethod
    def build_payload(self, params: ImageParams) -> dict:
        """构建请求参数（子类必须实现）"""
        pass
    
    def get_timeout(self) -> float:
        """获取请求超时时间（秒）"""
        return 300.0
    
    def check_error(self, response: dict):
        """检查响应错误（子类可以重写）"""
        if "error" in response:
            error_msg = response.get("error", {}).get("message", "未知错误")
            raise ValueError(f"生图失败: {error_msg}")
        
        if response.get("code") not in (0, None, 1):
            error_msg = response.get("message", "未知错误")
            raise ValueError(f"生图失败: {error_msg}")
    
    def extract_image_urls(self, response: dict) -> List[str]:
        """提取图片URL（使用ResponseParser）"""
        from loguru import logger
        logger.info(f"API响应内容: {str(response)[:500]}")
        return self.parser.extract_urls(response)

