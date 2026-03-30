"""Gemini 图像生成 Provider（通过中转站）"""

import base64
from typing import Optional, List
from loguru import logger

from ..models.image import ImageParams
from .sync_relay_provider import SyncRelayProvider
from ..config.aspect_ratios import get_aspect_ratio_for_dimensions, get_size_for_aspect_ratio


class GeminiProvider(SyncRelayProvider):
    """Gemini 图像生成 Provider

    支持两种模型：
    1. gemini-*-image-* 系列 → /v1beta/models/{model}:generateContent
    2. imagen-* 系列 → /v1beta/models/{model}:predict
    """

    def get_endpoint(self) -> str:
        return "/v1beta/models/gemini-2.5-flash-image-preview:generateContent"

    def get_timeout(self) -> float:
        return 300.0

    def _is_imagen_model(self, model: str) -> bool:
        return "imagen" in model.lower()

    async def generate_image(self, params: ImageParams) -> bytes:
        images = await self.generate_images(params)
        return images[0]

    async def generate_images(self, params: ImageParams) -> List[bytes]:
        model = params.model or ""
        if self._is_imagen_model(model):
            return await self._generate_imagen(params)
        return await self._generate_gemini(params)

    async def _generate_gemini(self, params: ImageParams) -> List[bytes]:
        """gemini-*-image-* 系列走 /v1beta/models/{model}:generateContent"""
        model = params.model or ""
        endpoint = f"/v1beta/models/{model}:generateContent"
        extra = params.extra_params or {}

        # 构建增强的prompt，包含尺寸和质量信息
        enhanced_prompt = params.prompt

        # 获取宽高比和标准化尺寸
        if params.width and params.height:
            aspect_ratio = get_aspect_ratio_for_dimensions(params.width, params.height)
            quality = params.quality or "2k"

            # 使用配置函数获取标准化尺寸
            standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)

            # 添加尺寸描述到prompt
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

            resolution_desc = f"{params.width}x{params.height} resolution"
            enhanced_prompt = f"{enhanced_prompt}, {size_desc}, {resolution_desc}"
            logger.info(f"[Gemini] 添加尺寸参数: {params.width}x{params.height} -> {size_desc} (标准: {standard_width}x{standard_height})")
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
            logger.info(f"[Gemini] 添加质量参数: {params.quality} -> {quality_text}")

        # 添加数量描述到prompt
        if params.n and params.n > 1:
            enhanced_prompt = f"{enhanced_prompt}, generate {params.n} images"
            logger.info(f"[Gemini] 添加数量参数: {params.n}")

        # 构建generationConfig — Gemini API 文档统一使用 TEXT+IMAGE
        generation_config = {
            "responseModalities": ["TEXT", "IMAGE"]
        }

        # 添加实际图片尺寸参数 - 按照Gemini API文档设置
        if params.width and params.height:
            # 添加详细调试日志
            actual_ratio = params.width / params.height
            logger.info(f"[Gemini] 接收到的尺寸: {params.width}x{params.height}, 计算比例: {actual_ratio:.3f}")

            # 使用配置函数获取标准宽高比
            aspect_ratio = get_aspect_ratio_for_dimensions(params.width, params.height)
            quality = params.quality or "2k"

            logger.info(f"[Gemini] 匹配到的宽高比: {aspect_ratio}")

            # 使用标准化尺寸
            standard_width, standard_height = get_size_for_aspect_ratio(aspect_ratio, quality)

            # 根据标准化尺寸选择最佳的imageSize
            max_dimension = max(standard_width, standard_height)
            if max_dimension >= 2048:
                image_size = "2K"
            else:
                image_size = "1K"

            # 按照 Gemini API 文档，参数应该包装在 imageConfig 对象中
            image_config = {"imageSize": image_size}

            # 只有当比例匹配到标准比例且不是默认1:1时才传递 aspectRatio
            if aspect_ratio in ["3:2", "4:3", "5:4", "16:9", "16:10", "21:9"]:
                image_config["aspectRatio"] = aspect_ratio
                logger.info(f"[Gemini] 使用标准比例: {aspect_ratio}")
            elif aspect_ratio in ["2:3", "3:4", "4:5", "9:16"]:
                image_config["aspectRatio"] = aspect_ratio
                logger.info(f"[Gemini] 使用标准比例: {aspect_ratio}")
            else:
                logger.info(f"[Gemini] 使用默认比例 1:1，不传递 aspectRatio 参数")

            generation_config["imageConfig"] = image_config

            logger.info(f"[Gemini] 设置API参数: imageConfig={image_config}, 请求尺寸={params.width}x{params.height}, 标准化尺寸={standard_width}x{standard_height}")

        parts = [{"text": enhanced_prompt}]

        image_val = extra.get("image")
        if image_val is not None:
            mime_type = extra.get("reference_image_mime_type") or "image/png"
            try:
                if isinstance(image_val, (bytes, bytearray)):
                    inline_part = {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(bytes(image_val)).decode("ascii"),
                        }
                    }
                    # 参照图生图：text 在前，inline_data 在后（与 Gemini API 文档示例一致）
                    parts.append(inline_part)
                    logger.info("[Gemini] 参照图生图模式，已添加参考图片 mimeType={}", mime_type)
                else:
                    logger.warning("[Gemini] 参考图片不是 bytes，已跳过多模态图片输入")
            except Exception as exc:
                logger.warning("[Gemini] 添加参考图片失败: {}", exc)

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts
                }
            ],
            "generationConfig": generation_config
        }

        # 打印完整的payload用于调试
        logger.info(f"[Gemini] 完整generationConfig: {generation_config}")
        logger.info(f"[Gemini] 完整payload keys: {list(payload.keys())}")

        logger.info(f"[Gemini] 原始prompt: {params.prompt[:50]}...")
        logger.info(f"[Gemini] 增强prompt: {enhanced_prompt[:50]}...")
        logger.info(f"[Gemini] 调用 {endpoint}, 完整payload={str(payload)[:200]}")
        response = await self.client.post(endpoint, json=payload, timeout=self.get_timeout())
        logger.info(f"[Gemini] 响应类型: {type(response)}, keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")

        # 打印响应的详细信息，特别是candidates部分
        if isinstance(response, dict) and "candidates" in response:
            candidates = response["candidates"]
            logger.info(f"[Gemini] candidates数量: {len(candidates)}")
            if candidates:
                candidate = candidates[0]
                logger.info(f"[Gemini] candidate keys: {list(candidate.keys()) if isinstance(candidate, dict) else 'N/A'}")
                if "content" in candidate:
                    content = candidate["content"]
                    logger.info(f"[Gemini] content keys: {list(content.keys()) if isinstance(content, dict) else 'N/A'}")
                    if "parts" in content:
                        parts = content["parts"]
                        for i, part in enumerate(parts):
                            logger.info(f"[Gemini] part {i} keys: {list(part.keys()) if isinstance(part, dict) else 'N/A'}")

        self.check_error(response)

        # 检查响应中是否包含图片尺寸信息
        if isinstance(response, dict) and "candidates" in response:
            candidates = response["candidates"]
            if candidates and "content" in candidates[0]:
                content = candidates[0]["content"]
                if "parts" in content:
                    parts = content["parts"]
                    for part in parts:
                        if "inlineData" in part:
                            inline_data = part["inlineData"]
                            if "mimeType" in inline_data:
                                logger.info(f"[Gemini] 返回图片类型: {inline_data['mimeType']}")
                                # 尝试解析可能的尺寸信息
                                if "data" in inline_data:
                                    base64_data = inline_data["data"]
                                    # 计算base64数据的大致尺寸（不精确）
                                    import base64
                                    try:
                                        decoded = base64.b64decode(base64_data)
                                        # 这里只是估算，实际尺寸需要图片库解析
                                        logger.info(f"[Gemini] 图片数据大小: {len(decoded)} bytes")
                                    except Exception as e:
                                        logger.warning(f"[Gemini] 无法解码图片数据: {e}")

        image_urls = self._extract_gemini_images(response)
        if not image_urls:
            raise ValueError("未获取到生成的图片")
        images = []
        for url in image_urls:
            images.append(await self.client.download_image(url))
        return images

    async def _generate_imagen(self, params: ImageParams) -> List[bytes]:
        """imagen-* 系列走 /v1beta/models/{model}:predict"""
        from loguru import logger
        model = params.model or ""
        endpoint = f"/v1beta/models/{model}:predict"

        # 构建增强的prompt，包含尺寸和质量信息
        enhanced_prompt = params.prompt

        # 添加尺寸描述到prompt
        if params.width and params.height:
            ratio = params.width / params.height
            if ratio > 1.5:
                size_desc = "wide 16:9 aspect ratio"
                resolution_desc = f"{params.width}x{params.height} resolution"
            elif ratio > 1.2:
                size_desc = "landscape 4:3 aspect ratio"
                resolution_desc = f"{params.width}x{params.height} resolution"
            elif ratio > 0.8:
                size_desc = "square 1:1 aspect ratio"
                resolution_desc = f"{params.width}x{params.height} resolution"
            elif ratio > 0.7:
                size_desc = "portrait 3:4 aspect ratio"
                resolution_desc = f"{params.width}x{params.height} resolution"
            else:
                size_desc = "tall 9:16 aspect ratio"
                resolution_desc = f"{params.width}x{params.height} resolution"

            enhanced_prompt = f"{enhanced_prompt}, {size_desc}, {resolution_desc}"
            logger.info(f"[Imagen] 添加尺寸参数: {params.width}x{params.height} -> {size_desc}")

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
            logger.info(f"[Imagen] 添加质量参数: {params.quality} -> {quality_text}")

        # 添加数量描述到prompt
        if params.n and params.n > 1:
            enhanced_prompt = f"{enhanced_prompt}, generate {params.n} images"
            logger.info(f"[Imagen] 添加数量参数: {params.n}")

        # 构建parameters
        parameters = {
            "sampleCount": min(params.n, 4)
        }

        # 添加实际图片尺寸参数 - 按照Imagen API文档设置
        if params.width and params.height:
            # 计算长宽比
            ratio = params.width / params.height

            # 定义支持的标准比例及其对应的数值和容差范围
            aspect_ratios = [
                ("1:1", 1.0, 0.05),      # 正方形，容差±5%
                ("4:5", 0.8, 0.05),      # 肖像，容差±5%
                ("2:3", 0.667, 0.05),    # 肖像，容差±5%
                ("3:4", 0.75, 0.05),     # 肖像，容差±5%
                ("9:16", 0.5625, 0.05),  # 竖屏/手机，容差±5%
                ("3:2", 1.5, 0.05),      # 横屏/相机，容差±5%
                ("4:3", 1.333, 0.05),    # 横屏，容差±5%
                ("5:4", 1.25, 0.05),     # 横屏，容差±5%
                ("16:9", 1.778, 0.05),   # 宽屏/视频，容差±5%
                ("16:10", 1.6, 0.05),    # 宽屏显示器，容差±5%
                ("21:9", 2.333, 0.05)    # 超宽屏，容差±5%
            ]

            # 检查比例是否在标准比例的容差范围内
            matched_aspect_ratio = None
            for ar_name, ar_value, tolerance in aspect_ratios:
                if abs(ratio - ar_value) <= tolerance:
                    matched_aspect_ratio = ar_name
                    break

            # 根据请求的分辨率选择最佳的imageSize
            max_dimension = max(params.width, params.height)
            if max_dimension >= 2048:
                image_size = "2K"
            else:
                image_size = "1K"

            # 设置 imageSize 参数
            parameters["imageSize"] = image_size

            # 只有当比例匹配标准比例时才传递 aspectRatio
            if matched_aspect_ratio:
                parameters["aspectRatio"] = matched_aspect_ratio
                logger.info(f"[Imagen] 匹配到标准比例: {matched_aspect_ratio}")
            else:
                logger.info(f"[Imagen] 比例 {ratio:.3f} 不在标准比例范围内，不传递 aspectRatio 参数")

            logger.info(f"[Imagen] 设置API参数: imageSize={image_size}, 请求尺寸={params.width}x{params.height}, 计算比例={ratio:.3f}")

        payload = {
            "instances": [{"prompt": enhanced_prompt}],
            "parameters": parameters
        }

        logger.info(f"[Imagen] 原始prompt: {params.prompt[:50]}...")
        logger.info(f"[Imagen] 增强prompt: {enhanced_prompt[:50]}...")
        logger.info(f"[Imagen] 调用 {endpoint}, 完整payload={str(payload)[:200]}")
        response = await self.client.post(endpoint, json=payload, timeout=self.get_timeout())
        logger.info(f"[Imagen] 响应类型: {type(response)}, keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
        self.check_error(response)
        image_urls = self._extract_imagen_images(response)
        if not image_urls:
            raise ValueError("未获取到生成的图片")
        images = []
        for url in image_urls:
            images.append(await self.client.download_image(url))
        return images

    def _extract_gemini_images(self, response: dict) -> List[str]:
        """从 generateContent 响应中提取图片（data URI 或 URL）"""
        import re
        urls = []
        candidates = response.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                # inline_data: base64 图片
                inline = part.get("inlineData") or part.get("inline_data")
                if inline:
                    mime = inline.get("mimeType", "image/png")
                    b64 = inline.get("data", "")
                    if b64:
                        urls.append(f"data:{mime};base64,{b64}")
                # text 中可能有 markdown 图片
                text = part.get("text", "")
                if text:
                    matches = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
                    urls.extend(matches)
        return urls

    def _extract_imagen_images(self, response: dict) -> List[str]:
        """从 predict 响应中提取图片"""
        urls = []
        predictions = response.get("predictions", [])
        for pred in predictions:
            if isinstance(pred, dict):
                # base64 图片
                b64 = pred.get("bytesBase64Encoded") or pred.get("b64_json")
                if b64:
                    mime = pred.get("mimeType", "image/png")
                    urls.append(f"data:{mime};base64,{b64}")
                # URL
                url = pred.get("url") or pred.get("imageUrl")
                if url:
                    urls.append(url)
        return urls

    def build_payload(self, params: ImageParams) -> dict:
        # generate_images 已完全重写，此方法不会被调用
        return {}
