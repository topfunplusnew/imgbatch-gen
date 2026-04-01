"""百度文心Provider（通过中转站）"""

from typing import Optional, List

from ..models.image import ImageParams
from .sync_relay_provider import SyncRelayProvider
from ..config.settings import settings


class BaiduProvider(SyncRelayProvider):
    """百度文心生图Provider（通过中转站）
    
    支持的模型:
    - ernie-vilg-v2: 百度文心一格V2，支持中文提示词
    - sd_xl: Stable Diffusion XL
    
    特点:
    - 支持中文提示词
    - 支持多种风格
    - 高质量图像生成
    """
    
    # 百度支持的图像尺寸
    SUPPORTED_SIZES = [
        "512x512",
        "1024x1024", 
        "768x768",
        "1024x768",
        "768x1024",
    ]
    
    # 百度支持的风格
    SUPPORTED_STYLES = [
        "探索无限",  # 默认风格
        "古风", 
        "二次元", 
        "写实风格", 
        "浮世绘", 
        "低多边形", 
        "未来主义",
        "像素风格", 
        "概念艺术", 
        "赛博朋克", 
        "洛丽塔风格", 
        "巴洛克风格", 
        "极简主义", 
        "水彩画", 
        "蒸汽波", 
        "油画", 
        "卡通画",
    ]
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化百度Provider
        
        Args:
            base_url: 中转站基础URL，默认使用settings中的配置
            api_key: 中转站API Key，默认使用settings中的配置
        """
        super().__init__(base_url, api_key)
        self.model = settings.baidu_image_model or "ernie-vilg-v2"
    
    def get_endpoint(self) -> str:
        """获取API端点"""
        return "/v1/images/generations"
    
    def get_timeout(self) -> float:
        """获取请求超时时间（百度生图可能需要较长时间）"""
        return 180.0
    
    def build_payload(self, params: ImageParams) -> dict:
        """构建请求参数
        
        Args:
            params: 图像生成参数
            
        Returns:
            请求payload
        """
        # 处理尺寸
        size = self._normalize_size(params.width, params.height)
        
        payload = {
            "model": self.model,
            "prompt": params.prompt,
            "n": min(params.n, 4),  # 百度最多支持4张
            "size": size,
        }
        
        # 添加风格
        if params.style:
            # 如果风格在支持列表中，使用原名称
            if params.style in self.SUPPORTED_STYLES:
                payload["style"] = params.style
            else:
                # 否则作为自定义风格参数传递
                payload["style"] = params.style
        
        # 添加额外参数
        if params.extra_params:
            # 百度支持的质量参数
            if "quality" in params.extra_params:
                payload["quality"] = params.extra_params["quality"]
            
            # 百度支持的采样器
            if "sampler" in params.extra_params:
                payload["sampler"] = params.extra_params["sampler"]
            
            # 百度支持的引导强度
            if "guidance_scale" in params.extra_params:
                payload["guidance_scale"] = params.extra_params["guidance_scale"]
        
        return payload
    
    def _normalize_size(self, width: int, height: int) -> str:
        """规范化尺寸到百度支持的尺寸
        
        Args:
            width: 宽度
            height: 高度
            
        Returns:
            规范化后的尺寸字符串
        """
        size = f"{width}x{height}"
        
        # 如果是支持的尺寸，直接返回
        if size in self.SUPPORTED_SIZES:
            return size
        
        # 否则根据宽高比选择最接近的尺寸
        ratio = width / height
        
        if ratio > 1.2:
            # 宽图
            return "1024x768"
        elif ratio < 0.8:
            # 高图
            return "768x1024"
        elif max(width, height) <= 512:
            return "512x512"
        else:
            return "1024x1024"
    
    def check_error(self, response: dict):
        """检查响应错误
        
        Args:
            response: API响应
            
        Raises:
            ValueError: 如果响应包含错误
        """
        # 检查OpenAI格式错误
        if "error" in response:
            error = response["error"]
            if isinstance(error, dict):
                error_msg = error.get("message", "未知错误")
                error_code = error.get("code", "")
                raise ValueError(f"百度生图失败 [{error_code}]: {error_msg}")
            else:
                raise ValueError(f"百度生图失败: {error}")
        
        # 检查百度格式错误
        if "error_code" in response:
            error_code = response.get("error_code")
            error_msg = response.get("error_msg", "未知错误")
            raise ValueError(f"百度生图失败 [{error_code}]: {error_msg}")
        
        # 检查其他错误格式
        if response.get("code") not in (0, None, 1, 200):
            error_msg = response.get("message", response.get("msg", "未知错误"))
            raise ValueError(f"百度生图失败: {error_msg}")
    
    def extract_image_urls(self, response: dict) -> List[str]:
        """提取图片URL
        
        Args:
            response: API响应
            
        Returns:
            图片URL列表
        """
        urls = []
        
        # OpenAI格式响应
        if "data" in response:
            for item in response["data"]:
                if "url" in item:
                    urls.append(item["url"])
                elif "b64_json" in item:
                    # 如果返回base64，需要特殊处理
                    # 这里暂时不处理，由父类处理
                    pass
        
        # 百度格式响应
        elif "data" in response and isinstance(response["data"], dict):
            # 百度可能返回任务ID，需要轮询获取结果
            if "task_id" in response["data"]:
                # 这里需要特殊处理异步任务
                # 暂时返回空，由具体实现处理
                pass
            elif "image_urls" in response["data"]:
                urls.extend(response["data"]["image_urls"])
        
        return urls