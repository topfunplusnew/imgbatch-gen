"""生图接口"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from ...models.request import GenerateRequest
from ...models.task import ImageTask
from ...models.image import ImageParams
from ...engine import TaskManager
from ...extractor import get_extractor
from ...matcher import get_matcher
from ...providers import get_provider_by_model
from ...config.settings import settings
from ...config.model_registry import get_model_registry
from ...database import get_db_manager
from ..routes.chat import _extract_api_key
from ..auth import RequiredAuthDependency

router = APIRouter(prefix="/api/v1", tags=["generate"])


# ==================== 响应模型 ====================


class GenerationRecordResponse(BaseModel):
    """生成历史记录响应"""
    id: str
    user_request_id: str
    provider: str
    model: str
    prompt: str
    negative_prompt: str = ""
    width: int
    height: int
    n: int
    style: Optional[str] = None
    quality: Optional[str] = None
    status: str
    image_urls: List[str] = []
    image_paths: List[str] = []
    processing_time: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: str
    extra_params: dict = {}


class UnifiedGenerationRecord(BaseModel):
    """统一生成记录响应模型"""
    id: str
    type: Literal["chat", "async"]  # 标识来源
    model: str
    prompt: str
    status: str
    image_urls: List[str] = []
    timestamp: str  # 统一时间戳
    created_at: str  # 显示用时间

    # 可选字段
    provider: Optional[str] = None
    platform: Optional[str] = None  # 异步任务的平台
    processing_time: Optional[float] = None
    error: Optional[str] = None


def get_task_manager(request: Request) -> TaskManager:
    """获取任务管理器（依赖注入）"""
    return request.app.state.task_manager


@router.post("/generate", response_model=ImageTask)
async def generate_image(
    request: GenerateRequest,
    http_request: Request,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """单图生成接口"""
    try:
        from loguru import logger
        db_manager = get_db_manager()
        
        # 1. 确定使用的Provider
        provider_name = request.provider
        
        # 如果提供了模型名称，尝试从模型注册表查找
        if request.model_name:
            try:
                model_registry = getattr(http_request.app.state, "model_registry", None)
                if model_registry:
                    mapping = model_registry.get_provider_mapping(request.model_name)
                    if mapping:
                        provider_name = mapping.provider_type
                        logger.info(f"模型 {request.model_name} 自动映射到 Provider: {provider_name}")
                    else:
                        logger.warning(f"模型 {request.model_name} 未找到对应的 Provider 映射")
                else:
                    logger.warning("模型注册表未初始化，无法通过模型名称查找 Provider")
            except Exception as e:
                logger.warning(f"无法从模型注册表查找模型 {request.model_name}: {str(e)}")
        
        # 如果最终还是没有 provider，使用默认值
        if not provider_name:
            provider_name = settings.default_image_provider
            logger.debug(f"未指定 Provider，使用默认值: {provider_name}")
        
        # 2. 构建参数
        request_api_key = _require_api_key(http_request)

        params = ImageParams(
            prompt=request.prompt,
            width=request.width or 1024,
            height=request.height or 1024,
            style=request.style,
            quality=request.quality or "standard",
            n=request.n or 1,
            provider=provider_name,
            api_key=request_api_key,
            extra_params=request.extra_params or {},
        )
        
        # 3. 如果prompt是自然语言，使用LLM提取参数（但保留前端传递的宽高和api_key）
        if not params.prompt or len(params.prompt.split()) < 3:
            # 保存前端传递的关键参数
            original_width = params.width
            original_height = params.height
            original_quality = params.quality
            original_n = params.n
            original_api_key = params.api_key  # 保存 api_key

            extractor = get_extractor(api_key=original_api_key)
            extracted_params = await extractor.extract(request.prompt)

            # 如果LLM提取没有指定宽高，使用前端传递的值
            if extracted_params.width == 1024 and extracted_params.height == 1024:
                # LLM使用默认值，恢复前端传递的值
                extracted_params.width = original_width
                extracted_params.height = original_height

            # 如果前端传递了其他参数且LLM提取中没有明确覆盖，保留前端值
            if original_quality != "standard" and extracted_params.quality == "standard":
                extracted_params.quality = original_quality
            if original_n != 1 and extracted_params.n == 1:
                extracted_params.n = original_n

            params = extracted_params
            # 确保使用已确定的 provider 和 api_key
            params.provider = provider_name
            params.api_key = original_api_key  # 恢复 api_key

        # 4. 使用Embedding匹配增强参数（保留 api_key）
        matcher = get_matcher(api_key=params.api_key)
        enhanced_params = await matcher.enhance_params(params, request.prompt)
        enhanced_params.api_key = params.api_key  # 确保 api_key 不丢失
        enhanced_params.provider = provider_name  # 确保 provider 正确
        params = enhanced_params
        
        # 5. 检查是否是异步模型
        model_registry = getattr(http_request.app.state, "model_registry", None)
        is_async_model = False
        if model_registry and request.model_name:
            model_info = model_registry.get_model_info(request.model_name)
            if model_info and model_info.tags:
                tags = [t.strip() for t in model_info.tags.split(",") if t.strip()]
                is_async_model = "异步" in tags

        # 如果是异步模型，提交到异步任务数据库
        if is_async_model:
            from ...database.async_task_manager import get_async_task_manager
            async_manager = get_async_task_manager()
            credential_id = None
            if params.api_key:
                credential = await db_manager.store_api_credential(
                    api_key=params.api_key,
                    provider="relay",
                    base_url=settings.relay_base_url,
                    user_id=request.user_id,
                )
                credential_id = credential.id

            task = await async_manager.create_task(
                platform=request.model_name.split("/")[0] if "/" in request.model_name else "relay",
                model=request.model_name,
                prompt=params.prompt,
                params={
                    "width": params.width,
                    "height": params.height,
                    "quality": params.quality,
                    "n": params.n,
                    "credential_id": credential_id,
                    "relay_base_url": settings.relay_base_url,
                },
                user_id=request.user_id  # 传递用户ID
            )

            # 返回异步任务信息
            return ImageTask(
                task_id=task.id,
                status="pending",
                prompt=params.prompt,
                params=params,
                is_async=True
            )

        # 6. 同步模型：保存用户请求到数据库
        user_request = await db_manager.create_user_request(
            user_id=request.user_id,
            user_ip=http_request.client.host,
            user_agent=http_request.headers.get("user-agent", ""),
            request_type="image_generation",
            status="processing",  # 标记为处理中
            request_data={
                "prompt": request.prompt,
                "width": params.width,
                "height": params.height,
                "style": params.style,
                "quality": params.quality,
                "n": params.n,
                "provider": params.provider,
                "model_name": request.model_name,
                "extra_params": request.extra_params or {}
            }
        )

        # 6. 创建并提交任务
        task = task_manager.create_task(params, request.prompt, user_request.id, request.user_id)
        await task_manager.submit_task(task)

        # 关联任务和用户请求
        task.user_request_id = user_request.id

        return task

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生图失败: {str(e)}")


@router.get("/generate/history", response_model=List[GenerationRecordResponse], summary="获取生成历史")
async def get_generation_history(
    limit: int = Query(20, ge=1, le=100, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status: Optional[str] = Query(None, description="状态筛选: completed, failed"),
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取当前用户的图片生成历史记录

    按时间倒序排列，最新的在前
    """
    db_manager = get_db_manager()

    records = await db_manager.get_user_generation_records(
        user_id=user["id"],
        limit=limit,
        offset=offset,
        status=status
    )

    return [GenerationRecordResponse(**record) for record in records]


@router.get("/generate/history/count", summary="获取生成历史总数")
async def get_generation_history_count(
    status: Optional[str] = Query(None, description="状态筛选: completed, failed"),
    user: dict = Depends(RequiredAuthDependency())
):
    """获取当前用户的图片生成记录总数"""
    db_manager = get_db_manager()

    count = await db_manager.get_user_generation_records_count(
        user_id=user["id"],
        status=status
    )

    return {"count": count}


@router.get("/generate/history/unified", response_model=List[UnifiedGenerationRecord], summary="获取统一生成历史")
async def get_unified_generation_history(
    limit: int = Query(20, ge=1, le=100, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status: Optional[str] = Query(None, description="状态筛选: completed, failed"),
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取统一生成历史，包含：
    - 对话生成（ImageGenerationRecord）
    - 异步任务（AsyncTask）

    按时间倒序排列，最新的在前
    """
    from ...database.async_task_manager import get_async_task_manager

    db_manager = get_db_manager()
    async_manager = get_async_task_manager()
    user_id = user["id"]

    # 1. 从两个数据源获取数据
    chat_records = await db_manager.get_user_generation_records(
        user_id=user_id,
        limit=limit * 2,  # 多取一些用于合并
        offset=0,
        status=status
    )

    async_records = await async_manager.get_user_tasks(
        user_id=user_id,
        status=status,
        limit=limit * 2
    )

    # 2. 标准化为统一格式
    unified = []

    for record in chat_records:
        unified.append({
            "id": record["id"],
            "type": "chat",
            "model": record["model"],
            "prompt": record["prompt"],
            "status": record["status"],
            "image_urls": record["image_urls"] or [],
            "timestamp": record["created_at"],
            "created_at": record["created_at"],
            "provider": record.get("provider")
        })

    for task in async_records:
        unified.append({
            "id": task.id,
            "type": "async",
            "model": task.model,
            "prompt": task.prompt,
            "status": task.status,
            "image_urls": task.result_urls or [],
            "timestamp": task.submit_time.isoformat(),
            "created_at": task.submit_time.isoformat(),
            "platform": task.platform
        })

    # 3. 按时间排序（最新的在前）
    unified.sort(key=lambda x: x["timestamp"], reverse=True)

    # 4. 应用分页
    return unified[offset:offset + limit]


@router.get("/generate/history/unified/count", summary="获取统一生成历史总数")
async def get_unified_generation_history_count(
    status: Optional[str] = Query(None, description="状态筛选: completed, failed"),
    user: dict = Depends(RequiredAuthDependency())
):
    """获取统一生成记录总数"""
    from ...database.async_task_manager import get_async_task_manager

    db_manager = get_db_manager()
    async_manager = get_async_task_manager()
    user_id = user["id"]

    chat_count = await db_manager.get_user_generation_records_count(
        user_id=user_id,
        status=status
    )

    async_count = await async_manager.get_user_tasks_count(
        user_id=user_id,
        status=status
    )

    return {"count": chat_count + async_count}

