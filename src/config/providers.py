"""Provider配置管理"""

from typing import Dict, Any, Optional
from enum import Enum

from .settings import settings


class ProviderType(str, Enum):
    """Provider类型枚举"""
    OPENAI = "openai"
    STABLE_DIFFUSION = "stable_diffusion"
    BAIDU = "baidu"
    ALIYUN = "aliyun"
    OLLAMA = "ollama"
    LOCAL = "local"


class ProviderConfig:
    """Provider配置类"""
    
    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """获取OpenAI配置"""
        return {
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
            "model": settings.openai_model,
            "embedding_model": settings.openai_embedding_model,
            "image_model": settings.openai_image_model,
        }
    
    @staticmethod
    def get_ollama_config() -> Dict[str, Any]:
        """获取Ollama配置"""
        return {
            "base_url": settings.ollama_base_url,
            "model": settings.ollama_model,
            "embedding_model": settings.ollama_embedding_model,
        }
    
    @staticmethod
    def get_stable_diffusion_config() -> Dict[str, Any]:
        """获取Stable Diffusion配置"""
        return {
            "api_url": settings.stable_diffusion_api_url,
            "api_key": settings.stable_diffusion_api_key,
        }
    
    @staticmethod
    def get_baidu_config() -> Dict[str, Any]:
        """获取百度配置"""
        return {
            "api_key": settings.baidu_api_key,
            "secret_key": settings.baidu_secret_key,
            "image_model": settings.baidu_image_model,
        }
    
    @staticmethod
    def get_aliyun_config() -> Dict[str, Any]:
        """获取阿里云配置"""
        return {
            "api_key": settings.aliyun_api_key,
            "image_model": settings.aliyun_image_model,
        }
    
    @staticmethod
    def get_local_embedding_config() -> Dict[str, Any]:
        """获取本地Embedding配置"""
        return {
            "model": settings.local_embedding_model,
        }
    
    @staticmethod
    def get_provider_config(provider: str) -> Optional[Dict[str, Any]]:
        """根据Provider名称获取配置"""
        config_map = {
            ProviderType.OPENAI: ProviderConfig.get_openai_config,
            ProviderType.OLLAMA: ProviderConfig.get_ollama_config,
            ProviderType.STABLE_DIFFUSION: ProviderConfig.get_stable_diffusion_config,
            ProviderType.BAIDU: ProviderConfig.get_baidu_config,
            ProviderType.ALIYUN: ProviderConfig.get_aliyun_config,
            ProviderType.LOCAL: ProviderConfig.get_local_embedding_config,
        }
        
        provider_enum = ProviderType(provider.lower())
        if provider_enum in config_map:
            return config_map[provider_enum]()
        return None
    
    @staticmethod
    def validate_provider_config(provider: str) -> bool:
        """验证Provider配置是否完整"""
        config = ProviderConfig.get_provider_config(provider)
        if not config:
            return False
        
        # 检查必需字段
        if provider == ProviderType.OPENAI:
            return config.get("api_key") is not None
        elif provider == ProviderType.BAIDU:
            return config.get("api_key") is not None and config.get("secret_key") is not None
        elif provider == ProviderType.ALIYUN:
            return config.get("api_key") is not None
        elif provider == ProviderType.STABLE_DIFFUSION:
            return config.get("api_url") is not None
        
        return True

