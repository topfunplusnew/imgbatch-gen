"""模型查询接口"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional

from ...config.model_registry import get_model_registry

router = APIRouter(prefix="/api/v1", tags=["models"])


@router.get("/models")
async def list_models(
    request: Request,
    model_type: Optional[str] = None,
    keyword: Optional[str] = None
):
    """
    列出所有可用的图像模型
    
    Args:
        model_type: 模型类型过滤（图像/文本）
        keyword: 关键词搜索
    """
    try:
        model_registry = getattr(request.app.state, "model_registry", None)
        if not model_registry:
            # 如果注册表未初始化，尝试初始化
            model_registry = await get_model_registry()
            request.app.state.model_registry = model_registry
        
        if keyword:
            model_names = model_registry.search_models(keyword)
        elif model_type == "image":
            model_names = model_registry.list_image_models()
        elif model_type == "chat":
            model_names = model_registry.list_chat_models()
        else:
            # 默认只返回聊天和生图模型
            model_names = model_registry.list_chat_models() + model_registry.list_image_models()

        # 获取详细信息
        models_info = []

        # 允许显示的异步模型白名单
        async_whitelist = {
            "fal-ai/bytedance/seedream/v4/text-to-image",
            "fal-ai/flux-1/dev",
            "fal-ai/flux-1/schnell",
            "fal-ai/flux-lora",
            "fal-ai/flux-pro/kontext/max/text-to-image",
            "fal-ai/flux-pro/kontext/text-to-image",
            "fal-ai/nano-banana"
        }

        for model_name in model_names:
            model_info = model_registry.get_model_info(model_name)
            if model_info:
                mapping = model_registry.get_provider_mapping(model_name)
                tags = [t.strip() for t in model_info.tags.split(",") if t.strip()] if model_info.tags else []

                # 过滤异步模型：如果tags中有"异步"且不在白名单中，则跳过
                has_async_tag = "异步" in tags
                if has_async_tag and model_name not in async_whitelist:
                    continue

                models_info.append({
                    "model_name": model_info.model_name,
                    "description": model_info.description,
                    "model_type": model_info.model_type,
                    "vendor_name": model_info.vendor_name,
                    "tags": tags,
                    "supported_endpoint_types": model_info.supported_endpoint_types,
                    "provider": mapping.provider_type if mapping else None,
                    "is_async": mapping.is_async if mapping else False,
                })
        
        return {
            "total": len(models_info),
            "models": models_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/models/refresh")
async def refresh_models_get(request: Request):
    """手动刷新模型配置（GET方法，方便浏览器直接访问）"""
    try:
        return await _refresh_models_impl(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新模型配置失败: {str(e)}")


@router.get("/models/{model_name}")
async def get_model_info(
    model_name: str,
    request: Request
):
    """获取指定模型的详细信息"""
    try:
        model_registry = getattr(request.app.state, "model_registry", None)
        if not model_registry:
            model_registry = await get_model_registry()
            request.app.state.model_registry = model_registry
        
        model_info = model_registry.get_model_info(model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"模型 {model_name} 不存在")
        
        mapping = model_registry.get_provider_mapping(model_name)
        
        return {
            "model_name": model_info.model_name,
            "description": model_info.description,
            "model_type": model_info.model_type,
            "vendor_name": model_info.vendor_name,
            "vendor_id": model_info.vendor_id,
            "tags": model_info.tags,
            "supported_endpoint_types": model_info.supported_endpoint_types,
            "enable_groups": model_info.enable_groups,
            "endpoints": model_info.endpoints,
            "provider": {
                "type": mapping.provider_type if mapping else None,
                "is_async": mapping.is_async if mapping else False,
                "endpoint_path": mapping.endpoint_path if mapping else None,
            } if mapping else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


async def _refresh_models_impl(request: Request):
    """刷新模型配置的实现函数"""
    model_registry = getattr(request.app.state, "model_registry", None)
    if not model_registry:
        model_registry = await get_model_registry()
        request.app.state.model_registry = model_registry
    
    await model_registry.refresh(force=True)
    
    return {
        "message": "模型配置刷新成功",
        "total_models": len(model_registry.list_all_models()),
        "last_update": model_registry.last_update.isoformat() if model_registry.last_update else None
    }


@router.post("/models/refresh")
async def refresh_models_post(request: Request):
    """手动刷新模型配置（POST方法）"""
    try:
        return await _refresh_models_impl(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新模型配置失败: {str(e)}")

