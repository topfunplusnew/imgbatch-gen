"""系统配置API路由（仅管理员可访问）"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from loguru import logger

from ...database import get_db_manager, SystemConfig
from ..auth import RequiredAuthDependency
from ...services.auth_service import get_auth_service


router = APIRouter(prefix="/api/v1/admin/system-config", tags=["系统配置"])


# ==================== 请求模型 ====================


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    config_key: str = Field(..., description="配置键")
    config_value: str = Field(..., description="配置值（JSON字符串）")
    description: Optional[str] = Field(None, description="配置说明")


class BatchUpdateConfigRequest(BaseModel):
    """批量更新配置请求"""
    configs: Dict[str, str] = Field(..., description="配置键值对")


# ==================== 响应模型 ====================


class ConfigItemResponse(BaseModel):
    """配置项响应"""
    config_key: str
    config_value: str
    config_type: str
    category: str
    description: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== 辅助函数 ====================


async def verify_admin(user_id: str) -> bool:
    """验证用户是否为管理员"""
    auth_service = get_auth_service()
    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        return False

    return user.role == "admin"


# 预定义的配置项
PREDEFINED_CONFIGS = {
    # API 配置
    "relay.api_key": {
        "config_type": "string",
        "category": "api",
        "description": "中转站API Key",
        "is_encrypted": True,
        "is_public": False,
    },
    "relay.base_url": {
        "config_type": "string",
        "category": "api",
        "description": "中转站Base URL",
        "is_encrypted": False,
        "is_public": False,
    },
    "config.api_url": {
        "config_type": "string",
        "category": "api",
        "description": "模型配置接口URL",
        "is_encrypted": False,
        "is_public": False,
    },

    # 存储配置
    "storage.type": {
        "config_type": "string",
        "category": "storage",
        "description": "存储类型 (local/minio)",
        "is_encrypted": False,
        "is_public": False,
    },
    "minio.endpoint": {
        "config_type": "string",
        "category": "storage",
        "description": "MinIO服务地址",
        "is_encrypted": False,
        "is_public": False,
    },
    "minio.access_key": {
        "config_type": "string",
        "category": "storage",
        "description": "MinIO访问密钥",
        "is_encrypted": True,
        "is_public": False,
    },
    "minio.secret_key": {
        "config_type": "string",
        "category": "storage",
        "description": "MinIO密钥",
        "is_encrypted": True,
        "is_public": False,
    },
    "minio.bucket_name": {
        "config_type": "string",
        "category": "storage",
        "description": "MinIO存储桶名称",
        "is_encrypted": False,
        "is_public": False,
    },
}


# ==================== 路由 ====================


@router.get("/list", response_model=List[ConfigItemResponse], summary="获取所有配置项")
async def get_all_configs(user: dict = Depends(RequiredAuthDependency())):
    """
    获取所有系统配置项

    - 需要管理员权限
    - 返回所有配置项（包括敏感信息）
    """
    # 验证管理员权限
    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import select

            stmt = select(SystemConfig)
            result = await session.execute(stmt)
            configs = result.scalars().all()

            # 如果数据库中没有配置，初始化预定义配置
            if not configs:
                await _init_predefined_configs(db_manager, user["id"])
                # 重新查询
                result = await session.execute(stmt)
                configs = result.scalars().all()

            return [
                ConfigItemResponse(
                    config_key=c.config_key,
                    config_value=c.config_value or "",
                    config_type=c.config_type,
                    category=c.category,
                    description=c.description,
                    updated_at=c.updated_at.isoformat() if c.updated_at else None,
                )
                for c in configs
            ]
    except Exception as e:
        logger.error(f"获取配置列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置列表失败")


@router.get("/get/{config_key}", response_model=ConfigItemResponse, summary="获取单个配置项")
async def get_config(config_key: str, user: dict = Depends(RequiredAuthDependency())):
    """获取单个配置项的值"""
    # 验证管理员权限
    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import select

            stmt = select(SystemConfig).where(SystemConfig.config_key == config_key)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                # 如果配置不存在，使用预定义配置创建
                if config_key in PREDEFINED_CONFIGS:
                    predefined = PREDEFINED_CONFIGS[config_key]
                    config = SystemConfig(
                        config_key=config_key,
                        config_value="",
                        **predefined
                    )
                    session.add(config)
                    await session.commit()
                else:
                    raise HTTPException(status_code=404, detail="配置项不存在")

            return ConfigItemResponse(
                config_key=config.config_key,
                config_value=config.config_value or "",
                config_type=config.config_type,
                category=config.category,
                description=config.description,
                updated_at=config.updated_at.isoformat() if config.updated_at else None,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置项失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置项失败")


@router.post("/update", summary="更新配置项")
async def update_config(
    body: UpdateConfigRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    更新单个配置项

    - 需要管理员权限
    - 会记录更新者信息
    """
    # 验证管理员权限
    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import select

            stmt = select(SystemConfig).where(SystemConfig.config_key == body.config_key)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                # 如果配置不存在，创建新配置
                if body.config_key in PREDEFINED_CONFIGS:
                    predefined = PREDEFINED_CONFIGS[body.config_key]
                    config = SystemConfig(
                        config_key=body.config_key,
                        config_value=body.config_value,
                        description=body.description or predefined.get("description"),
                        updated_by=user["id"],
                        **{k: v for k, v in predefined.items() if k not in ["description"]}
                    )
                    session.add(config)
                else:
                    raise HTTPException(status_code=404, detail="配置项不存在")
            else:
                # 更新现有配置
                config.config_value = body.config_value
                if body.description:
                    config.description = body.description
                config.updated_by = user["id"]

            await session.commit()

            logger.info(f"配置更新: {body.config_key} by user {user['id']}")

            return {"success": True, "message": "配置更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.post("/batch-update", summary="批量更新配置")
async def batch_update_config(
    body: BatchUpdateConfigRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    批量更新多个配置项

    - 需要管理员权限
    - 会记录更新者信息
    """
    # 验证管理员权限
    if not await verify_admin(user["id"]):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import select

            for config_key, config_value in body.configs.items():
                stmt = select(SystemConfig).where(SystemConfig.config_key == config_key)
                result = await session.execute(stmt)
                config = result.scalar_one_or_none()

                if config:
                    # 更新现有配置
                    config.config_value = config_value
                    config.updated_by = user["id"]
                else:
                    # 创建新配置
                    if config_key in PREDEFINED_CONFIGS:
                        predefined = PREDEFINED_CONFIGS[config_key]
                        config = SystemConfig(
                            config_key=config_key,
                            config_value=config_value,
                            updated_by=user["id"],
                            **predefined
                        )
                        session.add(config)

            await session.commit()

            logger.info(f"批量更新配置: {len(body.configs)} 项 by user {user['id']}")

            return {"success": True, "message": f"成功更新 {len(body.configs)} 项配置"}
    except Exception as e:
        logger.error(f"批量更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量更新配置失败")


async def _init_predefined_configs(db_manager, user_id: str):
    """初始化预定义配置"""
    async with db_manager.get_session() as session:
        for config_key, config_data in PREDEFINED_CONFIGS.items():
            # 检查是否已存在
            from sqlalchemy import select
            stmt = select(SystemConfig).where(SystemConfig.config_key == config_key)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                config = SystemConfig(
                    config_key=config_key,
                    config_value="",
                    updated_by=user_id,
                    **config_data
                )
                session.add(config)

        await session.commit()
        logger.info("初始化系统配置完成")
