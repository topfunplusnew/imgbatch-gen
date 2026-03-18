"""LLM参数提取器基础接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import json

from ..models.image import ImageParams
from .schema import IMAGE_PARAMS_SCHEMA, EXTRACTION_PROMPT_TEMPLATE


class BaseExtractor(ABC):
    """基础提取器接口"""
    
    @abstractmethod
    async def extract(self, user_input: str) -> ImageParams:
        """
        从自然语言输入中提取参数
        
        Args:
            user_input: 用户输入的自然语言描述
            
        Returns:
            提取的参数对象
        """
        pass
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应为字典"""
        # 尝试提取JSON
        response = (response or "").strip()
        
        # 如果响应包含代码块，提取其中的JSON
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    json_str = part.replace("json", "").strip()
                elif part.strip().startswith("{"):
                    json_str = part.strip()
                else:
                    continue
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        # 尝试直接解析
        if response.startswith("{") and response.endswith("}"):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        # 如果无法解析，返回包含prompt的默认结构
        return {"prompt": response}
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> ImageParams:
        """验证并规范化参数"""
        # 提取prompt
        prompt = data.get("prompt", "")
        if not prompt:
            raise ValueError("无法提取prompt参数")
        
        # 提取尺寸
        width = data.get("width", 1024)
        height = data.get("height", 1024)
        
        # 确保尺寸在合理范围内
        width = max(256, min(4096, int(width)))
        height = max(256, min(4096, int(height)))
        
        # 提取其他参数
        style = data.get("style")
        quality = data.get("quality", "standard")
        n = max(1, min(10, int(data.get("n", 1))))
        
        return ImageParams(
            prompt=prompt,
            width=width,
            height=height,
            style=style,
            quality=quality,
            n=n,
            extra_params={k: v for k, v in data.items() if k not in ["prompt", "width", "height", "style", "quality", "n"]}
        )
    
    def _build_prompt(self, user_input: str) -> str:
        """构建提取提示词"""
        schema_str = json.dumps(IMAGE_PARAMS_SCHEMA, indent=2, ensure_ascii=False)
        return EXTRACTION_PROMPT_TEMPLATE.format(
            user_input=user_input,
            schema=schema_str
        )

