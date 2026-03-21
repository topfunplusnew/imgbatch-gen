"""邀请码API路由"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

from ...services.referral_service import get_referral_service
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/referral", tags=["邀请码"])


# ==================== 请求模型 ====================


class ApplyInviteCodeRequest(BaseModel):
    """使用邀请码请求"""
    invite_code: str = Field(..., min_length=8, max_length=8, description="邀请码")


# ==================== 响应模型 ====================


class InviteCodeResponse(BaseModel):
    """邀请码响应"""
    invite_code: str
    total_invite_count: int
    total_reward_points: int


class InviteRecordResponse(BaseModel):
    """邀请记录响应"""
    user_id: str
    username: str
    phone: Optional[str] = None
    created_at: str


# ==================== 路由 ====================


@router.get("/my-code", response_model=InviteCodeResponse, summary="获取我的邀请码")
async def get_my_invite_code(user: dict = Depends(RequiredAuthDependency())):
    """
    获取我的邀请码

    - 如果没有邀请码，会自动生成一个
    - 返回邀请统计信息
    """
    referral_service = get_referral_service()

    try:
        code = await referral_service.get_my_invite_code(user["id"])
        stats = await referral_service.get_invite_stats(user["id"])

        return InviteCodeResponse(
            invite_code=code,
            total_invite_count=stats["total_invite_count"],
            total_reward_points=stats["total_reward_points"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取邀请码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取邀请码失败，请稍后重试")


@router.post("/apply", summary="使用邀请码")
async def apply_invite_code(
    body: ApplyInviteCodeRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    使用邀请码

    - 只能在注册时使用一次
    - 邀请人将获得50积分奖励
    """
    referral_service = get_referral_service()

    try:
        result = await referral_service.apply_invite_code(user["id"], body.invite_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"使用邀请码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="使用邀请码失败，请稍后重试")


@router.get("/records", response_model=List[InviteRecordResponse], summary="获取邀请记录")
async def get_invite_records(user: dict = Depends(RequiredAuthDependency())):
    """
    获取邀请记录

    返回所有使用我邀请码注册的用户列表
    """
    referral_service = get_referral_service()

    try:
        records = await referral_service.get_invite_records(user["id"])
        return [InviteRecordResponse(**r) for r in records]
    except Exception as e:
        logger.error(f"获取邀请记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取邀请记录失败，请稍后重试")


@router.get("/stats", response_model=InviteCodeResponse, summary="获取邀请统计")
async def get_invite_stats(user: dict = Depends(RequiredAuthDependency())):
    """
    获取邀请统计

    返回邀请人数和累计奖励积分
    """
    referral_service = get_referral_service()

    try:
        stats = await referral_service.get_invite_stats(user["id"])

        # 如果没有邀请码，生成一个
        invite_code = stats["invite_code"]
        if not invite_code:
            invite_code = await referral_service.get_my_invite_code(user["id"])

        return InviteCodeResponse(
            invite_code=invite_code,
            total_invite_count=stats["total_invite_count"],
            total_reward_points=stats["total_reward_points"],
        )
    except Exception as e:
        logger.error(f"获取邀请统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取邀请统计失败，请稍后重试")
