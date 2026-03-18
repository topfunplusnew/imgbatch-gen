"""Ideogram Provider（通过中转站）"""

from typing import Optional, Dict, Any, Union, List
import io
from ..models.image import ImageParams
from .sync_relay_provider import SyncRelayProvider
from .response_parser import ResponseParser


class IdeogramProvider(SyncRelayProvider):
    """Ideogram生图Provider（通过中转站）"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化Ideogram Provider"""
        super().__init__(base_url, api_key)
        self.parser = ResponseParser()

    async def generate_images(self, params: ImageParams) -> List[bytes]:
        """批量生成图片，有参考图片时走 remix 接口"""
        extra = params.extra_params or {}
        if "image" in extra:
            return await self._generate_with_remix(params)
        return await super().generate_images(params)

    async def _generate_with_remix(self, params: ImageParams) -> List[bytes]:
        """有参考图片时走 /ideogram/v1/ideogram-v3/remix"""
        from loguru import logger
        import io

        image_val = params.extra_params["image"]
        if isinstance(image_val, bytes):
            image_data = image_val
        else:
            image_data = await self.client.download_image(str(image_val))

        logger.info(f"✓ Ideogram 走 remix 接口，参考图片大小: {len(image_data)} bytes")

        files = {"image": ("reference.jpg", image_data, "image/jpeg")}
        data = {
            "prompt": params.prompt,
            "num_images": str(min(params.n, 8)),
        }
        extra = params.extra_params or {}
        if "rendering_speed" in extra:
            data["rendering_speed"] = extra["rendering_speed"]
        if "aspect_ratio" in extra:
            data["aspect_ratio"] = extra["aspect_ratio"]

        response = await self.client.post(
            "/ideogram/v1/ideogram-v3/remix",
            data=data,
            files=files,
            timeout=self.get_timeout()
        )
        self.check_error(response)
        image_urls = self.extract_image_urls(response)
        if not image_urls:
            raise ValueError("未获取到生成的图片URL")

        images = []
        for url in image_urls:
            images.append(await self.client.download_image(url))
        return images


    
    def get_endpoint(self) -> str:
        return "/ideogram/v1/ideogram-v3/generate"
    
    def get_timeout(self) -> float:
        return 180.0  # Ideogram可能需要更长时间
    
    def build_payload(self, params: ImageParams) -> dict:
        extra = params.extra_params or {}
        aspect_ratio = extra.get("aspect_ratio")
        resolution_override = extra.get("resolution")

        payload = {
            "prompt": params.prompt,
            "num_images": min(params.n, 8),
        }

        # gemini 模型需要传 model 字段
        model = params.model or self.model
        if model:
            payload["model"] = model

        # OpenAPI 约束：resolution 与 aspect_ratio 不能同时使用
        # - 若提供 aspect_ratio，则不发送 resolution（忽略 width/height 与 resolution 覆盖）
        # - 否则发送 resolution（可被 extra_params.resolution 覆盖）
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        else:
            payload["resolution"] = resolution_override or f"{params.width}x{params.height}"
        
        # 风格映射
        if params.style:
            style_mapping = {
                "realistic": "REALISTIC",
                "cartoon": "GENERAL",
                "abstract": "GENERAL",
                "design": "DESIGN",
            }
            payload["style_type"] = style_mapping.get(params.style.lower(), "AUTO")
        
        # 质量映射
        if params.quality:
            quality_mapping = {
                "hd": "QUALITY",
                "high": "QUALITY",
                "standard": "DEFAULT",
                "low": "TURBO",
            }
            payload["rendering_speed"] = quality_mapping.get(params.quality.lower(), "DEFAULT")
        
        # 额外参数（允许覆盖部分字段）
        for key in [
            "seed",
            "negative_prompt",
            "magic_prompt",
            "color_palette",
            "style_codes",
            "style_type",
            "rendering_speed",
        ]:
            if key in extra and extra[key] is not None:
                payload[key] = extra[key]
        
        return payload
    
    async def edit_image(
        self,
        image: Union[bytes, io.BytesIO],
        prompt: Optional[str] = None,
        mask: Optional[Union[bytes, io.BytesIO]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        编辑图片（使用 Ideogram v3 edit 接口）
        
        Args:
            image: 要编辑的图片（bytes 或 BytesIO）
            prompt: 提示词
            mask: 可选的蒙版图片
            seed: 随机种子
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        data = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image"] = ("image.png", image, "image/png")
        
        # 处理蒙版
        if mask:
            if isinstance(mask, bytes):
                files["mask"] = ("mask.png", io.BytesIO(mask), "image/png")
            else:
                files["mask"] = ("mask.png", mask, "image/png")
        
        # 处理其他参数
        if prompt:
            data["prompt"] = prompt
        if seed is not None:
            data["seed"] = str(seed)
        
        response = await self.client.post(
            "/ideogram/v1/ideogram-v3/edit",
            data=data,
            files=files,
            timeout=180.0
        )
        return response
    
    async def remix_image(
        self,
        image: Union[bytes, io.BytesIO],
        prompt: Optional[str] = None,
        num_images: Optional[int] = None,
        rendering_speed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        重制图片（使用 Ideogram v3 remix 接口）
        
        Args:
            image: 要重制的图片
            prompt: 提示词
            num_images: 生成图片数量
            rendering_speed: 渲染速度（DEFAULT, QUALITY, TURBO）
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        data = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image"] = ("image.png", image, "image/png")
        
        if prompt:
            data["prompt"] = prompt
        if num_images:
            data["num_images"] = str(num_images)
        if rendering_speed:
            data["rendering_speed"] = rendering_speed
        
        response = await self.client.post(
            "/ideogram/v1/ideogram-v3/remix",
            data=data,
            files=files,
            timeout=180.0
        )
        return response
    
    async def reframe_image(
        self,
        image: Union[bytes, io.BytesIO],
        resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        重构图片（使用 Ideogram v3 reframe 接口）
        
        Args:
            image: 要重构的图片
            resolution: 目标分辨率，例如 "512x1536"
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        data = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image"] = ("image.png", image, "image/png")
        
        if resolution:
            data["resolution"] = resolution
        
        response = await self.client.post(
            "/ideogram/v1/ideogram-v3/reframe",
            data=data,
            files=files,
            timeout=180.0
        )
        return response
    
    async def replace_background(
        self,
        image: Union[bytes, io.BytesIO],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        替换背景（使用 Ideogram v3 replace-background 接口）
        
        Args:
            image: 要处理的图片
            prompt: 背景描述提示词
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        data = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image"] = ("image.png", image, "image/png")
        
        if prompt:
            data["prompt"] = prompt
        
        response = await self.client.post(
            "/ideogram/v1/ideogram-v3/replace-background",
            data=data,
            files=files,
            timeout=180.0
        )
        return response
    
    async def upscale_image(
        self,
        image: Union[bytes, io.BytesIO],
        prompt: Optional[str] = None,
        resemblance: Optional[int] = None,
        detail: Optional[int] = None,
        magic_prompt_option: Optional[str] = None,
        num_images: Optional[int] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        放大图片（使用 Ideogram upscale 接口）
        
        Args:
            image: 要放大的图片
            prompt: 提示词（用于指导放大）
            resemblance: 相似度（1-100，默认50）
            detail: 细节程度（1-100，默认50）
            magic_prompt_option: MagicPrompt选项（AUTO/ON/OFF）
            num_images: 生成图片数量（1-8，默认1）
            seed: 随机种子
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        data = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image_file"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image_file"] = ("image.png", image, "image/png")
        
        # 构建 image_request JSON 字符串
        image_request = {}
        if prompt:
            image_request["prompt"] = prompt
        if resemblance is not None:
            image_request["resemblance"] = resemblance
        if detail is not None:
            image_request["detail"] = detail
        if magic_prompt_option:
            image_request["magic_prompt_option"] = magic_prompt_option
        if num_images:
            image_request["num_images"] = num_images
        if seed is not None:
            image_request["seed"] = seed
        
        if image_request:
            import json
            data["image_request"] = json.dumps(image_request)
        
        response = await self.client.post(
            "/ideogram/upscale",
            data=data,
            files=files,
            timeout=180.0
        )
        return response
    
    async def describe_image(self, image: Union[bytes, io.BytesIO]) -> Dict[str, Any]:
        """
        描述图片（使用 Ideogram describe 接口）
        
        Args:
            image: 要描述的图片
            
        Returns:
            包含 task_id 的响应
        """
        files = {}
        
        # 处理图片
        if isinstance(image, bytes):
            files["image_file"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            files["image_file"] = ("image.png", image, "image/png")
        
        response = await self.client.post(
            "/ideogram/describe",
            files=files,
            timeout=180.0
        )
        return response
