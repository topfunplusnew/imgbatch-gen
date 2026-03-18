"""宽高比像素尺寸映射配置

基于1024最大边长的标准像素尺寸，与前端保持一致
"""

# 标准宽高比对应的基准像素尺寸（1024最大边长）
ASPECT_RATIO_SIZES = {
    "1:1": (1024, 1024),      # 正方形
    "3:4": (768, 1024),       # 竖版
    "4:3": (1024, 768),       # 横版
    "9:16": (576, 1024),      # 竖版/手机
    "16:9": (1024, 576),      # 宽屏/视频
    "2:3": (683, 1024),       # 竖版
    "3:2": (1024, 683),       # 横屏/相机
    "4:5": (819, 1024),       # 竖版
    "5:4": (1024, 819),       # 横版
    "16:10": (1024, 640),     # 宽屏显示器
    "21:9": (1024, 439),     # 超宽屏/影院
}

# 质量等级对应的最大边长
QUALITY_MAX_DIMENSIONS = {
    "720p": 1024,
    "2k": 2048,
    "4k": 3840,
    "hd": 2048,
    "high": 2048,
    "standard": 1024,
    "low": 1024,
}

def get_size_for_aspect_ratio(aspect_ratio: str, quality: str = "2k") -> tuple[int, int]:
    """
    根据宽高比和质量等级获取像素尺寸

    Args:
        aspect_ratio: 宽高比，如 "4:5", "16:9"
        quality: 质量等级，如 "720p", "2k", "4k"

    Returns:
        (width, height) 像素尺寸元组
    """
    # 获取基准尺寸
    base_size = ASPECT_RATIO_SIZES.get(aspect_ratio)
    if not base_size:
        # 如果没有找到对应比例，返回默认1024x1024
        return (1024, 1024)

    # 获取最大边长
    max_dim = QUALITY_MAX_DIMENSIONS.get(quality, 2048)

    base_width, base_height = base_size

    # 计算比例
    ratio_value = base_width / base_height

    # 根据最大边长和比例计算最终尺寸
    if ratio_value >= 1:
        # 横向或方形图片
        final_width = max_dim
        final_height = round(max_dim / ratio_value)
    else:
        # 竖向图片
        final_height = max_dim
        final_width = round(max_dim * ratio_value)

    return (final_width, final_height)

def get_aspect_ratio_for_dimensions(width: int, height: int) -> str:
    """
    根据像素尺寸获取最接近的标准宽高比

    Args:
        width: 宽度
        height: 高度

    Returns:
        标准宽高比字符串
    """
    if not width or not height:
        return "1:1"

    ratio = width / height

    # 定义标准比例及其容差范围（±5%）
    aspect_ratios = [
        ("1:1", 1.0, 0.05),
        ("4:5", 0.8, 0.05),
        ("2:3", 0.667, 0.05),
        ("3:4", 0.75, 0.05),
        ("9:16", 0.5625, 0.05),
        ("3:2", 1.5, 0.05),
        ("4:3", 1.333, 0.05),
        ("5:4", 1.25, 0.05),
        ("16:9", 1.778, 0.05),
        ("16:10", 1.6, 0.05),
        ("21:9", 2.333, 0.05)
    ]

    # 先尝试精确匹配
    for ar_name, ar_value, tolerance in aspect_ratios:
        if abs(ratio - ar_value) <= tolerance:
            # 添加调试日志
            from loguru import logger
            logger.info(f"[宽高比] 尺寸 {width}x{height} (比例 {ratio:.3f}) 匹配到 {ar_name} (目标 {ar_value:.3f}, 差值 {abs(ratio - ar_value):.4f})")
            return ar_name

    # 如果没有匹配到，返回最接近的
    closest = min(aspect_ratios, key=lambda x: abs(ratio - x[1]))
    # 添加调试日志
    from loguru import logger
    logger.warning(f"[宽高比] 尺寸 {width}x{height} (比例 {ratio:.3f}) 未在容差范围内匹配到标准比例，使用最接近的: {closest[0]}")
    return closest[0]