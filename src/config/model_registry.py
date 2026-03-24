"""模型注册表 - 动态模型发现和管理"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import httpx
from loguru import logger

from .settings import FIXED_CONFIG_API_URL, settings


@dataclass
class ModelInfo:
    """模型信息"""
    model_name: str
    description: str
    model_type: str  # 文本/图像
    vendor_id: int
    vendor_name: str
    supported_endpoint_types: List[str]
    endpoints: Dict[str, Dict[str, str]] = field(default_factory=dict)
    tags: str = ""
    enable_groups: List[str] = field(default_factory=list)


@dataclass
class ProviderMapping:
    """Provider映射信息"""
    provider_type: str  # midjourney, ideogram, openai等
    endpoint_path: Optional[str] = None  # API端点路径
    is_async: bool = False  # 是否需要轮询


class ModelRegistry:
    """模型注册表 - 管理所有可用模型"""
    
    def __init__(self, config_api_url: str = FIXED_CONFIG_API_URL):
        """初始化模型注册表"""
        self.config_api_url = config_api_url
        self.models: Dict[str, ModelInfo] = {}
        self.model_to_provider: Dict[str, ProviderMapping] = {}
        self.vendors: Dict[int, str] = {}
        self.last_update: Optional[datetime] = None
        self.cache_ttl = timedelta(hours=1)  # 缓存1小时
        self._lock = asyncio.Lock()
    
    async def refresh(self, force: bool = False):
        """刷新模型配置"""
        async with self._lock:
            # 检查缓存是否有效
            if not force and self.last_update:
                if datetime.now() - self.last_update < self.cache_ttl:
                    logger.debug("模型配置缓存有效，跳过刷新")
                    return
            
            try:
                logger.info(f"从API获取模型配置: {self.config_api_url}")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.config_api_url)
                    response.raise_for_status()
                    data = json.loads(response.content.decode("utf-8"))
                
                # 解析供应商信息
                self._parse_vendors(data.get("vendors", []))
                
                # 解析模型信息
                self._parse_models(data.get("data", []), data.get("endpoints", {}))
                
                # 建立模型到Provider的映射
                self._build_provider_mapping()
                
                self.last_update = datetime.now()
                logger.info(f"模型配置刷新成功，共 {len(self.models)} 个模型")
                
            except Exception as e:
                logger.error(f"刷新模型配置失败: {str(e)}")
                if not self.models:
                    raise  # 如果没有任何模型，抛出异常
    
    def _parse_vendors(self, vendors: List[Dict[str, Any]]):
        """解析供应商信息"""
        self.vendors = {}
        for vendor in vendors:
            vendor_id = vendor.get("id")
            vendor_name = vendor.get("name", "")
            if vendor_id:
                self.vendors[vendor_id] = vendor_name
    
    def _parse_models(self, models_data: List[Dict[str, Any]], endpoints: Dict[str, Any]):
        """解析模型信息"""
        self.models = {}
        
        for model_data in models_data:
            model_name = model_data.get("model_name", "")
            if not model_name:
                continue
            
            model_type = model_data.get("model_type", "")
            vendor_id = model_data.get("vendor_id", 0)
            vendor_name = self.vendors.get(vendor_id, "")
            
            # 只关注图像和文本模型
            if model_type not in ("图像", "文本"):
                continue
            
            model_info = ModelInfo(
                model_name=model_name,
                description=model_data.get("description", ""),
                model_type=model_type,
                vendor_id=vendor_id,
                vendor_name=vendor_name,
                supported_endpoint_types=model_data.get("supported_endpoint_types", []),
                tags=model_data.get("tags", ""),
                enable_groups=model_data.get("enable_groups", []),
            )
            
            # 提取该模型的端点信息
            vendor_name_lower = vendor_name.lower()
            if vendor_name_lower in endpoints:
                model_info.endpoints = endpoints[vendor_name_lower]
            
            self.models[model_name.lower()] = model_info
    
    def _build_provider_mapping(self):
        """建立模型名称到Provider的映射"""
        self.model_to_provider = {}
        
        # 供应商名称到Provider类型的映射
        vendor_to_provider = {
            "midjourney": "midjourney",
            "ideogram": "ideogram",
            "openai": "openai",
            "replicate": "replicate",
            "fal-ai": "fal-ai",
            "tencent": "tencent",
            "google": "gemini",  # Google Gemini/Imagen
            "百度": "baidu",  # 百度文心一格
            "baidu": "baidu",  # 百度（英文）
            "阿里云": "aliyun",  # 阿里云通义万相
            "aliyun": "aliyun",  # 阿里云（英文）
            "alibaba": "aliyun",  # 阿里巴巴
            "bailian": "aliyun",  # 阿里云百炼
            "通义": "aliyun",  # 通义万相
            "doubao": "openai",  # 豆包图像模型使用OpenAI兼容接口
            "doubao (豆包)": "openai",  # 豆包（带括号格式）
            "豆包": "openai",  # 豆包（中文）
            "kling": "openai",  # 可灵图像模型使用OpenAI兼容接口
            "kling (可灵)": "openai",  # 可灵（带括号格式）
        }

        # 端点类型到Provider类型的映射
        endpoint_to_provider = {
            # OpenAI 兼容接口
            "openai": "openai",
            "openai-response": "openai",
            "gemini": "openai",
            "geminitts": "openai",
            "anthropic": "openai",
            "image-generation": "openai",
            "dall-e-3": "openai",
            "embedding": "openai",
            "rerank": "openai",
            # 嵌入相关（中文端点）
            "嵌入": "openai",
            "嵌入chat格式": "openai",
            "嵌入兼容格式": "openai",
            "嵌入原生格式": "openai",
            "嵌入格式1": "openai",
            # TTS / 语音相关 → openai
            "文本转语音": "openai",
            "语音转文字": "openai",
            "异步语音": "openai",
            "同步语音": "openai",
            # Fal AI 异步接口
            "fal-ai": "fal-ai",
            # Replicate 异步接口
            "replicate": "replicate",
            # Midjourney（中文端点）
            "mj_imagine": "midjourney",
            "mj动作": "midjourney",
            "mj图片上传": "midjourney",
            "mj想象模式": "midjourney",
            "mj描述模式": "midjourney",
            "mj模态模式": "midjourney",
            "mj混合": "midjourney",
            # Ideogram（中文端点）
            "ideogram": "ideogram",
            "图生文": "ideogram",
            "图片编辑": "ideogram",
            "图片重制": "ideogram",
            "放大": "ideogram",
            "替换背景": "ideogram",
            "重构": "ideogram",
            "文生图": "ideogram",
            # Kling 可灵（中文端点）→ openai 兼容
            "kling生图": "openai",
            "图像识别": "openai",
            "对口型": "openai",
            "动作控制": "openai",
            "多模态视频编辑": "openai",
            "自定义音色": "openai",
            "数字人": "openai",
            "omni-image": "openai",
            "omni-video": "openai",
            "custom-elements": "openai",
            # 视频相关 → openai 兼容
            "视频统一格式": "openai",
            "openAI视频格式": "openai",
            "openAI官方视频格式": "openai",
            "图生视频": "openai",
            "文生视频": "openai",
            "视频延长": "openai",
            "视频特效": "openai",
            "视频生音效": "openai",
            "文生音效": "openai",
            "语音合成": "openai",
            "豆包视频异步": "openai",
            "海螺视频生成": "openai",
            "wan视频生成": "openai",
            "luma视频生成": "openai",
            "luma视频扩展": "openai",
            "runway图生视频": "openai",
            "grok视频": "openai",
            "suno音乐生成": "openai",
            "vidu生图": "openai",
            "vidu图生视频": "openai",
            "vidu文生视频": "openai",
            "vidu文生音效": "openai",
            "vidu参考生视频": "openai",
            "vidu首尾帧": "openai",
            "vidu语音合成": "openai",
            "创建角色": "openai",
            "aigc-image": "openai",
            "aigc-video": "openai",
        }
        
        for model_name, model_info in self.models.items():
            provider_type = None
            endpoint_path = None
            is_async = False
            
            # 方法1: 根据供应商名称映射（支持前缀匹配，处理带括号后缀的情况）
            vendor_name_lower = model_info.vendor_name.lower()
            if vendor_name_lower in vendor_to_provider:
                provider_type = vendor_to_provider[vendor_name_lower]
            else:
                for vendor_key, provider_val in vendor_to_provider.items():
                    if vendor_name_lower.startswith(vendor_key):
                        provider_type = provider_val
                        break
            
            # 方法2: 根据端点类型映射（精确匹配 + 前缀匹配）
            # 注意：dall-e-3/image-generation 端点类型强制覆盖 vendor 映射
            force_by_endpoint = any(
                t in ("dall-e-3", "image-generation") for t in model_info.supported_endpoint_types
            )
            if not provider_type or force_by_endpoint:
                for endpoint_type in model_info.supported_endpoint_types:
                    if endpoint_type in endpoint_to_provider:
                        provider_type = endpoint_to_provider[endpoint_type]
                        if provider_type in ("fal-ai", "replicate"):
                            is_async = True
                        break
                    # 前缀匹配：处理 fal-ai/xxx、replicate/xxx、stability-ai/xxx 等
                    for prefix, ptype in (
                        ("fal-ai/", "fal-ai"),
                        ("black-forest-labs/", "fal-ai"),
                        ("flux-kontext-apps/", "fal-ai"),
                        ("google/", "fal-ai"),
                        ("ideogram-ai/", "ideogram"),
                        ("recraft-ai/", "fal-ai"),
                        ("stability-ai/", "replicate"),
                        ("lucataco/", "replicate"),
                        ("andreasjansson/", "replicate"),
                        ("prunaai/", "replicate"),
                        ("minimax/", "replicate"),
                        ("cjwbw/", "replicate"),
                        ("sujaykhandekar/", "replicate"),
                        ("riffusion/", "replicate"),
                    ):
                        if endpoint_type.startswith(prefix):
                            provider_type = ptype
                            is_async = True
                            break
                    if provider_type:
                        break
            
            # gemini 图像模型走 gemini provider
            if provider_type == "openai" and "gemini" in model_name.lower() and model_info.model_type == "图像":
                provider_type = "gemini"
            # imagen 模型也走 gemini provider
            if "imagen" in model_name.lower() and model_info.model_type == "图像":
                provider_type = "gemini"

            # 方法3: 根据模型名称关键词映射
            if not provider_type:
                model_name_lower = model_name.lower()
                if "mj" in model_name_lower or "midjourney" in model_name_lower:
                    provider_type = "midjourney"
                    is_async = True
                elif "ideogram" in model_name_lower:
                    provider_type = "ideogram"
                elif ("dall" in model_name_lower or "openai" in model_name_lower
                      or "gpt-image" in model_name_lower or model_name_lower.startswith("gpt-")
                      or model_name_lower.startswith("o1") or model_name_lower.startswith("o3")
                      or model_name_lower.startswith("o4") or "mistral" in model_name_lower
                      or "ernie" in model_name_lower or "suno" in model_name_lower
                      or "dolphin" in model_name_lower):
                    provider_type = "openai"
                elif "replicate" in model_name_lower or "flux" in model_name_lower:
                    provider_type = "replicate"
                    is_async = True
                elif "fal" in model_name_lower or "nano-banana" in model_name_lower:
                    provider_type = "fal-ai"
                    is_async = True
                elif "tencent" in model_name_lower or "hunyuan" in model_name_lower or "gem" in model_name_lower:
                    provider_type = "tencent"
                    is_async = True
                elif "doubao" in model_name_lower or "seedream" in model_name_lower:
                    provider_type = "openai"  # 豆包/Seedream使用OpenAI兼容接口
                # 百度文心一格模型
                elif "ernie-vilg" in model_name_lower or "文心" in model_name_lower:
                    provider_type = "baidu"
                # 阿里云通义万相模型 (wanx, qwen-image, 通义)
                elif "wanx" in model_name_lower or "通义" in model_name_lower:
                    provider_type = "aliyun"
                elif "qwen" in model_name_lower:
                    provider_type = "openai"  # qwen-image-edit 走 /v1/images/generations
                # 可灵图像模型
                elif "kling" in model_name_lower:
                    provider_type = "openai"
            
            # 提取端点路径
            if model_info.endpoints:
                # 查找生成端点
                if "生成" in model_info.endpoints:
                    endpoint_path = model_info.endpoints["生成"].get("path")
                elif "generate" in model_info.endpoints:
                    endpoint_path = model_info.endpoints["generate"].get("path")
            
            if provider_type:
                self.model_to_provider[model_name] = ProviderMapping(
                    provider_type=provider_type,
                    endpoint_path=endpoint_path,
                    is_async=is_async
                )
                logger.debug(f"模型 {model_name} 映射到 Provider: {provider_type}")
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self.models.get(model_name.lower())
    
    def get_provider_mapping(self, model_name: str) -> Optional[ProviderMapping]:
        """获取模型对应的Provider映射"""
        return self.model_to_provider.get(model_name.lower())
    
    def list_image_models(self) -> List[str]:
        """列出所有图像模型名称（返回原始模型名称）"""
        return [model_info.model_name for model_info in self.models.values() if model_info.model_type == "图像"]

    def list_chat_models(self) -> List[str]:
        """列出所有文本/聊天模型名称"""
        return [model_info.model_name for model_info in self.models.values() if model_info.model_type == "文本"]

    def list_all_models(self) -> List[str]:
        """列出所有模型名称"""
        return [model_info.model_name for model_info in self.models.values()]

    def search_models(self, keyword: str) -> List[str]:
        """搜索模型（根据关键词）"""
        keyword_lower = keyword.lower()
        results = []
        for model_name, model_info in self.models.items():
            if (keyword_lower in model_name or 
                keyword_lower in model_info.description.lower() or
                keyword_lower in model_info.vendor_name.lower()):
                results.append(model_info.model_name)
        return results


# 全局模型注册表实例
_model_registry: Optional[ModelRegistry] = None


async def get_model_registry() -> ModelRegistry:
    """获取模型注册表实例（单例模式）"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry(settings.config_api_url)
        await _model_registry.refresh()
    return _model_registry

