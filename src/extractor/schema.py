"""JSON Schema定义"""

IMAGE_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "图片生成的提示词描述"
        },
        "width": {
            "type": "integer",
            "description": "图片宽度（像素）",
            "default": 1024,
            "minimum": 256,
            "maximum": 4096
        },
        "height": {
            "type": "integer",
            "description": "图片高度（像素）",
            "default": 1024,
            "minimum": 256,
            "maximum": 4096
        },
        "style": {
            "type": "string",
            "description": "图片风格，如：realistic, cartoon, abstract, oil painting等",
            "enum": ["realistic", "cartoon", "abstract", "oil painting", "watercolor", "sketch", "anime", "3d", "photography", "digital art"]
        },
        "quality": {
            "type": "string",
            "description": "图片质量",
            "enum": ["standard", "hd", "high", "low"],
            "default": "standard"
        },
        "n": {
            "type": "integer",
            "description": "生成图片数量",
            "default": 1,
            "minimum": 1,
            "maximum": 10
        }
    },
    "required": ["prompt"]
}

EXTRACTION_PROMPT_TEMPLATE = """你是一个专业的参数提取助手。请从用户的自然语言描述中提取图片生成所需的参数，并返回JSON格式。

用户输入：{user_input}

请根据以下JSON Schema提取参数：
{schema}

要求：
1. 必须提取prompt字段（图片描述）
2. 如果用户没有明确指定尺寸，使用默认值1024x1024
3. 如果用户没有指定风格，可以不包含style字段
4. 只返回有效的JSON，不要包含其他解释文字
5. 如果用户输入中包含数字和尺寸相关描述，请正确提取width和height

返回格式示例：
{{
    "prompt": "a beautiful sunset over the ocean",
    "width": 1024,
    "height": 1024,
    "style": "realistic",
    "quality": "hd"
}}
"""


