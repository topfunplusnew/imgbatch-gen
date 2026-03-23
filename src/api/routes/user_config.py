"""用户配置API路由"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
from sqlalchemy import select

from ...database import get_db_manager, StoredCredential
from ...config.settings import settings
from ...utils.credential_crypto import encrypt_api_key, decrypt_api_key, mask_api_key
from ..auth import get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["用户配置"])


# ==================== 请求模型 ====================


class SaveApiConfigRequest(BaseModel):
    """保存API配置请求"""
    api_key: str = Field(..., description="API Key")
    default_model: Optional[str] = Field(None, description="默认模型")


class ApiConfigResponse(BaseModel):
    """API配置响应"""
    api_key_hint: Optional[str] = Field(None, description="API Key脱敏提示")
    default_model: Optional[str] = Field(None, description="默认模型")
    has_api_key: bool = Field(False, description="是否已配置API Key")


# ==================== 路由 ====================


@router.get("/config", response_model=ApiConfigResponse, summary="获取用户API配置")
async def get_user_config(request: Request, user: dict = Depends(get_current_user)):
    """
    获取当前用户的API配置

    - 需要登录
    - 返回脱敏后的API Key提示和默认模型
    """
    user_id = user["id"]
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            # 查找用户存储的凭据
            stmt = select(StoredCredential).where(
                StoredCredential.user_id == user_id,
                StoredCredential.provider == "relay",
                StoredCredential.status == "active"
            ).order_by(StoredCredential.created_at.desc()).limit(1)

            result = await session.execute(stmt)
            credential = result.scalar_one_or_none()

            if credential:
                return ApiConfigResponse(
                    api_key_hint=credential.key_hint,
                    default_model=credential.base_url,  # 复用 base_url 字段存储 default_model
                    has_api_key=True
                )
            else:
                return ApiConfigResponse(
                    api_key_hint=None,
                    default_model=None,
                    has_api_key=False
                )
    except Exception as e:
        logger.error(f"获取用户配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config", summary="保存用户API配置")
async def save_user_config(
    body: SaveApiConfigRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    保存用户的API配置

    - 需要登录
    - API Key 会被加密存储
    - 默认模型存储在 base_url 字段中（复用现有字段）
    """
    user_id = user["id"]
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            # 查找是否已存在配置
            stmt = select(StoredCredential).where(
                StoredCredential.user_id == user_id,
                StoredCredential.provider == "relay"
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            from datetime import datetime

            if existing:
                # 更新现有配置
                existing.encrypted_api_key = encrypt_api_key(body.api_key)
                existing.key_hint = mask_api_key(body.api_key)
                existing.base_url = body.default_model or ""  # 复用此字段存储默认模型
                existing.status = "active"
                existing.last_used_at = datetime.utcnow()
                logger.info(f"更新用户API配置: user_id={user_id}, key_hint={existing.key_hint}")
            else:
                # 创建新配置
                credential = StoredCredential(
                    provider="relay",
                    base_url=body.default_model or "",  # 复用此字段存储默认模型
                    user_id=user_id,
                    session_id=None,
                    encrypted_api_key=encrypt_api_key(body.api_key),
                    key_hint=mask_api_key(body.api_key),
                    status="active",
                    expires_at=None,  # 用户配置不过期
                    last_used_at=datetime.utcnow(),
                )
                session.add(credential)
                logger.info(f"创建用户API配置: user_id={user_id}, key_hint={credential.key_hint}")

            await session.commit()

            return {
                "success": True,
                "message": "配置保存成功",
                "api_key_hint": mask_api_key(body.api_key)
            }
    except Exception as e:
        logger.error(f"保存用户配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="保存配置失败")


@router.delete("/config", summary="删除用户API配置")
async def delete_user_config(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    删除用户的API配置

    - 需要登录
    """
    user_id = user["id"]
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            stmt = select(StoredCredential).where(
                StoredCredential.user_id == user_id,
                StoredCredential.provider == "relay"
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = "revoked"
                await session.commit()
                logger.info(f"删除用户API配置: user_id={user_id}")

            return {"success": True, "message": "配置已删除"}
    except Exception as e:
        logger.error(f"删除用户配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除配置失败")
