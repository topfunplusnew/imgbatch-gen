"""图片相关模型定义"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ImageParams(BaseModel):
    """标准化生图参数"""
    prompt: str = Field(..., description="提示词")
    negative_prompt: Optional[str] = Field(None, description="负面提示词")
    model: Optional[str] = Field(None, description="模型名称")
    width: int = Field(1024, description="图片宽度")
    height: int = Field(1024, description="图片高度")
    style: Optional[str] = Field(None, description="风格")
    quality: Optional[str] = Field("standard", description="质量")
    n: int = Field(1, description="生成数量")
    seed: Optional[int] = Field(None, description="随机种子")
    provider: Optional[str] = Field(None, description="Provider名称")
    api_key: Optional[str] = Field(None, description="前端传入的API Key，优先于环境变量")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="额外参数")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "a beautiful sunset over the ocean",
                "width": 1024,
                "height": 1024,
                "style": "realistic",
                "quality": "hd",
                "n": 1
            }
        }


class ImageResult(BaseModel):
    """图片生成结果"""
    image_id: str = Field(..., description="图片ID")
    task_id: str = Field(..., description="任务ID")
    file_path: str = Field(..., description="本地文件路径")
    url: Optional[str] = Field(None, description="访问URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL（压缩预览）")
    width: int = Field(..., description="图片宽度")
    height: int = Field(..., description="图片高度")
    size: int = Field(..., description="文件大小（字节）")
    format: str = Field(..., description="图片格式（png/jpg等）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


