"""账户计费API路由"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from ...services.account_service import get_account_service, AccountService, get_billing_config
from ...database import Transaction, ConsumptionRecord
from ..auth import RequiredAuthDependency, OptionalAuthDependency


router = APIRouter(prefix="/api/v1/account", tags=["账户"])


# ==================== 响应模型 ====================


class AccountInfoResponse(BaseModel):
    """账户信息响应"""
    user_id: str
    balance: int  # 余额（分）
    balance_yuan: float  # 余额（元）
    points: int  # 永久积分
    gift_points: int  # 临时积分（签到赠送）
    gift_points_expiry: Optional[str] = None  # 临时积分过期时间
    total_points: int  # 总可用积分
    subscription_plan: Optional[str] = None
    subscription_expires_at: Optional[str] = None
    total_generated: int  # 总生成次数
    total_spent: float  # 总消费（元）
    total_points_earned: int  # 历史累计获得积分


class TransactionResponse(BaseModel):
    """交易记录响应"""
    id: str
    transaction_type: str
    amount: int
    points_change: int
    balance_after: int
    points_after: int
    description: str
    status: str
    created_at: str


class ConsumptionRecordResponse(BaseModel):
    """消费记录响应"""
    id: str
    model_name: str
    provider: str
    cost_type: str
    points_used: int
    amount: int
    prompt: Optional[str] = None
    image_count: int
    image_urls: Optional[List[str]] = None
    status: str = "success"  # 新增: success, failed
    error_reason: Optional[str] = None  # 新增: 失败原因
    created_at: str


class ModelPriceResponse(BaseModel):
    """模型价格响应"""
    model_name: str
    display_name: str
    points: int
    amount: int  # 分
    amount_yuan: float  # 元
    description: str


class RechargeOptionResponse(BaseModel):
    """充值选项响应"""
    id: str
    name: str
    amount: int  # 分
    amount_yuan: float  # 元
    points: int
    bonus: int  # 赠送积分
    popular: bool


class SubscriptionPlanResponse(BaseModel):
    """订阅套餐响应"""
    id: str
    name: str
    icon: str
    badge: str
    monthly_price: int
    yearly_price: int
    points_per_month: int
    features: List[str]
    color: str


# ==================== 路由 ====================


@router.get("", response_model=AccountInfoResponse, summary="获取账户信息")
async def get_account_info(user: dict = Depends(RequiredAuthDependency())):
    """获取当前用户的账户信息"""
    account_service = get_account_service()
    account_info = await account_service.get_account_info(user["id"])

    if not account_info:
        raise HTTPException(status_code=404, detail="账户不存在")

    return AccountInfoResponse(**account_info)


@router.get("/transactions", response_model=List[TransactionResponse], summary="获取交易记录")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(RequiredAuthDependency())
):
    """获取当前用户的交易记录"""
    account_service = get_account_service()
    transactions = await account_service.get_transactions(user["id"], limit, offset)

    return [
        TransactionResponse(
            id=t.id,
            transaction_type=t.transaction_type,
            amount=t.amount,
            points_change=t.points_change,
            balance_after=t.balance_after,
            points_after=t.points_after,
            description=t.description or "",
            status=t.status,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )
        for t in transactions
    ]


@router.get("/consumption", response_model=List[ConsumptionRecordResponse], summary="获取消费记录")
async def get_consumption_records(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(RequiredAuthDependency())
):
    """获取当前用户的消费记录"""
    account_service = get_account_service()
    records = await account_service.get_consumption_records(user["id"], limit, offset)

    return [
        ConsumptionRecordResponse(
            id=r.id,
            model_name=r.model_name or "",
            provider=r.provider or "",
            cost_type=r.cost_type,
            points_used=r.points_used,
            amount=r.amount,
            prompt=r.prompt,
            image_count=r.image_count,
            image_urls=r.image_urls,
            status=r.status or "success",
            error_reason=r.error_reason,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]


@router.get("/models/pricing", response_model=List[ModelPriceResponse], summary="获取模型价格列表")
async def get_model_pricing(user: dict = Depends(OptionalAuthDependency())):
    """获取所有模型的计费价格"""
    config = get_billing_config()
    models = config.get("model_pricing", {}).get("models", {})

    result = []
    for model_key, model_config in models.items():
        if model_key == "default":
            continue
        result.append(
            ModelPriceResponse(
                model_name=model_key,
                display_name=model_config.get("name", model_key),
                points=model_config.get("points", 0),
                amount=model_config.get("amount", 0),
                amount_yuan=model_config.get("amount", 0) / 100,
                description=model_config.get("description", ""),
            )
        )

    return result


@router.get("/recharge/options", response_model=List[RechargeOptionResponse], summary="获取充值选项")
async def get_recharge_options(user: dict = Depends(OptionalAuthDependency())):
    """获取可用的充值选项"""
    config = get_billing_config()
    options = config.get("recharge_options", {}).get("options", [])

    return [
        RechargeOptionResponse(
            id=opt.get("id", ""),
            name=opt.get("name", ""),
            amount=opt.get("amount", 0),
            amount_yuan=opt.get("amount_yuan", 0),
            points=opt.get("points", 0),
            bonus=opt.get("bonus", 0),
            popular=opt.get("popular", False),
        )
        for opt in options
    ]


@router.get("/subscription/plans", response_model=List[SubscriptionPlanResponse], summary="获取订阅套餐")
async def get_subscription_plans(user: dict = Depends(OptionalAuthDependency())):
    """获取公开的订阅套餐列表"""
    config = get_billing_config()
    plans = config.get("subscription_plans", {}).get("plans", [])

    return [
        SubscriptionPlanResponse(
            id=plan.get("id", ""),
            name=plan.get("name", ""),
            icon=plan.get("icon", "workspace_premium"),
            badge=plan.get("badge", ""),
            monthly_price=plan.get("monthly_price", 0),
            yearly_price=plan.get("yearly_price", 0),
            points_per_month=plan.get("points_per_month", 0),
            features=plan.get("features", []) or [],
            color=plan.get("color", "red"),
        )
        for plan in plans
    ]


@router.get("/billing/config", summary="获取计费配置")
async def get_billing_config_info(user: dict = Depends(OptionalAuthDependency())):
    """获取计费配置信息（公开接口）"""
    config = get_billing_config()

    return {
        "billing": config.get("billing", {}),
        "initial_quota": config.get("initial_quota", {}),
        "recharge_options": config.get("recharge_options", {}),
        "subscription_plans": config.get("subscription_plans", {}),
        "limits": config.get("limits", {}),
    }
