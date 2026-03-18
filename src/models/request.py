"""请求模型定义"""

from typing import Optional, List
from pydantic import BaseModel, Field


class FileInput(BaseModel):
    """文件输入模型"""
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型（excel/csv/json/txt）")
    content: Optional[str] = Field(None, description="文件内容（文本格式）")
    file_path: Optional[str] = Field(None, description="文件路径")


class GenerateRequest(BaseModel):
    """生图请求模型"""
    prompt: str = Field(..., description="提示词（自然语言描述）")
    provider: Optional[str] = Field(None, description="指定Provider（可选，默认使用配置）")
    model_name: Optional[str] = Field(None, description="模型名称（可选，如果提供会自动选择对应的Provider）")
    
    class Config:
        protected_namespaces = ()  # 不保护任何命名空间，允许 model_name 字段
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")
    style: Optional[str] = Field(None, description="风格")
    quality: Optional[str] = Field(None, description="质量（standard/hd等）")
    n: Optional[int] = Field(1, description="生成数量")
    extra_params: Optional[dict] = Field(default_factory=dict, description="额外参数")
    user_id: Optional[str] = Field("anonymous", description="用户ID")


class BatchGenerateRequest(BaseModel):
    """批量生图请求模型"""
    prompts: Optional[List[str]] = Field(None, description="提示词列表")
    file: Optional[FileInput] = Field(None, description="文件输入")
    provider: Optional[str] = Field(None, description="指定Provider")
    default_params: Optional[dict] = Field(default_factory=dict, description="默认参数（应用于所有任务）")


class UnifiedGenerateRequest(BaseModel):
    """统一的生图请求模型 - 支持文件、对话内容、模型选择"""
    # 对话内容（单个或列表）
    prompt: Optional[str] = Field(None, description="单个提示词")
    prompts: Optional[List[str]] = Field(None, description="提示词列表")
    
    # 模型选择（优先使用 model_name）
    model_name: Optional[str] = Field(None, description="模型名称（可选，如果提供会自动选择对应的Provider）")
    provider: Optional[str] = Field(None, description="指定Provider（可选，默认使用配置）")
    
    # 图片参数
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")
    style: Optional[str] = Field(None, description="风格")
    quality: Optional[str] = Field(None, description="质量（standard/hd等）")
    n: Optional[int] = Field(1, description="生成数量")
    extra_params: Optional[dict] = Field(default_factory=dict, description="额外参数")
    
    class Config:
        protected_namespaces = ()  # 不保护任何命名空间，允许 model_name 字段

