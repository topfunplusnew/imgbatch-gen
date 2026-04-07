"""OpenAI DALL-E Provider（通过中转站）"""

from typing import Optional, Dict, Any, Union, List
import io
import base64
from ..models.image import ImageParams
from .sync_relay_provider import SyncRelayProvider
from ..config.settings import settings
from ..config.model_registry import get_model_registry
from ..config.aspect_ratios import get_size_for_aspect_ratio


class OpenAIRelayProvider(SyncRelayProvider):
    """OpenAI DALL-E生图Provider（通过中转站）"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化OpenAI Provider"""
        super().__init__(base_url, api_key)
        self.model = settings.openai_image_model

    async def generate_images(self, params: ImageParams) -> List[bytes]:
        """批量生成图片（重写以支持base64数据和参考图片）"""
        model = (params.model or self.model or "").lower()

        # 豆包/Seedream 模型走增强处理
        if "doubao" in model or "seedream" in model:
            return await self._generate_doubao(params)

        # qwen 模型走 /v1/images/generations（传图片URL）
        if "qwen" in model:
            return await self._generate_qwen(params)

        # 如果有参考图片，使用 /v1/images/edits 接口
        if params.extra_params and "image" in params.extra_params:
            return await self._generate_with_reference(params)

        # 根据模型类型选择端点（优先查 registry 的 model_type）
        is_image_endpoint = await self._is_image_generation_model(params.model or self.model or "")
        endpoint = "/v1/images/generations" if is_image_endpoint else self.get_endpoint()

        # 构建请求参数
        payload = self.build_payload(params, is_image_endpoint=is_image_endpoint)

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

        # 下载所有图片
        images = []
        for url in image_urls:
            if url.startswith("data:image/"):
                image_data = self._decode_base64_image(url)
            else:
                image_data = await self.client.download_image(url)
            images.append(image_data)

        return images

    async def _generate_doubao(self, params: ImageParams) -> List[bytes]:
        """豆包/Seedream 系列走 /v1/images/generations，增强尺寸和比例支持"""
        from loguru import logger
        import base64 as b64

        model = params.model or self.model

        # 构建增强的prompt，包含尺寸和质量信息
        enhanced_prompt = params.prompt

        # 获取宽高比和标准化尺寸
        if params.width and params.height:
            aspect_ratio = get_aspect_ratio_for_dimensions(params.width, params.height)
            quality = params.quality or "2k"

            # 使用配置函数获取标准化尺寸
            standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)

            # 根据aspect_ratio精确添加尺寸描述到prompt
            # 豆包API可能对某些比例有特殊处理，使用更明确的描述
            ratio_descriptions = {
                "1:1": "perfectly square 1:1 aspect ratio",
                "4:3": "horizontal 4:3 landscape aspect ratio",
                "3:4": "vertical 3:4 portrait aspect ratio",
                "16:9": "widescreen 16:9 horizontal aspect ratio",
                "9:16": "vertical 9:16 portrait aspect ratio",
                "2:3": "vertical 2:3 portrait aspect ratio",
                "3:2": "horizontal 3:2 landscape aspect ratio",
                "4:5": "vertical 4:5 portrait aspect ratio",
                "5:4": "horizontal 5:4 landscape aspect ratio",
            }

            # 强调具体像素尺寸和比例，避免豆包自动调整
            size_desc = ratio_descriptions.get(aspect_ratio, "standard aspect ratio")
            resolution_desc = f"{params.width}x{params.height} pixels resolution"
            aspect_description = f"exact dimensions {params.width} width x {params.height} height, {size_desc}"

            enhanced_prompt = f"{enhanced_prompt}, {aspect_description}, maintain exact aspect ratio, do not auto-adjust dimensions"
            logger.info(f"[Doubao] 添加尺寸参数: {params.width}x{params.height} -> {size_desc} (标准: {standard_width}x{standard_height})")
        else:
            # 如果没有指定尺寸，使用1:1 2k质量作为默认
            aspect_ratio = "1:1"
            quality = params.quality or "2k"
            standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)

        # 添加质量描述到prompt
        if params.quality:
            quality_desc = {
                "720p": "standard quality",
                "2k": "high quality, detailed",
                "4k": "ultra high quality, highly detailed, sharp, professional",
                "hd": "high quality",
                "high": "high quality",
                "standard": "standard quality",
                "low": "lower quality"
            }
            quality_text = quality_desc.get(params.quality.lower(), "high quality")
            enhanced_prompt = f"{enhanced_prompt}, {quality_text}"
            logger.info(f"[Doubao] 添加质量参数: {params.quality} -> {quality_text}")

        # 添加数量描述到prompt
        if params.n and params.n > 1:
            enhanced_prompt = f"{enhanced_prompt}, generate {params.n} images"
            logger.info(f"[Doubao] 添加数量参数: {params.n}")

        # 构建豆包API参数
        payload = {
            "model": model,
            "prompt": enhanced_prompt,
            "n": min(params.n, 10),
        }

        # 豆包/Seedream模型使用方式2：传递具体的宽高像素值
        if params.width and params.height:
            # 验证像素尺寸符合豆包要求
            total_pixels = params.width * params.height
            ratio = params.width / params.height

            # 豆包要求：总像素范围 [921600, 16777216]，宽高比范围 [1/16, 16]
            if not (921600 <= total_pixels <= 16777216):
                logger.warning(f"[Doubao] 像素总数 {total_pixels} 超出豆包范围 [921600, 16777216]，使用标准化尺寸")
                # 使用标准化尺寸
                if max(standard_width, standard_height) >= 2048:
                    payload["size"] = f"{standard_width}x{standard_height}"
                else:
                    payload["size"] = f"{standard_width}x{standard_height}"
            elif not (1/16 <= ratio <= 16):
                logger.warning(f"[Doubao] 宽高比 {ratio:.3f} 超出豆包范围 [1/16, 16]，使用标准化尺寸")
                # 使用标准化尺寸
                if max(standard_width, standard_height) >= 2048:
                    payload["size"] = f"{standard_width}x{standard_height}"
                else:
                    payload["size"] = f"{standard_width}x{standard_height}"
            else:
                # 使用用户请求的尺寸
                payload["size"] = f"{params.width}x{params.height}"
                logger.info(f"[Doubao] 使用精确像素尺寸: {payload['size']}, 总像素: {total_pixels}, 宽高比: {ratio:.3f}, 标准比例: {aspect_ratio}")
        else:
            # auto模式：使用默认 1:1 2k 尺寸
            default_w, default_h = get_size_for_aspect_ratio("1:1", params.quality or "2k")
            payload["size"] = f"{default_w}x{default_h}"
            logger.info(f"[Doubao] 使用auto默认尺寸: {payload['size']}")

        logger.info(f"[Doubao] 原始prompt: {params.prompt[:50]}...")
        logger.info(f"[Doubao] 增强prompt: {enhanced_prompt[:50]}...")

        response = await self.client.post(
            "/v1/images/generations",
            json=payload,
            timeout=self.get_timeout()
        )
        self.check_error(response)
        image_urls = self.extract_image_urls(response)
        if not image_urls:
            raise ValueError("未获取到生成的图片URL")

        images = []
        for url in image_urls:
            if url.startswith("data:image/"):
                images.append(self._decode_base64_image(url))
            else:
                images.append(await self.client.download_image(url))
        return images

    async def _generate_qwen(self, params: ImageParams) -> List[bytes]:
        """qwen 系列走 /v1/images/generations"""
        from loguru import logger
        import base64 as b64

        extra = params.extra_params or {}
        image_val = extra.get("image")

        if isinstance(image_val, bytes):
            image_url = "data:image/jpeg;base64," + b64.b64encode(image_val).decode()
        else:
            image_url = image_val

        payload = {
            "model": params.model or self.model,
            "prompt": params.prompt,
            "n": min(params.n, 4),
        }
        if params.width and params.height:
            payload["size"] = f"{params.width}x{params.height}"
        if image_url:
            payload["image"] = image_url
        # qwen 支持的额外参数
        for key in ("watermark", "prompt_extend", "negative_prompt", "seed"):
            if key in extra and extra[key] is not None:
                payload[key] = extra[key]

        logger.info(f"✓ qwen 走 /v1/images/generations, image={'有' if image_url else '无'}")

        response = await self.client.post(
            "/v1/images/generations",
            json=payload,
            timeout=self.get_timeout()
        )
        self.check_error(response)
        image_urls = self.extract_image_urls(response)
        if not image_urls:
            raise ValueError("未获取到生成的图片URL")

        images = []
        for url in image_urls:
            if url.startswith("data:image/"):
                images.append(self._decode_base64_image(url))
            else:
                images.append(await self.client.download_image(url))
        return images

    async def _generate_with_reference(self, params: ImageParams) -> List[bytes]:
        """使用参考图片调用 /v1/images/edits 接口"""
        from loguru import logger

        image_bytes = params.extra_params["image"]
        logger.info(f"✓ 使用 /v1/images/edits 接口，参考图片大小: {len(image_bytes)} bytes")

        files = {"image": ("reference.jpg", image_bytes, "image/jpeg")}
        data = {
            "prompt": params.prompt,
            "model": params.model or self.model,
            "n": str(min(params.n, 10)),
        }
        if params.quality:
            data["quality"] = params.quality

        response = await self.client.post(
            "/v1/images/edits",
            files=files,
            data=data,
            timeout=self.get_timeout()
        )

        self.check_error(response)
        image_urls = self.extract_image_urls(response)

        if not image_urls:
            raise ValueError("未获取到生成的图片URL")

        images = []
        for url in image_urls:
            if url.startswith("data:image/"):
                image_data = self._decode_base64_image(url)
            else:
                image_data = await self.client.download_image(url)
            images.append(image_data)

        return images

    def _decode_base64_image(self, data_uri: str) -> bytes:
        """解码base64编码的图片数据"""
        # 从data:image/png;base64,xxx中提取base64数据
        try:
            # 查找逗号分隔符
            comma_index = data_uri.find(',')
            if comma_index >= 0:
                base64_data = data_uri[comma_index + 1:]
                return base64.b64decode(base64_data)
            else:
                # 如果没有逗号，直接解码
                return base64.b64decode(data_uri)
        except Exception as e:
            raise ValueError(f"解码base64图片失败: {str(e)}")
    
    def get_endpoint(self) -> str:
        return "/v1/chat/completions"

    async def _is_image_generation_model(self, model: str) -> bool:
        """判断是否应该走 /v1/images/generations 接口，优先查 supported_endpoint_types"""
        try:
            registry = await get_model_registry()
            model_info = registry.get_model_info(model)
            if model_info is not None:
                types = model_info.supported_endpoint_types
                # 图像模型始终走 /v1/images/generations
                if model_info.model_type == "图像":
                    return True
                # 有 image-generation 或 dall-e-3 端点类型，走 /v1/images/generations
                if "image-generation" in types or "dall-e-3" in types:
                    return True
                # 有 openai 或 openai-response 端点类型，走 chat completions
                if "openai" in types or "openai-response" in types:
                    return False
        except Exception:
            pass
        # fallback: 关键词匹配
        m = (model or "").lower()
        return any(k in m for k in ("dall-e", "dall_e", "gpt-image", "imagen", "flux", "seedream", "seedance"))

    def _is_doubao_model(self, model: str) -> bool:
        """判断是否是豆包/Seedream模型"""
        return "doubao" in model.lower() or "seedream" in model.lower()

    def build_payload(self, params: ImageParams, is_image_endpoint: bool = True) -> dict:
        from loguru import logger
        model = params.model or self.model

        if is_image_endpoint:
            # /v1/images/generations 格式
            payload = {
                "model": model,
                "prompt": params.prompt,
                "n": min(params.n, 10),
            }

            # 豆包/Seedream模型使用方式2：传递具体的宽高像素值
            if self._is_doubao_model(model):
                if params.width and params.height:
                    # 验证像素尺寸符合豆包要求
                    total_pixels = params.width * params.height
                    ratio = params.width / params.height

                    # 豆包要求：总像素范围 [921600, 16777216]，宽高比范围 [1/16, 16]
                    if not (921600 <= total_pixels <= 16777216):
                        logger.warning(f"[Doubao] 像素总数 {total_pixels} 超出豆包范围 [921600, 16777216]，使用标准化尺寸")
                        # 使用标准化尺寸
                        aspect_ratio = get_aspect_ratio_for_dimensions(params.width, params.height)
                        quality = params.quality or "2k"
                        standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)
                        payload["size"] = f"{standard_width}x{standard_height}"
                    elif not (1/16 <= ratio <= 16):
                        logger.warning(f"[Doubao] 宽高比 {ratio:.3f} 超出豆包范围 [1/16, 16]，使用标准化尺寸")
                        # 使用标准化尺寸
                        aspect_ratio = get_aspect_ratio_for_dimensions(params.width, params.height)
                        quality = params.quality or "2k"
                        standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)
                        payload["size"] = f"{standard_width}x{standard_height}"
                    else:
                        # 使用用户请求的尺寸
                        payload["size"] = f"{params.width}x{params.height}"
                        logger.info(f"[Doubao] 使用精确像素尺寸: {payload['size']}, 总像素: {total_pixels}, 宽高比: {ratio:.3f}")
                else:
                    # 使用标准化默认尺寸
                    aspect_ratio = "1:1"
                    quality = params.quality or "2k"
                    standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)
                    payload["size"] = f"{standard_width}x{standard_height}"
                    logger.info(f"[Doubao] 使用默认像素尺寸: {payload['size']} (标准化尺寸: {standard_width}x{standard_height})")
            else:
                # 其他模型使用标准尺寸格式
                if params.width and params.height:
                    payload["size"] = f"{params.width}x{params.height}"

            if params.quality:
                # gpt-image-1.x 系列只支持 low/medium/high/auto，不支持 standard/hd
                quality = params.quality
                if quality == "standard":
                    quality = "medium"
                elif quality == "hd":
                    quality = "high"
                payload["quality"] = quality
            return payload

        # chat completions 格式
        message_content = f"生成一张{params.width}x{params.height}的图片：{params.prompt}"
        if params.quality:
            message_content = f"生成一张高质量{params.width}x{params.height}的图片：{params.prompt}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "n": min(params.n, 10)
        }

        # 如果extra_params中有image，添加图片到消息中
        if params.extra_params and "image" in params.extra_params:
            import base64
            from loguru import logger
            image_data = params.extra_params["image"]
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"✓ 将参考图片编码为base64 (大小: {len(image_base64)} 字符)")
            else:
                image_base64 = str(image_data)

            payload["messages"][0]["content"] = [
                {
                    "type": "text",
                    "text": params.prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
            logger.info(f"✓ 已将参考图片添加到请求payload中")

        return payload
    
    async def edit_image(
        self,
        image: Union[bytes, io.BytesIO],
        prompt: str,
        mask: Optional[Union[bytes, io.BytesIO]] = None,
        model: Optional[str] = None,
        n: Optional[int] = None,
        quality: Optional[str] = None,
        response_format: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        background: Optional[str] = None,
        moderation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        编辑图片（使用 OpenAI images/edits 接口）
        
        Args:
            image: 要编辑的图片（bytes 或 BytesIO）
            prompt: 提示词（必填）
            mask: 可选的蒙版图片（PNG格式，透明区域表示要编辑的部分）
            model: 模型名称（默认使用配置的模型）
            n: 生成图片数量（1-10）
            quality: 图片质量（high/medium/low/standard/auto）
            response_format: 响应格式（url/b64_json）
            aspect_ratio: 宽高比（21:9, 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16, 9:21）
            background: 背景设置（transparent/opaque/auto，仅 gpt-image-1 支持）
            moderation: 内容审核级别（low/auto，仅 gpt-image-1 支持）
            
        Returns:
            编辑结果
        """
        files = {}
        data = {
            "prompt": prompt,
        }
        
        # 处理图片
        if isinstance(image, bytes):
            # 尝试检测图片格式
            if image.startswith(b'\x89PNG'):
                files["image"] = ("image.png", io.BytesIO(image), "image/png")
            elif image.startswith(b'\xff\xd8'):
                files["image"] = ("image.jpg", io.BytesIO(image), "image/jpeg")
            elif image.startswith(b'RIFF') and b'WEBP' in image[:12]:
                files["image"] = ("image.webp", io.BytesIO(image), "image/webp")
            else:
                files["image"] = ("image.png", io.BytesIO(image), "image/png")
        else:
            # BytesIO 对象，确保位置在开头
            if hasattr(image, 'seek'):
                image.seek(0)
            files["image"] = ("image.png", image, "image/png")
        
        # 处理蒙版
        if mask:
            if isinstance(mask, bytes):
                files["mask"] = ("mask.png", io.BytesIO(mask), "image/png")
            else:
                files["mask"] = ("mask.png", mask, "image/png")
        
        # 处理其他参数
        if model:
            data["model"] = model
        elif self.model:
            data["model"] = self.model
        
        if n is not None:
            data["n"] = str(n)
        if quality:
            data["quality"] = quality
        if response_format:
            data["response_format"] = response_format
        if aspect_ratio:
            data["aspect_ratio"] = aspect_ratio
        if background:
            data["background"] = background
        if moderation:
            data["moderation"] = moderation
        
        response = await self.client.post(
            "/v1/images/edits",
            data=data,
            files=files,
            timeout=180.0
        )
        return response

