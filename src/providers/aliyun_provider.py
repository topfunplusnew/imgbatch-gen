"""阿里通义Provider（通过中转站）"""

from typing import Optional, List

from ..models.image import ImageParams
from .sync_relay_provider import SyncRelayProvider
from ..config.settings import settings


class AliyunProvider(SyncRelayProvider):
    """阿里通义万相Provider（通过中转站）
    
    支持的模型:
    - wanx-v1: 通义万相V1，基础图像生成
    - wanx-sketch-to-image-v1: 素描转图像
    - wanx-style-repaint-v1: 风格重绘
    - wanx-v2: 通义万相V2，更高质量的图像生成
    - wanx-xpress: 通义万相Xpress，快速生成
    - wanx-lite: 通义万相Lite，轻量级快速生成
    - wanx-sketch-v1: 通义万相素描版
    - wanx-sculpture-v1: 通义万相雕塑版
    - wanx-3d-v1: 通义万相3D版
    - wanx-2d-v1: 通义万相2D版
    - wanx-cyberpunk-v1: 通义万相赛博朋克版
    - wanx-natural-v1: 通义万相自然风光版
    - wanx-anime-v1: 通义万相动漫版
    - wanx-painting-v1: 通义万相油画版
    - wanx-3d-cartoon-v1: 通义万相3D卡通版
    - flux: Flux模型（Black Forest Labs）
    - flux-schnell: Flux Schnell快速版
    
    特点:
    - 支持中文提示词
    - 多种风格模型可选
    - 高质量图像生成
    - 支持素描转图像
    - 支持风格重绘
    """
    
    # 通义万相支持的图像尺寸
    SUPPORTED_SIZES = [
        # 正方形
        "512x512",
        "1024x1024",
        # 横向
        "768x512",
        "1024x768",
        "1280x720",
        "1920x1080",
        # 纵向
        "512x768",
        "768x1024",
        "720x1280",
        "1080x1920",
    ]
    
    # 通义万相支持的风格（用于style参数）
    SUPPORTED_STYLES = [
        "<auto>",       # 自动风格
        "<3d cartoon>", # 3D卡通
        "<anime>",      # 动漫
        "<oil painting>", # 油画
        "<watercolor>", # 水彩
        "<sketch>",     # 素描
        "<chinese painting>", # 中国画
        "<photo>",      # 照片
        "<realistic>",  # 写实
        "<cyberpunk>",  # 赛博朋克
        "<fantasy>",    # 奇幻
        "<sci-fi>",     # 科幻
        "<pixel>",      # 像素
        "<steampunk>",  # 蒸汽朋克
        "<concept art>", # 概念艺术
    ]
    
    # 各模型的特点描述
    MODEL_DESCRIPTIONS = {
        "wanx-v1": "通义万相V1，基础图像生成，支持中文提示词",
        "wanx-v2": "通义万相V2，更高质量的图像生成，细节更丰富",
        "wanx-lite": "通义万相Lite，轻量级快速生成，适合批量生成",
        "wanx-xpress": "通义万相Xpress，快速生成，平衡质量和速度",
        "wanx-sketch-to-image-v1": "素描转图像，将素描转换为真实图像",
        "wanx-style-repaint-v1": "风格重绘，将图像转换为指定风格",
        "wanx-sketch-v1": "通义万相素描版，生成素描风格图像",
        "wanx-sculpture-v1": "通义万相雕塑版，生成雕塑风格图像",
        "wanx-3d-v1": "通义万相3D版，生成3D渲染风格图像",
        "wanx-2d-v1": "通义万相2D版，生成2D平面风格图像",
        "wanx-cyberpunk-v1": "通义万相赛博朋克版，生成赛博朋克风格",
        "wanx-natural-v1": "通义万相自然风光版，生成自然风景图像",
        "wanx-anime-v1": "通义万相动漫版，生成动漫风格图像",
        "wanx-painting-v1": "通义万相油画版，生成油画风格图像",
        "wanx-3d-cartoon-v1": "通义万相3D卡通版，生成3D卡通图像",
        "flux": "Flux模型，高质量图像生成",
        "flux-schnell": "Flux Schnell，快速生成版本",
    }
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """初始化阿里云Provider
        
        Args:
            base_url: 中转站基础URL，默认使用settings中的配置
            api_key: 中转站API Key，默认使用settings中的配置
        """
        super().__init__(base_url, api_key)
        self.model = settings.aliyun_image_model or "wanx-v1"
    
    def get_endpoint(self) -> str:
        """获取API端点"""
        return "/v1/images/generations"
    
    def get_timeout(self) -> float:
        """获取请求超时时间（阿里云生图可能需要较长时间）"""
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
            "n": min(params.n, 4),  # 阿里云最多支持4张
            "size": size,
        }
        
        # 添加风格
        if params.style:
            # 如果风格在支持列表中，使用原名称
            if params.style in self.SUPPORTED_STYLES:
                payload["style"] = params.style
            elif f"<{params.style}>" in self.SUPPORTED_STYLES:
                payload["style"] = f"<{params.style}>"
            else:
                # 否则作为自定义风格参数传递
                payload["style"] = params.style
        
        # 添加额外参数
        if params.extra_params:
            # 阿里云支持的质量参数 (standard, hd)
            if "quality" in params.extra_params:
                payload["quality"] = params.extra_params["quality"]
            
            # 阿里云支持的采样器
            if "sampler" in params.extra_params:
                payload["sampler"] = params.extra_params["sampler"]
            
            # 阿里云支持的引导强度
            if "guidance_scale" in params.extra_params:
                payload["guidance_scale"] = params.extra_params["guidance_scale"]
            
            # 阿里云支持的步数
            if "steps" in params.extra_params:
                payload["steps"] = params.extra_params["steps"]
            
            # 阿里云支持的种子
            if "seed" in params.extra_params:
                payload["seed"] = params.extra_params["seed"]
            
            # 负面提示词
            if "negative_prompt" in params.extra_params:
                payload["negative_prompt"] = params.extra_params["negative_prompt"]
            
            # 参考图像（用于图生图）
            if "ref_image" in params.extra_params:
                payload["ref_image"] = params.extra_params["ref_image"]
            
            # 重绘强度
            if "strength" in params.extra_params:
                payload["strength"] = params.extra_params["strength"]
        
        return payload
    
    def _normalize_size(self, width: int, height: int) -> str:
        """规范化尺寸到阿里云支持的尺寸
        
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
        
        if ratio > 1.5:
            # 宽屏
            if max(width, height) <= 720:
                return "1280x720"
            else:
                return "1920x1080"
        elif ratio > 1.2:
            # 稍宽
            if max(width, height) <= 768:
                return "768x512"
            else:
                return "1024x768"
        elif ratio < 0.67:
            # 竖屏
            if max(width, height) <= 1280:
                return "720x1280"
            else:
                return "1080x1920"
        elif ratio < 0.83:
            # 稍高
            if max(width, height) <= 768:
                return "512x768"
            else:
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
                raise ValueError(f"阿里云生图失败 [{error_code}]: {error_msg}")
            else:
                raise ValueError(f"阿里云生图失败: {error}")
        
        # 检查阿里云格式错误
        if "code" in response and response["code"] != "Success":
            error_code = response.get("code", "未知错误")
            error_msg = response.get("message", "未知错误")
            raise ValueError(f"阿里云生图失败 [{error_code}]: {error_msg}")
        
        # 检查DashScope格式错误
        if "output" in response and "code" in response["output"]:
            if response["output"]["code"] != "Success":
                error_code = response["output"].get("code", "未知错误")
                error_msg = response["output"].get("message", "未知错误")
                raise ValueError(f"阿里云生图失败 [{error_code}]: {error_msg}")
    
    def extract_image_urls(self, response: dict) -> List[str]:
        """提取图片URL
        
        Args:
            response: API响应
            
        Returns:
            图片URL列表
        """
        urls = []
        
        # OpenAI格式响应（中转站返回的格式）
        if "data" in response:
            for item in response["data"]:
                if "url" in item:
                    urls.append(item["url"])
                elif "b64_json" in item:
                    # 如果返回base64，需要特殊处理
                    pass
        
        # 阿里云DashScope格式响应
        elif "output" in response:
            output = response["output"]
            if "results" in output:
                for result in output["results"]:
                    if "url" in result:
                        urls.append(result["url"])
            elif "result" in output:
                result = output["result"]
                if isinstance(result, dict) and "url" in result:
                    urls.append(result["url"])
                elif isinstance(result, str):
                    # 可能是base64或URL
                    if result.startswith("http"):
                        urls.append(result)
        
        # 直接URL列表
        elif "urls" in response:
            urls.extend(response["urls"])
        
        return urls
