"""支付API路由"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger

from ...services.payment_service import (
    get_payment_service,
    get_wechat_pay_service,
    get_alipay_service,
)
from ...database import PaymentOrder
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/payment", tags=["支付"])


# ==================== 请求模型 ====================


class CreateOrderRequest(BaseModel):
    """创建支付订单请求"""
    order_type: str = Field(..., pattern=r'^(recharge|subscription)$', description="订单类型")
    amount: int = Field(..., gt=0, description="金额（分）")
    payment_method: str = Field(..., pattern=r'^(wechat|alipay)$', description="支付方式")
    plan_id: Optional[str] = Field(None, description="套餐ID")
    subject: str = Field(..., description="订单标题")
    body: str = Field("", description="订单描述")


class CreateRechargeOrderRequest(BaseModel):
    """创建充值订单请求（简化版）"""
    recharge_option_id: str = Field(..., description="充值选项ID")
    payment_method: str = Field(..., pattern=r'^(wechat|alipay)$', description="支付方式")


# ==================== 响应模型 ====================


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: str
    user_id: str
    order_type: str
    amount: int
    amount_yuan: float
    payment_method: str
    status: str
    subject: str
    created_at: str
    expire_time: Optional[str] = None
    qr_code_url: Optional[str] = None
    pay_url: Optional[str] = None


class OrderListResponse(BaseModel):
    """订单列表响应"""
    order_id: str
    order_type: str
    amount: int
    amount_yuan: float
    payment_method: str
    status: str
    subject: str
    created_at: str
    paid_at: Optional[str] = None


# ==================== 路由 ====================


@router.post("/create", response_model=OrderResponse, summary="创建支付订单")
async def create_payment_order(
    request: Request,
    body: CreateRechargeOrderRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    创建支付订单（充值）

    根据充值选项ID创建订单，返回支付二维码URL
    """
    payment_service = get_payment_service()

    # 获取充值配置
    import json
    from pathlib import Path
    config_path = Path(__file__).parent.parent.parent / "config" / "billing_config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    recharge_options = config.get("recharge_options", {}).get("options", [])
    selected_option = None
    for opt in recharge_options:
        if opt.get("id") == body.recharge_option_id:
            selected_option = opt
            break

    if not selected_option:
        raise HTTPException(status_code=400, detail="无效的充值选项")

    # 创建订单
    order = await payment_service.create_order(
        user_id=user["id"],
        order_type="recharge",
        amount=selected_option["amount"],
        payment_method=body.payment_method,
        subject=selected_option["name"],
        body=f"充值 {selected_option['amount_yuan']} 元，获得 {selected_option['points']} 积分",
    )

    # 调用支付接口
    qr_code_url = None
    pay_url = None

    if body.payment_method == "wechat":
        wechat_service = get_wechat_pay_service()
        result = await wechat_service.create_native_pay(
            order_id=order.order_id,
            amount=order.amount,
            subject=order.subject,
        )
        qr_code_url = result.get("code_url")
        order.prepay_id = result.get("prepay_id")
        order.qr_code_url = qr_code_url

    elif body.payment_method == "alipay":
        alipay_service = get_alipay_service()
        result = await alipay_service.create_trade_precreate(
            order_id=order.order_id,
            amount=order.amount,
            subject=order.subject,
        )
        qr_code_url = result.get("qr_code_url")
        order.qr_code_url = qr_code_url

    # 更新订单
    async with payment_service.db_manager.get_session() as session:
        from sqlalchemy import select
        from ...database import PaymentOrder
        stmt = select(PaymentOrder).where(PaymentOrder.order_id == order.order_id)
        result = await session.execute(stmt)
        db_order = result.scalar_one_or_none()
        if db_order:
            db_order.qr_code_url = qr_code_url
            await session.commit()

    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        order_type=order.order_type,
        amount=order.amount,
        amount_yuan=order.amount / 100,
        payment_method=order.payment_method,
        status=order.status,
        subject=order.subject,
        created_at=order.created_at.isoformat() if order.created_at else "",
        expire_time=order.expire_time.isoformat() if order.expire_time else None,
        qr_code_url=qr_code_url,
        pay_url=pay_url,
    )


@router.get("/qrcode/{order_id}", summary="获取支付二维码")
async def get_payment_qrcode(
    order_id: str,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    获取支付二维码URL

    如果订单已过期或不存在，返回错误
    """
    payment_service = get_payment_service()

    # 检查订单是否过期
    is_expired = await payment_service.check_order_expire(order_id)
    if is_expired:
        raise HTTPException(status_code=400, detail="订单已过期")

    order = await payment_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单所属用户
    if order.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    return {
        "order_id": order.order_id,
        "qr_code_url": order.qr_code_url,
        "pay_url": order.pay_url,
        "amount": order.amount,
        "amount_yuan": order.amount / 100,
        "status": order.status,
        "expire_time": order.expire_time.isoformat() if order.expire_time else None,
    }


@router.get("/status/{order_id}", summary="查询订单状态")
async def get_order_status(
    order_id: str,
    user: dict = Depends(RequiredAuthDependency())
):
    """查询订单支付状态"""
    payment_service = get_payment_service()

    # 检查订单是否过期
    await payment_service.check_order_expire(order_id)

    order = await payment_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单所属用户
    if order.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    return {
        "order_id": order.order_id,
        "status": order.status,
        "amount": order.amount,
        "amount_yuan": order.amount / 100,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


@router.get("/orders", response_model=List[OrderListResponse], summary="获取订单列表")
async def get_orders(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(RequiredAuthDependency())
):
    """获取当前用户的订单列表"""
    payment_service = get_payment_service()
    orders = await payment_service.get_user_orders(user["id"], limit, offset)

    return [
        OrderListResponse(
            order_id=o.order_id,
            order_type=o.order_type,
            amount=o.amount,
            amount_yuan=o.amount / 100,
            payment_method=o.payment_method,
            status=o.status,
            subject=o.subject or "",
            created_at=o.created_at.isoformat() if o.created_at else "",
            paid_at=o.paid_at.isoformat() if o.paid_at else None,
        )
        for o in orders
    ]


@router.post("/cancel/{order_id}", summary="取消订单")
async def cancel_order(
    order_id: str,
    user: dict = Depends(RequiredAuthDependency())
):
    """取消未支付的订单"""
    payment_service = get_payment_service()

    order = await payment_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单所属用户
    if order.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="只能取消待支付订单")

    await payment_service.cancel_order(order_id)

    return {"success": True, "message": "订单已取消"}


# ==================== 支付回调接口 ====================


@router.post("/callback/wechat", summary="微信支付回调")
async def wechat_pay_callback(request: Request):
    """
    微信支付回调通知

    注意：此接口不需要认证，由微信服务器调用
    """
    import xml.etree.ElementTree as ET

    # 获取回调数据
    body = await request.body()
    data = ET.fromstring(body)

    # 提取字段
    order_id = data.find("out_trade_no").text
    transaction_id = data.find("transaction_id").text
    return_code = data.find("return_code").text
    result_code = data.find("result_code").text

    logger.info(f"微信支付回调: order={order_id}, transaction={transaction_id}")

    # 验证签名
    wechat_service = get_wechat_pay_service()
    # TODO: 验证签名

    # 处理支付结果
    if return_code == "SUCCESS" and result_code == "SUCCESS":
        payment_service = get_payment_service()
        await payment_service.handle_payment_success(
            order_id=order_id,
            transaction_id=transaction_id,
            notify_data=ET.tostring(data),
        )

    # 返回微信要求的格式
    return Response(
        content="<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>",
        media_type="application/xml",
    )


@router.post("/callback/alipay", summary="支付宝回调")
async def alipay_pay_callback(request: Request):
    """
    支付宝回调通知

    注意：此接口不需要认证，由支付宝服务器调用
    """
    form_data = await request.form()

    order_id = form_data.get("out_trade_no")
    trade_no = form_data.get("trade_no")
    trade_status = form_data.get("trade_status")

    logger.info(f"支付宝回调: order={order_id}, trade={trade_no}, status={trade_status}")

    # 验证签名
    alipay_service = get_alipay_service()
    # TODO: 验证签名

    # 处理支付结果
    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        payment_service = get_payment_service()
        await payment_service.handle_payment_success(
            order_id=order_id,
            transaction_id=trade_no,
            notify_data=dict(form_data),
        )

    return "success"


# 导入Response用于微信回调
from fastapi.responses import Response
