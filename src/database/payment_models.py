"""支付订单相关数据库模型"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseModel


class PaymentOrder(BaseModel):
    """支付订单表"""
    __tablename__ = "payment_orders"

    # 订单基本信息
    order_id = Column(String(100), unique=True, nullable=False, comment="订单号")
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 订单类型和金额
    order_type = Column(String(20), nullable=False, comment="订单类型: recharge, subscription")
    amount = Column(Integer, nullable=False, comment="订单金额(分)")

    # 关联信息
    plan_id = Column(String(50), nullable=True, comment="关联的套餐ID")

    # 支付方式
    payment_method = Column(String(20), nullable=False, comment="支付方式: wechat, alipay")
    payment_channel = Column(String(50), nullable=True, comment="支付渠道: native, h5, jsapi")

    # 订单状态
    status = Column(String(20), default="pending", comment="状态: pending, paid, failed, cancelled, refunded, timeout")

    # 第三方支付信息
    transaction_id = Column(String(100), nullable=True, comment="第三方交易ID")
    prepay_id = Column(String(100), nullable=True, comment="预支付ID")
    qr_code_url = Column(Text, nullable=True, comment="支付二维码URL")
    pay_url = Column(Text, nullable=True, comment="支付跳转URL(H5支付用)")

    # 回调信息
    notify_time = Column(DateTime, nullable=True, comment="支付回调时间")
    notify_data = Column(JSON, nullable=True, comment="回调原始数据")

    # 过期时间
    expire_time = Column(DateTime, nullable=True, comment="订单过期时间")
    paid_at = Column(DateTime, nullable=True, comment="支付完成时间")

    # 备注
    subject = Column(String(255), comment="订单标题")
    body = Column(Text, comment="订单描述")
    attach = Column(JSON, nullable=True, comment="附加数据(JSON)")

    # 客户端信息
    client_ip = Column(String(50), comment="客户端IP")
    user_agent = Column(String(500), comment="用户代理")

    def __repr__(self):
        return f"<PaymentOrder(id={self.id}, order_id={self.order_id}, user_id={self.user_id}, status={self.status})>"


class PaymentRefund(BaseModel):
    """退款记录表"""
    __tablename__ = "payment_refunds"

    # 关联支付订单
    payment_order_id = Column(String(100), ForeignKey("payment_orders.order_id"), nullable=False, comment="原支付订单ID")
    payment_order = relationship("PaymentOrder", foreign_keys=[payment_order_id])

    # 退款基本信息
    refund_id = Column(String(100), unique=True, nullable=False, comment="退款单号")
    refund_amount = Column(Integer, nullable=False, comment="退款金额(分)")
    refund_reason = Column(String(255), comment="退款原因")

    # 状态
    status = Column(String(20), default="pending", comment="状态: pending, success, failed, cancelled")

    # 第三方退款信息
    refund_transaction_id = Column(String(100), nullable=True, comment="第三方退款交易ID")

    # 时间
    refund_time = Column(DateTime, nullable=True, comment="退款完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<PaymentRefund(id={self.id}, refund_id={self.refund_id}, amount={self.refund_amount}, status={self.status})>"
