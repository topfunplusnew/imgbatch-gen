"""支付服务"""

import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger

from ..database import get_db_manager, PaymentOrder, PaymentRefund
from ..config.settings import settings


class PaymentService:
    """支付服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.order_expire_minutes = 30  # 订单过期时间（分钟）

    def _generate_order_id(self) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PAY{timestamp}{random_str}"

    def _generate_refund_id(self) -> str:
        """生成退款单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"REF{timestamp}{random_str}"

    async def create_order(
        self,
        user_id: str,
        order_type: str,
        amount: int,
        payment_method: str,
        plan_id: Optional[str] = None,
        subject: str = "",
        body: str = "",
    ) -> PaymentOrder:
        """
        创建支付订单

        Args:
            user_id: 用户ID
            order_type: 订单类型 (recharge, subscription)
            amount: 金额（分）
            payment_method: 支付方式 (wechat, alipay)
            plan_id: 套餐ID（可选）
            subject: 订单标题
            body: 订单描述

        Returns:
            PaymentOrder
        """
        order_id = self._generate_order_id()
        expire_time = datetime.utcnow() + timedelta(minutes=self.order_expire_minutes)

        order = PaymentOrder(
            order_id=order_id,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            payment_method=payment_method,
            payment_channel="native",  # 默认扫码支付
            status="pending",
            subject=subject,
            body=body,
            plan_id=plan_id,
            expire_time=expire_time,
        )

        async with self.db_manager.get_session() as session:
            session.add(order)
            await session.flush()
            await session.commit()
            await session.refresh(order)

        logger.info(f"创建支付订单: {order_id}, user={user_id}, amount={amount}")
        return order

    async def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """获取订单"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(PaymentOrder).where(PaymentOrder.order_id == order_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_orders(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[PaymentOrder]:
        """获取用户订单列表"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = (
                select(PaymentOrder)
                .where(PaymentOrder.user_id == user_id)
                .order_by(PaymentOrder.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        transaction_id: Optional[str] = None,
        notify_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[PaymentOrder]:
        """更新订单状态"""
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(PaymentOrder).where(PaymentOrder.order_id == order_id)
            result = await session.execute(stmt)
            order = result.scalar_one_or_none()

            if not order:
                return None

            order.status = status
            if transaction_id:
                order.transaction_id = transaction_id
            if notify_data:
                order.notify_data = notify_data
            if status == "paid":
                order.paid_at = datetime.utcnow()
            order.notify_time = datetime.utcnow()

            await session.commit()
            await session.refresh(order)

            logger.info(f"更新订单状态: {order_id} -> {status}")
            return order

    async def cancel_order(self, order_id: str) -> Optional[PaymentOrder]:
        """取消订单"""
        return await self.update_order_status(order_id, "cancelled")

    async def check_order_expire(self, order_id: str) -> bool:
        """检查订单是否过期"""
        order = await self.get_order(order_id)
        if not order:
            return True

        if order.status != "pending":
            return False

        if order.expire_time and datetime.utcnow() > order.expire_time:
            await self.update_order_status(order_id, "timeout")
            return True

        return False

    async def handle_payment_success(
        self,
        order_id: str,
        transaction_id: str,
        notify_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        处理支付成功回调

        Args:
            order_id: 订单号
            transaction_id: 第三方交易ID
            notify_data: 回调原始数据

        Returns:
            是否处理成功
        """
        order = await self.get_order(order_id)
        if not order:
            logger.warning(f"订单不存在: {order_id}")
            return False

        if order.status == "paid":
            logger.info(f"订单已处理，跳过: {order_id}")
            return True

        # 更新订单状态
        order = await self.update_order_status(order_id, "paid", transaction_id, notify_data)
        if not order:
            return False

        # 发放权益
        await self._grant_benefits(order)

        logger.info(f"支付成功处理完成: {order_id}")
        return True

    async def _grant_benefits(self, order: PaymentOrder):
        """
        发放订单权益

        Args:
            order: 支付订单
        """
        from ..services.account_service import get_account_service

        account_service = get_account_service()

        if order.order_type == "recharge":
            # 充值：增加余额和积分
            config = self._get_recharge_config()
            options = config.get("options", [])
            recharge_option = None

            # 查找对应的充值选项
            for opt in options:
                if opt.get("amount") == order.amount:
                    recharge_option = opt
                    break

            if recharge_option:
                points = recharge_option.get("points", order.amount)
                bonus = recharge_option.get("bonus", 0)
                total_points = points + bonus

                # 添加交易记录（同时更新账户余额和积分）
                await account_service.db_manager.add_transaction(
                    user_id=order.user_id,
                    transaction_type="recharge",
                    amount=order.amount,  # 充值金额
                    points_change=total_points,  # 获得积分
                    description=f"充值 - {recharge_option.get('name', '余额充值')}",
                    related_order_id=order.order_id,
                )

                logger.info(
                    f"充值发放: user={order.user_id}, amount={order.amount}, points={total_points}"
                )

        elif order.order_type == "subscription":
            # 订阅：开通会员
            # TODO: 实现订阅逻辑
            logger.info(f"订阅开通: user={order.user_id}, plan={order.plan_id}")

    def _get_recharge_config(self) -> Dict[str, Any]:
        """获取充值配置"""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "config" / "billing_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("recharge_options", {})
        except Exception as e:
            logger.error(f"加载充值配置失败: {str(e)}")
            return {"options": []}


# 微信支付相关
class WeChatPayService:
    """微信支付服务"""

    def __init__(self):
        self.appid = settings.wechat_appid if hasattr(settings, 'wechat_appid') else ""
        self.mch_id = settings.wechat_mch_id if hasattr(settings, 'wechat_mch_id') else ""
        self.api_key = settings.wechat_api_key if hasattr(settings, 'wechat_api_key') else ""
        self.notify_url = settings.wechat_notify_url if hasattr(settings, 'wechat_notify_url') else ""

    async def create_native_pay(
        self, order_id: str, amount: int, subject: str
    ) -> Dict[str, Any]:
        """
        创建微信Native支付（扫码）

        Args:
            order_id: 订单号
            amount: 金额（分）
            subject: 商品描述

        Returns:
            {"code_url": "二维码链接", "prepay_id": "预支付ID"}
        """
        # TODO: 调用微信支付API
        # 开发环境返回模拟数据
        logger.info(f"[模拟] 创建微信Native支付: order={order_id}, amount={amount}")

        mock_code_url = f"weixin://wxpay/bizpayurl?pr={mock_random_string()}"

        return {
            "code_url": mock_code_url,
            "prepay_id": f"wx{mock_random_string(32)}",
        }

    def verify_notify(self, data: Dict[str, Any]) -> bool:
        """验证微信支付回调签名"""
        # TODO: 实现签名验证
        return True


# 支付宝相关
class AlipayService:
    """支付宝支付服务"""

    def __init__(self):
        self.app_id = settings.alipay_app_id if hasattr(settings, 'alipay_app_id') else ""
        self.private_key = settings.alipay_private_key if hasattr(settings, 'alipay_private_key') else ""
        self.public_key = settings.alipay_public_key if hasattr(settings, 'alipay_public_key') else ""
        self.notify_url = settings.alipay_notify_url if hasattr(settings, 'alipay_notify_url') else ""

    async def create_trade_precreate(
        self, order_id: str, amount: int, subject: str
    ) -> Dict[str, Any]:
        """
        创建支付宝当面付（扫码）

        Args:
            order_id: 订单号
            amount: 金额（分）
            subject: 商品描述

        Returns:
            {"qr_code_url": "二维码内容"}
        """
        # TODO: 调用支付宝API
        # 开发环境返回模拟数据
        logger.info(f"[模拟] 创建支付宝当面付: order={order_id}, amount={amount}")

        mock_qr_code = f"https://qr.alipay.com/{mock_random_string(24)}"

        return {
            "qr_code_url": mock_qr_code,
        }

    def verify_notify(self, data: Dict[str, Any]) -> bool:
        """验证支付宝回调签名"""
        # TODO: 实现签名验证
        return True


def mock_random_string(length: int = 16) -> str:
    """生成随机字符串（用于模拟）"""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# 全局服务实例
_payment_service: Optional[PaymentService] = None
_wechat_pay_service: Optional[WeChatPayService] = None
_alipay_service: Optional[AlipayService] = None


def get_payment_service() -> PaymentService:
    """获取支付服务实例"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service


def get_wechat_pay_service() -> WeChatPayService:
    """获取微信支付服务实例"""
    global _wechat_pay_service
    if _wechat_pay_service is None:
        _wechat_pay_service = WeChatPayService()
    return _wechat_pay_service


def get_alipay_service() -> AlipayService:
    """获取支付宝服务实例"""
    global _alipay_service
    if _alipay_service is None:
        _alipay_service = AlipayService()
    return _alipay_service
