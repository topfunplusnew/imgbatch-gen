"""生图Provider基础接口"""

from abc import ABC, abstractmethod
from typing import Optional
import asyncio

from ..models.image import ImageParams


class BaseProvider(ABC):
    """基础Provider接口"""
    
    @abstractmethod
    async def generate_image(self, params: ImageParams) -> bytes:
        """
        生成图片
        
        Args:
            params: 生图参数
            
        Returns:
            图片字节数据
        """
        pass
    
    @abstractmethod
    async def generate_images(self, params: ImageParams) -> list[bytes]:
        """
        批量生成图片（n > 1时）
        
        Args:
            params: 生图参数
            
        Returns:
            图片字节数据列表
        """
        pass
    
    def validate_params(self, params: ImageParams) -> bool:
        """
        验证参数是否有效

        Args:
            params: 生图参数

        Returns:
            是否有效
        """
        if not params.prompt:
            return False
        # width/height 为 0 表示 auto（让模型自动决定），跳过尺寸验证
        if params.width and (params.width < 256 or params.width > 8192):
            return False
        if params.height and (params.height < 256 or params.height > 8192):
            return False
        if params.n < 1 or params.n > 10:
            return False
        return True

    def supports_batch(self) -> bool:
        """
        是否支持批量生成（一次请求生成多张）

        Returns:
            是否支持批量生成
        """
        return False

    def supports_parallel(self) -> bool:
        """
        是否支持并行调用（同时发起多个请求）

        Returns:
            是否支持并行调用（默认True）
        """
        return True
    
    async def generate(self, params: ImageParams) -> list[bytes]:
        """
        统一的生成接口（根据n参数决定生成数量）

        Args:
            params: 生图参数

        Returns:
            图片字节数据列表
        """
        if not self.validate_params(params):
            raise ValueError("参数验证失败")

        if params.n == 1:
            image = await self.generate_image(params)
            return [image]
        elif self.supports_batch():
            return await self.generate_images(params)
        else:
            # 不支持原生批量的 provider，循环调用 n 次
            if self.supports_parallel():
                tasks = [self.generate_image(params) for _ in range(params.n)]
                return list(await asyncio.gather(*tasks))
            else:
                results = []
                for _ in range(params.n):
                    image = await self.generate_image(params)
                    results.append(image)
                return results


