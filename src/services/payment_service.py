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

    async def update_order_payment_info(
        self,
        order_id: str,
        qr_code_url: Optional[str] = None,
        prepay_id: Optional[str] = None,
        pay_url: Optional[str] = None,
        payment_channel: Optional[str] = None,
    ) -> Optional[PaymentOrder]:
        """
        更新订单支付信息（二维码URL、预支付ID等）

        Args:
            order_id: 订单号
            qr_code_url: 支付二维码URL
            prepay_id: 预支付ID
            pay_url: 支付跳转URL（H5支付用）
            payment_channel: 支付渠道

        Returns:
            更新后的订单，订单不存在返回None
        """
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(PaymentOrder).where(PaymentOrder.order_id == order_id)
            result = await session.execute(stmt)
            order = result.scalar_one_or_none()

            if not order:
                return None

            if qr_code_url is not None:
                order.qr_code_url = qr_code_url
            if prepay_id is not None:
                order.prepay_id = prepay_id
            if pay_url is not None:
                order.pay_url = pay_url
            if payment_channel is not None:
                order.payment_channel = payment_channel

            await session.commit()
            await session.refresh(order)

            logger.info(f"更新订单支付信息: {order_id}")
            return order

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
        paid_amount: Optional[int] = None,  # 支付金额（分），用于校验
    ) -> bool:
        """
        处理支付成功回调

        Args:
            order_id: 订单号
            transaction_id: 第三方交易ID
            notify_data: 回调原始数据
            paid_amount: 实际支付金额（分），用于安全校验

        Returns:
            是否处理成功
        """
        order = await self.get_order(order_id)
        if not order:
            logger.warning(f"订单不存在: {order_id}")
            return False

        # 幂等性检查：订单已支付
        if order.status == "paid":
            logger.info(f"订单已处理，跳过: {order_id}")
            return True

        # 状态检查：订单必须是待支付状态
        if order.status != "pending":
            logger.warning(f"订单状态异常，无法处理: {order_id}, status={order.status}")
            return False

        # 金额校验：确保支付金额与订单金额一致
        if paid_amount is not None and paid_amount != order.amount:
            logger.error(
                f"金额不匹配! order={order_id}, "
                f"order_amount={order.amount}, paid_amount={paid_amount}"
            )
            return False

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

                # 添加交易记录（只增加积分，不增加余额）
                await account_service.db_manager.add_transaction(
                    user_id=order.user_id,
                    transaction_type="recharge",
                    amount=0,  # 不增加余额，充值只送积分
                    points_change=total_points,  # 获得积分
                    description=f"充值 - {recharge_option.get('name', '积分充值')}",
                    related_order_id=order.order_id,
                )

                logger.info(
                    f"充值发放: user={order.user_id}, points={total_points}, balance_change=0"
                )

        elif order.order_type == "subscription":
            # 订阅：开通会员
            account = await account_service.get_or_create_account(order.user_id)

            # 查找套餐配置
            plan_config = self._get_plan_config(order.plan_id)
            duration_days = plan_config.get("duration_days", 30) if plan_config else 30
            points_included = plan_config.get("points_included", 0) if plan_config else 0
            plan_name = plan_config.get("name", order.plan_id) if plan_config else order.plan_id

            # 设置订阅到期时间
            from datetime import datetime, timedelta
            account.subscription_plan = order.plan_id
            account.subscription_expires_at = datetime.now() + timedelta(days=duration_days)
            await account_service.db_manager.update_account(account)

            # 发放套餐包含的积分
            if points_included > 0:
                await account_service.db_manager.add_transaction(
                    user_id=order.user_id,
                    transaction_type="subscription",
                    amount=0,
                    points_change=points_included,
                    description=f"订阅 {plan_name} - 赠送 {points_included} 积分",
                    related_order_id=order.order_id,
                )

            logger.info(
                f"订阅开通: user={order.user_id}, plan={order.plan_id}, "
                f"expires={account.subscription_expires_at}, points={points_included}"
            )

    def _get_recharge_config(self) -> Dict[str, Any]:
        """获取充值配置"""
        return self._load_billing_config().get("recharge_options", {})

    def _get_plan_config(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取订阅套餐配置"""
        config = self._load_billing_config()
        plans = config.get("subscription_plans", {}).get("plans", [])
        for plan in plans:
            if plan.get("id") == plan_id or plan.get("plan_id") == plan_id:
                return plan
        return None

    def _load_billing_config(self) -> Dict[str, Any]:
        """加载计费配置"""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "config" / "billing_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载计费配置失败: {str(e)}")
            return {}


# 微信支付相关
class WeChatPayService:
    """微信支付服务 - 使用 wechatpayv3 异步 SDK（平台公钥模式）"""

    def __init__(self):
        self.appid = settings.wechat_appid or ""
        self.mch_id = settings.wechat_mch_id or ""
        self.api_key = settings.wechat_api_key or ""  # APIv3密钥
        self.cert_serial_no = settings.wechat_cert_serial_no or ""  # 商户证书序列号
        self.key_path = settings.wechat_key_path or ""  # 商户私钥路径
        self.notify_url = settings.wechat_notify_url or ""
        # 平台公钥模式
        self.public_key = settings.wechat_public_key or ""  # 微信支付平台公钥
        self.public_key_id = settings.wechat_public_key_id or ""  # 微信支付平台公钥ID
        self._private_key = None

    def _load_private_key(self) -> str:
        """加载商户私钥"""
        if self._private_key:
            return self._private_key

        if not self.key_path:
            raise ValueError("微信支付商户私钥路径未配置 (wechat_key_path)")

        # 同步读取私钥文件
        try:
            with open(self.key_path, 'r', encoding='utf-8') as f:
                self._private_key = f.read()
            return self._private_key
        except Exception as e:
            logger.error(f"读取商户私钥失败: {e}")
            raise ValueError(f"读取商户私钥失败: {e}")

    def _load_public_key(self) -> str:
        """加载微信支付平台公钥"""
        if not self.public_key:
            return ""

        # 如果直接配置了公钥内容，直接返回
        if self.public_key.startswith('-----BEGIN PUBLIC KEY-----'):
            return self.public_key

        # 否则作为文件路径读取
        try:
            with open(self.public_key, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取平台公钥失败: {e}")
            raise ValueError(f"读取平台公钥失败: {e}")

    def _is_configured(self) -> bool:
        """检查是否配置完整（平台公钥模式）"""
        return all([
            self.appid,
            self.mch_id,
            self.api_key,
            self.cert_serial_no,
            self.key_path,
            self.public_key,
            self.public_key_id,
        ])

    async def _create_client(self):
        """创建微信支付客户端（异步版本 - 平台公钥模式）"""
        from wechatpayv3.async_ import AsyncWeChatPay, WeChatPayType

        private_key = self._load_private_key()

        # 创建异步客户端（平台公钥模式）
        client = AsyncWeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=self.mch_id,
            private_key=private_key,
            cert_serial_no=self.cert_serial_no,
            apiv3_key=self.api_key,
            appid=self.appid,
            notify_url=self.notify_url,
            logger=logger,
            partner_mode=False,
            # 平台公钥模式参数
            public_key=self._load_public_key(),
            public_key_id=self.public_key_id,
        )

        return client

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
        from wechatpayv3.async_ import WeChatPayType
        import json

        if not self._is_configured():
            # 配置不完整，使用模拟模式
            logger.info(f"[模拟] 创建微信Native支付: order={order_id}, amount={amount}")
            return {
                "code_url": f"weixin://wxpay/bizpayurl?pr={mock_random_string()}",
                "prepay_id": f"wx{mock_random_string(32)}",
            }

        try:
            async with await self._create_client() as client:
                code, message = await client.pay(
                    description=subject,
                    out_trade_no=order_id,
                    amount={'total': amount, 'currency': 'CNY'},
                    pay_type=WeChatPayType.NATIVE,
                )

                if code == 200:
                    data = json.loads(message) if isinstance(message, str) else message
                    code_url = data.get('code_url', '')
                    logger.info(f"微信Native支付创建成功: order={order_id}, code_url={code_url[:50]}...")
                    return {
                        "code_url": code_url,
                        "prepay_id": data.get('prepay_id', ''),
                    }
                else:
                    logger.error(f"微信Native支付创建失败: code={code}, message={message}")
                    raise Exception(f"微信支付下单失败: {message}")

        except Exception as e:
            logger.error(f"创建微信Native支付异常: {e}")
            raise

    async def create_h5_pay(
        self, order_id: str, amount: int, subject: str, client_ip: str
    ) -> Dict[str, Any]:
        """
        创建微信H5支付（手机网页支付）

        Args:
            order_id: 订单号
            amount: 金额（分）
            subject: 商品描述
            client_ip: 客户端IP地址

        Returns:
            {"h5_url": "支付跳转链接"}
        """
        from wechatpayv3.async_ import WeChatPayType
        import json

        if not self._is_configured():
            # 配置不完整，使用模拟模式
            logger.info(f"[模拟] 创建微信H5支付: order={order_id}, amount={amount}")
            return {
                "h5_url": f"https://wx.tenpay.com/cgi-bin/mmpayweb-bin/checkmweb?prepay_id=wx{mock_random_string(32)}&package=mock"
            }

        try:
            async with await self._create_client() as client:
                code, message = await client.pay(
                    description=subject,
                    out_trade_no=order_id,
                    amount={'total': amount, 'currency': 'CNY'},
                    scene_info={
                        'payer_client_ip': client_ip,
                        'h5_info': {'type': 'Wap'}
                    },
                    pay_type=WeChatPayType.H5,
                )

                if code == 200:
                    data = json.loads(message) if isinstance(message, str) else message
                    h5_url = data.get('h5_url', '')
                    logger.info(f"微信H5支付创建成功: order={order_id}, h5_url={h5_url[:50]}...")
                    return {
                        "h5_url": h5_url,
                    }
                else:
                    logger.error(f"微信H5支付创建失败: code={code}, message={message}")
                    raise Exception(f"微信H5支付下单失败: {message}")

        except Exception as e:
            logger.error(f"创建微信H5支付异常: {e}")
            raise

    async def query_order(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态

        Args:
            order_id: 商户订单号

        Returns:
            订单状态信息
        """
        import json

        if not self._is_configured():
            logger.info(f"[模拟] 查询微信订单: order={order_id}")
            return {
                "trade_state": "NOTPAY",
                "out_trade_no": order_id,
            }

        try:
            async with await self._create_client() as client:
                code, message = await client.query(out_trade_no=order_id)

                if code == 200:
                    data = json.loads(message) if isinstance(message, str) else message
                    logger.info(f"查询微信订单成功: order={order_id}, state={data.get('trade_state')}")
                    return data
                else:
                    logger.error(f"查询微信订单失败: code={code}, message={message}")
                    raise Exception(f"查询订单失败: {message}")

        except Exception as e:
            logger.error(f"查询微信订单异常: {e}")
            raise

    async def close_order(self, order_id: str) -> bool:
        """
        关闭订单

        Args:
            order_id: 商户订单号

        Returns:
            是否关闭成功
        """
        if not self._is_configured():
            logger.info(f"[模拟] 关闭微信订单: order={order_id}")
            return True

        try:
            async with await self._create_client() as client:
                code, message = await client.close(out_trade_no=order_id)

                if code in (200, 204):
                    logger.info(f"关闭微信订单成功: order={order_id}")
                    return True
                else:
                    logger.warning(f"关闭微信订单失败: code={code}, message={message}")
                    return False

        except Exception as e:
            logger.error(f"关闭微信订单异常: {e}")
            return False

    async def handle_callback(self, headers: Dict[str, str], body: bytes) -> Optional[Dict[str, Any]]:
        """
        处理微信支付回调通知（验签 + 解密）

        Args:
            headers: HTTP请求头（需要包含 Wechatpay-* 头）
            body: 请求体原始字节

        Returns:
            解密后的回调数据，验签失败返回 None
        """
        import json

        if not self._is_configured():
            # 模拟模式，不验签
            logger.warning("[模拟] 微信回调未验签")
            try:
                return json.loads(body.decode('utf-8'))
            except Exception:
                return None

        try:
            # 将 headers 的 key 转换为小写格式（FastAPI 兼容）
            headers_lower = {k.lower(): v for k, v in headers.items()}

            # 获取必要的回调头信息（SDK 支持小写的 fastapi 格式）
            callback_headers = {
                'wechatpay-serial': headers_lower.get('wechatpay-serial', ''),
                'wechatpay-nonce': headers_lower.get('wechatpay-nonce', ''),
                'wechatpay-signature': headers_lower.get('wechatpay-signature', ''),
                'wechatpay-timestamp': headers_lower.get('wechatpay-timestamp', ''),
            }

            # 使用同步客户端的 callback 方法（验签不需要网络请求）- 平台公钥模式
            from wechatpayv3 import WeChatPay, WeChatPayType

            private_key = self._load_private_key()
            sync_client = WeChatPay(
                wechatpay_type=WeChatPayType.NATIVE,
                mchid=self.mch_id,
                private_key=private_key,
                cert_serial_no=self.cert_serial_no,
                apiv3_key=self.api_key,
                appid=self.appid,
                notify_url=self.notify_url,
                logger=logger,
                partner_mode=False,
                # 平台公钥模式参数
                public_key=self._load_public_key(),
                public_key_id=self.public_key_id,
            )

            # 使用 SDK 进行验签和解密
            result = sync_client.callback(
                headers=callback_headers,
                body=body.decode('utf-8')
            )

            if result is None:
                logger.error("微信回调验签失败")
                return None

            # result 包含解密后的 resource 字段
            logger.info(f"微信回调验签解密成功: order={result.get('out_trade_no', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"微信回调验签失败: {e}")
            return None


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
