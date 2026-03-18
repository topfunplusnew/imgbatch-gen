"""参数模板库"""

from typing import List, Dict, Any
from ..models.image import ImageParams

# 预设的参数模板
PARAMETER_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "realistic_photo",
        "description": "写实摄影风格",
        "params": {
            "style": "realistic",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["写实", "照片", "摄影", "realistic", "photo", "photography"]
    },
    {
        "name": "cartoon_style",
        "description": "卡通风格",
        "params": {
            "style": "cartoon",
            "quality": "standard",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["卡通", "动画", "cartoon", "anime", "animation"]
    },
    {
        "name": "abstract_art",
        "description": "抽象艺术风格",
        "params": {
            "style": "abstract",
            "quality": "standard",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["抽象", "艺术", "abstract", "art", "artistic"]
    },
    {
        "name": "oil_painting",
        "description": "油画风格",
        "params": {
            "style": "oil painting",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["油画", "绘画", "oil", "painting", "paint"]
    },
    {
        "name": "watercolor",
        "description": "水彩画风格",
        "params": {
            "style": "watercolor",
            "quality": "standard",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["水彩", "watercolor", "water"]
    },
    {
        "name": "sketch",
        "description": "素描风格",
        "params": {
            "style": "sketch",
            "quality": "standard",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["素描", "草图", "sketch", "drawing"]
    },
    {
        "name": "anime",
        "description": "动漫风格",
        "params": {
            "style": "anime",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["动漫", "二次元", "anime", "manga", "2d"]
    },
    {
        "name": "3d_render",
        "description": "3D渲染风格",
        "params": {
            "style": "3d",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["3d", "三维", "渲染", "render", "3d model"]
    },
    {
        "name": "digital_art",
        "description": "数字艺术风格",
        "params": {
            "style": "digital art",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["数字", "数字艺术", "digital", "digital art", "cg"]
    },
    {
        "name": "portrait",
        "description": "人像摄影",
        "params": {
            "style": "photography",
            "quality": "hd",
            "width": 1024,
            "height": 1024,
        },
        "keywords": ["人像", "肖像", "portrait", "person", "face"]
    },
]


def get_template_by_name(name: str) -> Dict[str, Any]:
    """根据名称获取模板"""
    for template in PARAMETER_TEMPLATES:
        if template["name"] == name:
            return template
    return None


def get_all_templates() -> List[Dict[str, Any]]:
    """获取所有模板"""
    return PARAMETER_TEMPLATES


