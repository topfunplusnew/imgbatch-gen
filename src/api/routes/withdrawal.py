"""用户提现API路由"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from ...services.withdrawal_service import get_withdrawal_service
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/withdrawal", tags=["提现"])


# ==================== 请求模型 ====================


class CreateWithdrawalRequest(BaseModel):
    """创建提现申请请求"""
    amount: int = Field(..., gt=0, description="提现金额（分）")
    withdrawal_method: str = Field(..., pattern=r'^(wechat|alipay|bank)$', description="提现方式")
    withdrawal_account: str = Field(..., min_length=1, max_length=200, description="提现账号")
    withdrawal_name: str = Field(..., min_length=1, max_length=100, description="收款人姓名")
    user_note: Optional[str] = Field(None, max_length=500, description="用户备注")


class WithdrawalResponse(BaseModel):
    """提现记录响应"""
    id: str
    withdrawal_id: str
    amount: int
    amount_yuan: float
    withdrawal_method: str
    withdrawal_account: str
    withdrawal_name: str
    status: str
    user_note: Optional[str] = None
    review_note: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    completed_at: Optional[str] = None


# ==================== 路由 ====================


@router.post("/create", response_model=dict, summary="申请提现")
async def create_withdrawal(
    body: CreateWithdrawalRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    创建提现申请

    提现流程：
    1. 用户申请：创建提现记录，状态为 pending
    2. 管理员审核通过：扣除余额，状态变为 approved
    3. 管理员审核拒绝：余额不变，状态变为 rejected
    4. 管理员线下打款：标记为 completed

    注意：线下打款模式，无手续费
    """
    withdrawal_service = get_withdrawal_service()

    try:
        result = await withdrawal_service.create_withdrawal(
            user_id=user["id"],
            amount=body.amount,
            method=body.withdrawal_method,
            account=body.withdrawal_account,
            name=body.withdrawal_name,
            note=body.user_note
        )

        return {
            "success": True,
            "message": "提现申请已提交，等待审核",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建提现申请失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建提现申请失败，请稍后重试")


@router.get("/my-withdrawals", response_model=list[WithdrawalResponse], summary="我的提现记录")
async def get_my_withdrawals(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取当前用户的提现记录

    按创建时间倒序排列
    """
    withdrawal_service = get_withdrawal_service()

    try:
        withdrawals = await withdrawal_service.get_user_withdrawals(
            user_id=user["id"],
            limit=limit,
            offset=offset
        )

        return withdrawals

    except Exception as e:
        logger.error(f"获取提现记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取提现记录失败")


@router.get("/my-withdrawals/count", summary="我的提现记录总数")
async def get_my_withdrawals_count(
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取当前用户的提现记录总数
    """
    from ...database import get_db_manager
    db_manager = get_db_manager()

    try:
        count = await db_manager.get_withdrawals_count()

        return {"count": count}

    except Exception as e:
        logger.error(f"获取提现记录总数失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取提现记录总数失败")


@router.post("/cancel/{withdrawal_id}", summary="取消提现申请")
async def cancel_withdrawal(
    withdrawal_id: str,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    取消待审核的提现申请

    只有 pending 状态的提现申请才能取消
    """
    withdrawal_service = get_withdrawal_service()

    try:
        result = await withdrawal_service.cancel_withdrawal(
            withdrawal_id=withdrawal_id,
            user_id=user["id"]
        )

        return {
            "success": True,
            "message": "提现申请已取消",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消提现申请失败: {str(e)}")
        raise HTTPException(status_code=500, detail="取消提现申请失败")
