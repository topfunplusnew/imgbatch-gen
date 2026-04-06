"""System configuration endpoints for admin-only settings."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select

from ...database import SystemConfig, get_db_manager
from ...utils.credential_crypto import encrypt_api_key
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/admin/system-config", tags=["system-config"])

MASKED_VALUE = "••••••••"

PREDEFINED_CONFIGS = {
    "relay.api_key": {
        "config_type": "string",
        "category": "api",
        "description": "中转站API Key",
        "is_encrypted": True,
        "is_public": False,
    },
}


class UpdateConfigRequest(BaseModel):
    """Request body for updating a single system config."""

    config_key: str = Field(..., description="Config key")
    config_value: str = Field(..., description="Config value")
    description: Optional[str] = Field(None, description="Config description")


class BatchUpdateConfigRequest(BaseModel):
    """Request body for updating multiple system configs."""

    configs: Dict[str, str] = Field(..., description="Config map")


class ConfigItemResponse(BaseModel):
    """System config item returned to the frontend."""

    config_key: str
    config_value: str
    config_type: str
    category: str
    description: Optional[str] = None
    updated_at: Optional[str] = None


async def verify_admin(user_id: str) -> bool:
    """Return whether the current user is an admin."""

    db_manager = get_db_manager()
    user = await db_manager.get_user_by_id(user_id)
    return bool(user and user.role == "admin")


async def _ensure_predefined_configs(user_id: str) -> None:
    """Create missing supported configs without touching obsolete rows."""

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        for config_key, config_data in PREDEFINED_CONFIGS.items():
            existing = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            if existing:
                continue

            session.add(
                SystemConfig(
                    config_key=config_key,
                    config_value="",
                    updated_by=user_id,
                    **config_data,
                )
            )

        await session.commit()


def _serialize_config(config: SystemConfig) -> ConfigItemResponse:
    """Hide encrypted values while keeping presence visible to the UI."""

    predefined = PREDEFINED_CONFIGS.get(config.config_key, {})
    config_value = config.config_value or ""
    if predefined.get("is_encrypted") and config_value:
        config_value = MASKED_VALUE

    return ConfigItemResponse(
        config_key=config.config_key,
        config_value=config_value,
        config_type=config.config_type,
        category=config.category,
        description=config.description,
        updated_at=config.updated_at.isoformat() if config.updated_at else None,
    )


@router.get("/list", response_model=List[ConfigItemResponse], summary="List supported system configs")
async def get_all_configs(user: dict = Depends(RequiredAuthDependency())):
    """Return only currently supported system configs."""

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")

    await _ensure_predefined_configs(user["id"])
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.config_key.in_(list(PREDEFINED_CONFIGS.keys())))
            )
            configs = result.scalars().all()
            return [_serialize_config(config) for config in configs]
    except Exception as exc:
        logger.error(f"Failed to load system configs: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load system configs.")


@router.get("/get/{config_key}", response_model=ConfigItemResponse, summary="Get a single system config")
async def get_config(config_key: str, user: dict = Depends(RequiredAuthDependency())):
    """Return one supported system config."""

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")
    if config_key not in PREDEFINED_CONFIGS:
        raise HTTPException(status_code=404, detail="Config key is not supported.")

    await _ensure_predefined_configs(user["id"])
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == config_key)
            )
            if not config:
                raise HTTPException(status_code=404, detail="Config key is not supported.")
            return _serialize_config(config)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to load system config {config_key}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load system config.")


@router.post("/update", summary="Update a single system config")
async def update_config(
    body: UpdateConfigRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """Update one supported system config."""

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")
    if body.config_key not in PREDEFINED_CONFIGS:
        raise HTTPException(status_code=404, detail="Config key is not supported.")

    db_manager = get_db_manager()
    predefined = PREDEFINED_CONFIGS[body.config_key]
    config_value = body.config_value
    if predefined.get("is_encrypted") and config_value:
        config_value = encrypt_api_key(config_value)

    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == body.config_key)
            )
            if not config:
                config = SystemConfig(
                    config_key=body.config_key,
                    config_value=config_value,
                    description=body.description or predefined.get("description"),
                    updated_by=user["id"],
                    **predefined,
                )
                session.add(config)
            else:
                config.config_value = config_value
                config.updated_by = user["id"]
                if body.description:
                    config.description = body.description

            await session.commit()

        return {"success": True, "message": "Config updated successfully."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to update config {body.config_key}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to update config.")


@router.post("/batch-update", summary="Batch update system configs")
async def batch_update_config(
    body: BatchUpdateConfigRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """Update multiple supported system configs in one request."""

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")

    unsupported_keys = [key for key in body.configs if key not in PREDEFINED_CONFIGS]
    if unsupported_keys:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported config keys: {', '.join(sorted(unsupported_keys))}",
        )

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            for config_key, config_value in body.configs.items():
                predefined = PREDEFINED_CONFIGS[config_key]
                final_value = config_value
                if predefined.get("is_encrypted") and final_value:
                    final_value = encrypt_api_key(final_value)

                config = await session.scalar(
                    select(SystemConfig).where(SystemConfig.config_key == config_key)
                )
                if not config:
                    session.add(
                        SystemConfig(
                            config_key=config_key,
                            config_value=final_value,
                            updated_by=user["id"],
                            **predefined,
                        )
                    )
                    continue

                config.config_value = final_value
                config.updated_by = user["id"]

            await session.commit()

        return {"success": True, "message": f"Updated {len(body.configs)} config(s)."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to batch update configs: {exc}")
        raise HTTPException(status_code=500, detail="Failed to batch update configs.")


# ==================== 场景库数据接口 ====================

SCENES_CONFIG_KEY = "scenes.data"


@router.get("/scenes", summary="获取场景库数据（公开）")
async def get_scenes_data():
    """公开接口，所有用户可读取场景库数据。不需要登录。"""
    import json
    from pathlib import Path

    db_manager = get_db_manager()
    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == SCENES_CONFIG_KEY)
            )
            if config and config.config_value:
                return json.loads(config.config_value)
    except Exception as exc:
        logger.warning(f"Failed to load scenes from DB, falling back to JSON file: {exc}")

    # Fallback: load from static JSON file
    json_path = Path(__file__).parent.parent.parent.parent / "web" / "public" / "data" / "scenes.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"categories": [], "scenes": []}


class UpdateScenesRequest(BaseModel):
    """Request body for updating scenes data."""
    categories: list = Field(default_factory=list, description="场景分类列表")
    scenes: list = Field(default_factory=list, description="场景列表")


@router.post("/scenes", summary="更新场景库数据（管理员）")
async def update_scenes_data(
    body: UpdateScenesRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """管理员接口，更新场景库数据。"""
    import json

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")

    db_manager = get_db_manager()
    scenes_json = json.dumps({"categories": body.categories, "scenes": body.scenes}, ensure_ascii=False)

    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == SCENES_CONFIG_KEY)
            )
            if config:
                config.config_value = scenes_json
                config.updated_by = user["id"]
            else:
                session.add(SystemConfig(
                    config_key=SCENES_CONFIG_KEY,
                    config_value=scenes_json,
                    config_type="json",
                    category="content",
                    description="场景库数据",
                    updated_by=user["id"],
                ))
            await session.commit()

        return {"success": True, "message": f"场景库已更新，共 {len(body.scenes)} 个场景"}
    except Exception as exc:
        logger.error(f"Failed to update scenes data: {exc}")
        raise HTTPException(status_code=500, detail="更新场景库失败")


# ==================== 类型与风格配置接口 ====================

TYPES_STYLES_CONFIG_KEY = "home.types_styles"

# 默认数据
_DEFAULT_TYPES = [
    {"value": "poster", "label": "海报设计", "emoji": "🎨", "cover": "/covers/types/poster.webp"},
    {"value": "reading_notes", "label": "读书笔记", "emoji": "📖", "cover": "/covers/types/reading_notes.webp"},
    {"value": "mind_map", "label": "思维导图", "emoji": "🧠", "cover": "/covers/types/mind_map.webp"},
    {"value": "infographic", "label": "信息图表", "emoji": "📊", "cover": "/covers/types/infographic.webp"},
    {"value": "flow_guide", "label": "流程指南", "emoji": "📋", "cover": "/covers/types/flow_guide.webp"},
    {"value": "comic", "label": "漫画故事", "emoji": "💬", "cover": "/covers/types/comic.webp"},
    {"value": "timeline", "label": "时间线", "emoji": "⏳", "cover": "/covers/types/timeline.webp"},
    {"value": "comparison", "label": "对比分析", "emoji": "⚖️", "cover": "/covers/types/comparison.webp"},
    {"value": "tutorial", "label": "教程指南", "emoji": "📐", "cover": "/covers/types/tutorial.webp"},
    {"value": "concept_map", "label": "概念地图", "emoji": "🗺️", "cover": "/covers/types/concept_map.webp"},
    {"value": "visual_summary", "label": "视觉总结", "emoji": "📝", "cover": "/covers/types/visual_summary.webp"},
    {"value": "poetry", "label": "诗词解读", "emoji": "🌙", "cover": "/covers/types/poetry.webp"},
    {"value": "formula", "label": "公式原理", "emoji": "🔬", "cover": "/covers/types/formula.webp"},
]

_DEFAULT_STYLES = ["手绘", "水彩", "扁平", "卡通", "写实", "复古", "动漫", "3D", "极简", "水墨", "素描", "像素"]


@router.get("/types-styles", summary="获取类型与风格配置（公开）")
async def get_types_styles():
    """公开接口，获取首页类型和风格选项。"""
    import json

    db_manager = get_db_manager()
    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == TYPES_STYLES_CONFIG_KEY)
            )
            if config and config.config_value:
                return json.loads(config.config_value)
    except Exception as exc:
        logger.warning(f"Failed to load types/styles from DB: {exc}")

    return {"types": _DEFAULT_TYPES, "styles": _DEFAULT_STYLES}


class UpdateTypesStylesRequest(BaseModel):
    types: list = Field(default_factory=list, description="类型列表")
    styles: list = Field(default_factory=list, description="风格列表")


@router.post("/types-styles", summary="更新类型与风格配置（管理员）")
async def update_types_styles(
    body: UpdateTypesStylesRequest,
    user: dict = Depends(RequiredAuthDependency()),
):
    """管理员接口，更新首页类型和风格选项。"""
    import json

    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="Admin access required.")

    db_manager = get_db_manager()
    data_json = json.dumps({"types": body.types, "styles": body.styles}, ensure_ascii=False)

    try:
        async with db_manager.get_session() as session:
            config = await session.scalar(
                select(SystemConfig).where(SystemConfig.config_key == TYPES_STYLES_CONFIG_KEY)
            )
            if config:
                config.config_value = data_json
                config.updated_by = user["id"]
            else:
                session.add(SystemConfig(
                    config_key=TYPES_STYLES_CONFIG_KEY,
                    config_value=data_json,
                    config_type="json",
                    category="content",
                    description="首页类型与风格配置",
                    updated_by=user["id"],
                ))
            await session.commit()

        return {"success": True, "message": f"已更新 {len(body.types)} 个类型和 {len(body.styles)} 个风格"}
    except Exception as exc:
        logger.error(f"Failed to update types/styles: {exc}")
        raise HTTPException(status_code=500, detail="更新失败")
