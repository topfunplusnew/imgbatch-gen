"""账户计费相关数据库模型"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseModel


class Account(BaseModel):
    """用户账户表"""
    __tablename__ = "accounts"

    # 关联用户
    user_id = Column(String(100), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    user = relationship("User", back_populates="account", foreign_keys=[user_id])

    # 余额和积分
    balance = Column(Integer, default=0, comment="余额(分)")
    points = Column(Integer, default=0, comment="积分")

    # 订阅信息
    subscription_plan = Column(String(50), nullable=True, comment="订阅套餐ID")
    subscription_expires_at = Column(DateTime, nullable=True, comment="订阅到期时间")

    # 统计信息
    total_generated = Column(Integer, default=0, comment="总生成次数")
    total_spent = Column(Integer, default=0, comment="总消费(分)")
    total_points_earned = Column(Integer, default=0, comment="总获得积分")

    # 额度信息
    free_quota_used = Column(Integer, default=0, comment="已使用免费额度")
    subscription_quota_used = Column(Integer, default=0, comment="已使用订阅额度")

    # 赠送积分（每日清零）
    gift_points = Column(Integer, default=0, comment="赠送积分（每日清零）")
    gift_points_expiry = Column(DateTime, nullable=True, comment="赠送积分过期时间")

    # 签到信息
    last_checkin_date = Column(Date, nullable=True, comment="最后签到日期")
    consecutive_checkin_days = Column(Integer, default=0, comment="连续签到天数")

    # 邀请码信息
    invite_code = Column(String(20), unique=True, nullable=True, comment="我的邀请码")
    inviter_id = Column(String(100), ForeignKey("users.id"), nullable=True, comment="邀请人ID")
    inviter = relationship("User", foreign_keys=[inviter_id], remote_side="User.id")
    total_invite_count = Column(Integer, default=0, comment="累计邀请人数")

    def __repr__(self):
        return f"<Account(id={self.id}, user_id={self.user_id}, balance={self.balance}, points={self.points})>"


class BillingPlan(BaseModel):
    """计费套餐表"""
    __tablename__ = "billing_plans"

    # 套餐基本信息
    plan_id = Column(String(50), unique=True, nullable=False, comment="套餐ID")
    name = Column(String(100), nullable=False, comment="套餐名称")
    description = Column(Text, nullable=True, comment="套餐描述")

    # 价格信息
    price = Column(Integer, nullable=False, comment="价格(分)")
    original_price = Column(Integer, nullable=True, comment="原价(分)，用于显示折扣")

    # 有效期
    duration_days = Column(Integer, nullable=True, comment="有效天数(NULL表示永久)")

    # 包含权益
    points_included = Column(Integer, default=0, comment="包含积分")
    generation_quota = Column(Integer, default=0, comment="生成次数额度(0表示无限制)")
    daily_quota = Column(Integer, default=0, comment="每日生成次数额度(0表示无限制)")

    # 特权标记
    features = Column(JSON, nullable=True, comment="特权列表(JSON数组)")

    # 显示设置
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序序号")
    badge_text = Column(String(50), nullable=True, comment="徽章文字(如'热门')")

    def __repr__(self):
        return f"<BillingPlan(id={self.id}, plan_id={self.plan_id}, name={self.name}, price={self.price})>"


class Transaction(BaseModel):
    """交易记录表"""
    __tablename__ = "transactions"

    # 关联用户
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 交易基本信息
    transaction_type = Column(String(50), nullable=False, comment="交易类型: recharge, consumption, refund, subscription, gift, commission, system_adjust")
    amount = Column(Integer, default=0, comment="金额变化(分，正为增加，负为减少)")
    points_change = Column(Integer, default=0, comment="积分变化(正为增加，负为减少)")

    # 交易后状态
    balance_after = Column(Integer, comment="交易后余额")
    points_after = Column(Integer, comment="交易后积分")

    # 关联信息
    related_order_id = Column(String(100), nullable=True, comment="关联订单ID")
    related_request_id = Column(String(100), nullable=True, comment="关联请求ID")

    # 描述和状态
    description = Column(String(255), comment="交易描述")
    status = Column(String(20), default="success", comment="状态: pending, success, failed, cancelled")
    extra_data = Column(JSON, nullable=True, comment="额外信息(JSON)")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type={self.transaction_type}, amount={self.amount})>"


class ConsumptionRecord(BaseModel):
    """消费记录表"""
    __tablename__ = "consumption_records"

    # 关联用户
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 关联请求
    request_id = Column(String(100), nullable=True, comment="关联的生成请求ID")

    # 模型信息
    model_name = Column(String(100), comment="使用的模型名称")
    provider = Column(String(50), comment="Provider名称")

    # 计费信息
    cost_type = Column(String(20), nullable=False, comment="计费类型: free, subscription, points, balance")
    points_used = Column(Integer, default=0, comment="消耗积分")
    amount = Column(Integer, default=0, comment="消耗金额(分)")

    # 生成信息
    prompt = Column(Text, comment="提示词")
    image_count = Column(Integer, default=1, comment="生成图片数量")
    image_urls = Column(JSON, comment="生成的图片URL列表")

    # 状态信息
    status = Column(String(20), default="success", comment="状态: success, failed")
    error_reason = Column(Text, nullable=True, comment="失败原因")

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<ConsumptionRecord(id={self.id}, user_id={self.user_id}, model={self.model_name}, cost_type={self.cost_type})>"


class Withdrawal(BaseModel):
    """提现申请表"""
    __tablename__ = "withdrawals"

    # 基本信息
    withdrawal_id = Column(String(100), unique=True, nullable=False, comment="提现单号")
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    user = relationship("User", foreign_keys=[user_id])

    # 金额信息
    amount = Column(Integer, nullable=False, comment="提现金额(分)")

    # 收款信息（线下打款需要）
    withdrawal_method = Column(String(20), nullable=False, comment="提现方式: wechat, alipay, bank")
    withdrawal_account = Column(String(200), comment="提现账号(微信号/支付宝号/银行卡号)")
    withdrawal_name = Column(String(100), comment="收款人姓名")

    # 状态
    status = Column(String(20), default="pending", comment="状态: pending, approved, rejected, completed, failed")

    # 审核信息
    admin_id = Column(String(100), nullable=True, comment="审核管理员ID")
    review_note = Column(String(500), nullable=True, comment="审核备注")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")

    # 完成信息（线下打款）
    payment_proof = Column(String(500), nullable=True, comment="支付凭证URL/备注")
    completed_at = Column(DateTime, nullable=True, comment="完成打款时间")

    # 备注信息
    user_note = Column(String(500), nullable=True, comment="用户备注")

    def __repr__(self):
        return f"<Withdrawal(id={self.id}, withdrawal_id={self.withdrawal_id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
