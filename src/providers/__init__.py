"""生图接口适配器模块"""

from .base import BaseProvider
from .relay_client import RelayClient
from .response_parser import ResponseParser
from .async_relay_provider import AsyncRelayProvider
from .sync_relay_provider import SyncRelayProvider
from .midjourney_provider import MidjourneyProvider
from .ideogram_provider import IdeogramProvider
from .openai_relay_provider import OpenAIRelayProvider
from .gemini_provider import GeminiProvider
from .replicate_provider import ReplicateProvider
from .fal_ai_provider import FalAIProvider
from .tencent_provider import TencentProvider

from .baidu_provider import BaiduProvider
from .aliyun_provider import AliyunProvider

from ..config.settings import settings
from ..config.model_registry import get_model_registry


async def get_provider(provider: str = None, model_name: str = None, api_key: str = None) -> BaseProvider:
    """
    根据Provider名称或模型名称获取对应的Provider实例（使用中转站）

    Args:
        provider: Provider名称（如 midjourney, ideogram等）
        model_name: 模型名称（如 gemini-3.1-flash-image-preview），如果提供，会自动查找对应的Provider
        api_key: API Key（可选），如果未提供则使用管理员统一配置

    Returns:
        Provider实例
    """
    # 如果未提供 api_key，使用管理员统一配置
    key = (api_key or "").strip()
    if not key:
        from ..utils.config_helper import get_relay_config
        base_url, key = await get_relay_config()
        if not key:
            raise ValueError("系统未配置 API Key，请联系管理员")
    else:
        base_url = settings.relay_base_url

    # 如果提供了模型名称，尝试从模型注册表查找
    if model_name:
        try:
            # 尝试从全局变量获取已初始化的注册表
            from ..config.model_registry import _model_registry
            if _model_registry:
                mapping = _model_registry.get_provider_mapping(model_name)
                if mapping:
                    provider = mapping.provider_type
                    from loguru import logger
                    logger.info(f"模型 {model_name} 自动映射到 Provider: {provider}")
        except Exception as e:
            # 如果模型注册表未初始化或查找失败，继续使用provider参数
            from loguru import logger
            logger.warning(f"无法从模型注册表查找模型 {model_name}: {str(e)}")

    # 如果provider仍为None，使用默认值
    if provider is None:
        provider = settings.default_image_provider

    provider = provider.lower()
    # 清理 provider 名称：去掉括号及其内容，去掉多余空格
    import re
    provider = re.sub(r'\s*\([^)]*\)', '', provider).strip()

    # Provider映射
    if provider == "midjourney" or provider == "mj":
        return MidjourneyProvider(base_url, key)
    elif provider == "ideogram":
        return IdeogramProvider(base_url, key)
    elif provider == "openai" or provider == "dall-e":
        return OpenAIRelayProvider(base_url, key)
    elif provider == "replicate":
        return ReplicateProvider(base_url, key)
    elif provider == "fal-ai" or provider == "fal_ai":
        return FalAIProvider(base_url, key)
    elif provider == "tencent" or provider == "tencent-vod":
        return TencentProvider(base_url, key)
    elif provider == "baidu" or provider == "文心" or provider == "ernie":
        return BaiduProvider(base_url, key)
    elif provider == "aliyun" or provider == "阿里云" or provider == "wanx" or provider == "通义" or provider == "alibaba" or provider == "bailian":
        return AliyunProvider(base_url, key)
    elif provider == "doubao" or provider == "豆包":
        return OpenAIRelayProvider(base_url, key)
    elif provider == "kling" or provider == "可灵":
        return OpenAIRelayProvider(base_url, key)
    elif "gemini" in provider.lower() or "imagen" in provider.lower() or provider == "google":
        return GeminiProvider(base_url, key)
    else:
        raise ValueError(f"不支持的Provider: {provider}。支持的Provider: midjourney, ideogram, openai, replicate, fal-ai, tencent, baidu, aliyun, doubao, kling, gemini")

async def get_provider_by_model(model_name: str, api_key: str = None) -> BaseProvider:
    """
    根据模型名称获取对应的Provider实例（异步版本）

    Args:
        model_name: 模型名称
        api_key: API Key（可选），如果未提供则使用管理员统一配置

    Returns:
        Provider实例
    """
    from loguru import logger

    registry = await get_model_registry()
    mapping = registry.get_provider_mapping(model_name)

    if not mapping:
        raise ValueError(f"未找到模型 {model_name} 对应的Provider")

    logger.info(f"模型 {model_name} 映射到 Provider: {mapping.provider_type}")
    return await get_provider(provider=mapping.provider_type, api_key=api_key)
