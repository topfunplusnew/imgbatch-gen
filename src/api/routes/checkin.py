"""签到API路由"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from ...services.checkin_service import get_checkin_service
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/checkin", tags=["签到"])


# ==================== 响应模型 ====================


class CheckinResponse(BaseModel):
    """签到响应"""
    success: bool
    reward_points: int
    consecutive_days: int
    gift_points: int
    gift_points_expiry: Optional[str] = None


class CheckinStatusResponse(BaseModel):
    """签到状态响应"""
    can_checkin: bool
    consecutive_days: int
    gift_points: int
    gift_points_expiry: Optional[str] = None
    last_checkin_date: Optional[str] = None


# ==================== 路由 ====================


@router.post("/daily", response_model=CheckinResponse, summary="每日签到")
async def daily_checkin(user: dict = Depends(RequiredAuthDependency())):
    """
    每日签到

    - 奖励40积分（赠送积分，今日23:59:59过期）
    - 统计连续签到天数
    - 每天只能签到一次
    """
    checkin_service = get_checkin_service()

    try:
        result = await checkin_service.daily_checkin(user["id"])
        logger.info(f"签到结果: {result}")
        return CheckinResponse(**result)
    except ValueError as e:
        logger.warning(f"签到失败(ValueError): {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"签到失败(Exception): {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="签到失败，请稍后重试")


@router.get("/status", response_model=CheckinStatusResponse, summary="获取签到状态")
async def get_checkin_status(user: dict = Depends(RequiredAuthDependency())):
    """
    获取签到状态

    - 是否可以签到
    - 连续签到天数
    - 当前赠送积分余额
    - 赠送积分过期时间
    - 最后签到日期
    """
    checkin_service = get_checkin_service()

    result = await checkin_service.get_checkin_status(user["id"])
    return CheckinStatusResponse(**result)
