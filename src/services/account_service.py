"""账户计费服务"""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger

from ..database import get_db_manager, Account, Transaction, ConsumptionRecord
from ..config.settings import settings


# 加载计费配置
def load_billing_config() -> Dict[str, Any]:
    """加载计费配置"""
    config_path = Path(__file__).parent.parent / "config" / "billing_config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"计费配置文件不存在: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"计费配置文件解析失败: {str(e)}")
        return {}


# 全局配置缓存
_billing_config: Optional[Dict[str, Any]] = None


def get_billing_config() -> Dict[str, Any]:
    """获取计费配置（带缓存）"""
    global _billing_config
    if _billing_config is None:
        _billing_config = load_billing_config()
    return _billing_config


class AccountService:
    """账户服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.config = get_billing_config()

    async def get_account(self, user_id: str) -> Optional[Account]:
        """获取用户账户"""
        return await self.db_manager.get_account_by_user(user_id)

    async def get_or_create_account(self, user_id: str) -> Account:
        """获取或创建用户账户"""
        account = await self.get_account(user_id)
        if not account:
            account = await self.db_manager.create_user_account(user_id)
            # 赋予初始免费额度
            initial_quota = self.config.get("initial_quota", {}).get("free_generations", 10)
            logger.info(f"新用户 {user_id} 获得初始免费额度: {initial_quota} 次")
        return account

    async def get_account_info(self, user_id: str) -> Dict[str, Any]:
        """获取账户信息（包含统计）"""
        account = await self.get_or_create_account(user_id)
        if not account:
            return None

        # 计算总积分（永久 + 临时）
        total_points = account.points + (account.gift_points or 0)

        return {
            "user_id": account.user_id,
            "balance": account.balance,  # 余额（分）
            "balance_yuan": account.balance / 100,  # 余额（元）
            "points": account.points,  # 永久积分
            "gift_points": account.gift_points or 0,  # 临时积分（签到赠送）
            "gift_points_expiry": account.gift_points_expiry.isoformat() if account.gift_points_expiry else None,
            "total_points": total_points,  # 总可用积分
            "subscription_plan": account.subscription_plan,
            "subscription_expires_at": account.subscription_expires_at.isoformat() if account.subscription_expires_at else None,
            "total_generated": account.total_generated,
            "total_spent": account.total_spent / 100 if account.total_spent else 0,  # 总消费（元）
            "total_points_earned": account.total_points_earned or 0,  # 历史累计获得积分
        }

    async def get_model_price(self, model_name: str) -> Dict[str, int]:
        """获取模型价格"""
        models = self.config.get("model_pricing", {}).get("models", {})
        model_config = models.get(model_name, models.get("default", {}))
        return {
            "points": model_config.get("points", 10),
            "amount": model_config.get("amount", 50),  # 分
        }

    async def can_generate(self, user_id: str, model_name: str, count: int = 1) -> tuple[bool, str]:
        """
        检查用户是否可以生成图片

        Returns:
            (是否可以生成, 原因说明)
        """
        account = await self.get_or_create_account(user_id)
        if not account:
            return False, "账户不存在"

        model_price = await self.get_model_price(model_name)
        required_points = model_price["points"] * count
        required_amount = model_price["amount"] * count

        # 计算总可用积分（临时 + 永久）
        total_points = (account.gift_points or 0) + account.points

        # 优先使用临时积分，再使用永久积分
        if total_points >= required_points:
            return True, f"积分充足，消耗 {required_points} 积分"

        # 检查余额
        if account.balance >= required_amount:
            return True, f"余额支付，消耗 {required_amount / 100:.2f} 元"

        return False, f"积分和余额不足，需要 {required_points} 积分或 {required_amount / 100:.2f} 元"

    async def calculate_cost(self, user_id: str, model_name: str, count: int = 1) -> Dict[str, Any]:
        """
        计算生成成本

        扣费优先级：临时积分(gift_points) > 永久积分(points) > 余额(balance)

        Returns:
            {
                "cost_type": "gift_points" | "points" | "balance",
                "points_used": int,
                "amount": int (分),
                "description": str,
            }
        """
        account = await self.get_or_create_account(user_id)
        model_price = await self.get_model_price(model_name)
        required_points = model_price["points"] * count

        # 1. 优先检查临时积分（签到赠送，当日清零）
        gift_points = account.gift_points or 0
        if gift_points >= required_points:
            return {
                "cost_type": "gift_points",
                "points_used": required_points,
                "amount": 0,
                "description": f"使用临时积分 ({required_points} 积分)",
            }

        # 2. 检查永久积分（注册赠送+充值）
        if account.points >= required_points:
            return {
                "cost_type": "points",
                "points_used": required_points,
                "amount": 0,
                "description": f"使用永久积分 ({required_points} 积分)",
            }

        # 3. 余额支付
        required_amount = model_price["amount"] * count
        if account.balance >= required_amount:
            return {
                "cost_type": "balance",
                "points_used": 0,
                "amount": required_amount,
                "description": f"使用余额支付 ({required_amount / 100:.2f} 元)",
            }

        # 余额不足
        return {
            "cost_type": "insufficient",
            "points_used": 0,
            "amount": 0,
            "description": f"积分和余额不足，需要 {required_points} 积分或 {required_amount / 100:.2f} 元",
        }

    async def freeze_points(
        self,
        user_id: str,
        model_name: str,
        count: int = 1,
        request_id: str = "",
    ) -> Dict[str, Any]:
        """
        冻结积分（提交生图任务前调用）

        扣费优先级：gift_points > points > balance
        冻结时立即从账户扣减，记录 freeze 类型 Transaction。
        如果余额不足，返回 status="insufficient"。

        Returns:
            {
                "status": "frozen" | "insufficient",
                "freeze_id": str,          # Transaction.id，用于后续结算
                "points_amount": int,       # 冻结的积分数
                "money_amount": int,        # 冻结的金额（分）
                "cost_type": str,           # gift_points / points / balance
                "description": str,
                "balance_after": {"points": int, "gift_points": int, "balance": float},
            }
        """
        account = await self.get_or_create_account(user_id)
        cost_info = await self.calculate_cost(user_id, model_name, count)

        if cost_info["cost_type"] == "insufficient":
            model_price = await self.get_model_price(model_name)
            required = model_price["points"] * count
            return {
                "status": "insufficient",
                "freeze_id": None,
                "points_amount": required,
                "money_amount": 0,
                "cost_type": "insufficient",
                "description": cost_info["description"],
                "balance_after": {
                    "points": account.points,
                    "gift_points": account.gift_points or 0,
                    "balance": account.balance / 100,
                },
            }

        # 从账户扣减（冻结）
        if cost_info["cost_type"] == "gift_points":
            account.gift_points -= cost_info["points_used"]
        elif cost_info["cost_type"] == "points":
            account.points -= cost_info["points_used"]
        elif cost_info["cost_type"] == "balance":
            account.balance -= cost_info["amount"]

        await self.db_manager.update_account(account)

        # 记录冻结交易
        points_change = -cost_info["points_used"] if cost_info["points_used"] else 0
        amount_change = -cost_info["amount"] if cost_info["amount"] else 0
        transaction = await self.db_manager.add_transaction(
            user_id=user_id,
            transaction_type="freeze",
            amount=amount_change,
            points_change=points_change,
            description=f"冻结积分 - {model_name} x{count}（{cost_info['description']}）",
            related_request_id=request_id,
        )

        logger.info(
            f"用户 {user_id} 冻结积分: type={cost_info['cost_type']}, "
            f"points={cost_info['points_used']}, amount={cost_info['amount']}, "
            f"freeze_id={transaction.id}"
        )

        return {
            "status": "frozen",
            "freeze_id": transaction.id,
            "points_amount": cost_info["points_used"],
            "money_amount": cost_info["amount"],
            "cost_type": cost_info["cost_type"],
            "description": f"已冻结 {cost_info['points_used']} 积分" if cost_info["points_used"] else f"已冻结 ¥{cost_info['amount'] / 100:.2f}",
            "balance_after": {
                "points": account.points,
                "gift_points": account.gift_points or 0,
                "balance": account.balance / 100,
            },
        }

    async def settle_frozen_points(
        self,
        user_id: str,
        freeze_id: str,
        success: bool,
        model_name: str = "",
        provider: str = "",
        request_id: str = "",
        prompt: str = "",
        image_count: int = 0,
        image_urls: List[str] = None,
        error_reason: str = "",
    ) -> Dict[str, Any]:
        """
        结算冻结的积分

        成功：创建 consumption 记录 + 更新统计
        失败：回滚冻结（加回积分/余额）+ 创建 refund Transaction

        Returns:
            {
                "status": "deducted" | "refunded",
                "points_amount": int,
                "money_amount": int,
                "cost_type": str,
                "description": str,
                "balance_after": {"points": int, "gift_points": int, "balance": float},
            }
        """
        # 查找冻结交易记录
        freeze_tx = await self.db_manager.get_transaction_by_id(freeze_id)
        if not freeze_tx:
            logger.error(f"冻结交易记录不存在: {freeze_id}")
            return {
                "status": "error",
                "points_amount": 0,
                "money_amount": 0,
                "cost_type": "unknown",
                "description": "冻结记录不存在",
                "balance_after": {},
            }

        frozen_points = abs(freeze_tx.points_change or 0)
        frozen_amount = abs(freeze_tx.amount or 0)
        # 从冻结描述推断 cost_type
        cost_type = "points"
        if "临时积分" in (freeze_tx.description or ""):
            cost_type = "gift_points"
        elif "余额" in (freeze_tx.description or ""):
            cost_type = "balance"

        account = await self.get_or_create_account(user_id)

        if success:
            # 成功：冻结已扣，只需记录消费和更新统计
            account.total_generated += image_count
            if frozen_amount > 0:
                account.total_spent += frozen_amount
            await self.db_manager.update_account(account)

            # 创建结算交易记录
            await self.db_manager.add_transaction(
                user_id=user_id,
                transaction_type="consumption",
                amount=-frozen_amount if frozen_amount else 0,
                points_change=-frozen_points if frozen_points else 0,
                description=f"图片生成扣费 - {model_name} x{image_count}",
                related_request_id=request_id,
            )

            # 创建消费记录
            await self.db_manager.create_consumption_record(
                user_id=user_id,
                model_name=model_name,
                provider=provider,
                cost_type=cost_type,
                points_used=frozen_points,
                amount=frozen_amount,
                request_id=request_id,
                prompt=prompt,
                image_count=image_count,
                image_urls=image_urls,
                status="success",
            )

            # 处理分销佣金
            await self._process_referral_commission(
                user_id=user_id,
                consumed_amount=frozen_amount,
                request_id=request_id,
            )

            logger.info(
                f"用户 {user_id} 结算成功: freeze_id={freeze_id}, "
                f"points={frozen_points}, amount={frozen_amount}"
            )

            return {
                "status": "deducted",
                "points_amount": frozen_points,
                "money_amount": frozen_amount,
                "cost_type": cost_type,
                "description": f"已扣除 {frozen_points} 积分" if frozen_points else f"已扣除 ¥{frozen_amount / 100:.2f}",
                "balance_after": {
                    "points": account.points,
                    "gift_points": account.gift_points or 0,
                    "balance": account.balance / 100,
                },
            }
        else:
            # 失败：回滚冻结
            if cost_type == "gift_points":
                account.gift_points = (account.gift_points or 0) + frozen_points
            elif cost_type == "points":
                account.points += frozen_points
            elif cost_type == "balance":
                account.balance += frozen_amount

            await self.db_manager.update_account(account)

            # 创建退还交易记录
            await self.db_manager.add_transaction(
                user_id=user_id,
                transaction_type="refund",
                amount=frozen_amount,
                points_change=frozen_points,
                description=f"生成失败退还 - {model_name}（{error_reason[:100] if error_reason else '未知错误'}）",
                related_request_id=request_id,
            )

            # 创建消费记录（失败）
            await self.db_manager.create_consumption_record(
                user_id=user_id,
                model_name=model_name,
                provider=provider,
                cost_type="failed",
                points_used=0,
                amount=0,
                request_id=request_id,
                prompt=prompt,
                image_count=0,
                image_urls=None,
                status="failed",
                error_reason=error_reason,
            )

            logger.info(
                f"用户 {user_id} 结算退还: freeze_id={freeze_id}, "
                f"points={frozen_points}, amount={frozen_amount}, reason={error_reason[:100] if error_reason else ''}"
            )

            return {
                "status": "refunded",
                "points_amount": frozen_points,
                "money_amount": frozen_amount,
                "cost_type": cost_type,
                "description": f"已返还 {frozen_points} 积分" if frozen_points else f"已返还 ¥{frozen_amount / 100:.2f}",
                "balance_after": {
                    "points": account.points,
                    "gift_points": account.gift_points or 0,
                    "balance": account.balance / 100,
                },
            }

    async def deduct_cost_on_success(
        self,
        user_id: str,
        model_name: str,
        provider: str,
        request_id: str,
        prompt: str,
        image_count: int = 1,
        image_urls: List[str] = None,
    ) -> ConsumptionRecord:
        """
        仅在图片生成成功后扣费

        必须确保 image_urls 不为空才调用此方法

        Returns:
            ConsumptionRecord
        """
        if not image_urls:
            raise ValueError("图片URL为空，不应扣费")

        account = await self.get_or_create_account(user_id)
        cost_info = await self.calculate_cost(user_id, model_name, image_count)

        # 更新账户
        if cost_info["cost_type"] == "gift_points":
            account.gift_points -= cost_info["points_used"]
        elif cost_info["cost_type"] == "points":
            account.points -= cost_info["points_used"]
        elif cost_info["cost_type"] == "balance":
            account.balance -= cost_info["amount"]
        elif cost_info["cost_type"] == "insufficient":
            raise ValueError("积分和余额不足，无法扣费")

        account.total_generated += image_count
        if cost_info["amount"] > 0:
            account.total_spent += cost_info["amount"]

        await self.db_manager.update_account(account)

        # 创建交易记录
        if cost_info["amount"] > 0 or cost_info["points_used"] > 0:
            await self.db_manager.add_transaction(
                user_id=user_id,
                transaction_type="consumption",
                amount=-cost_info["amount"],
                points_change=-cost_info["points_used"],
                description=f"图片生成 - {model_name} x{image_count}",
                related_request_id=request_id,
            )

        # 创建消费记录（成功）
        record = await self.db_manager.create_consumption_record(
            user_id=user_id,
            model_name=model_name,
            provider=provider,
            cost_type=cost_info["cost_type"],
            points_used=cost_info["points_used"],
            amount=cost_info["amount"],
            request_id=request_id,
            prompt=prompt,
            image_count=image_count,
            image_urls=image_urls,
            status="success",
        )

        logger.info(
            f"用户 {user_id} 生成图片成功扣费: type={cost_info['cost_type']}, "
            f"points={cost_info['points_used']}, amount={cost_info['amount']}"
        )

        # 处理分销佣金（如果用户有邀请人）
        await self._process_referral_commission(
            user_id=user_id,
            consumed_amount=cost_info["amount"],
            request_id=request_id
        )

        return record

    async def record_generation_failure(
        self,
        user_id: str,
        model_name: str,
        provider: str,
        request_id: str,
        prompt: str,
        error_reason: str,
    ) -> ConsumptionRecord:
        """
        记录生成失败（不扣费）

        Args:
            user_id: 用户ID
            model_name: 模型名称
            provider: Provider名称
            request_id: 请求ID
            prompt: 提示词
            error_reason: 失败原因

        Returns:
            ConsumptionRecord
        """
        # 创建消费记录（失败）
        record = await self.db_manager.create_consumption_record(
            user_id=user_id,
            model_name=model_name,
            provider=provider,
            cost_type="failed",
            points_used=0,
            amount=0,
            request_id=request_id,
            prompt=prompt,
            image_count=0,
            image_urls=None,
            status="failed",
            error_reason=error_reason,
        )

        logger.warning(
            f"用户 {user_id} 图片生成失败: model={model_name}, "
            f"provider={provider}, reason={error_reason}"
        )

        return record

    # 保留原有方法以兼容旧代码
    async def deduct_cost(
        self,
        user_id: str,
        model_name: str,
        provider: str,
        request_id: str,
        prompt: str,
        image_count: int = 1,
        image_urls: List[str] = None,
    ) -> ConsumptionRecord:
        """
        扣费并创建消费记录（兼容方法）

        警告：此方法会立即扣费，不关心是否生成成功。
        推荐使用 deduct_cost_on_success 代替。

        Returns:
            ConsumptionRecord
        """
        return await self.deduct_cost_on_success(
            user_id=user_id,
            model_name=model_name,
            provider=provider,
            request_id=request_id,
            prompt=prompt,
            image_count=image_count,
            image_urls=image_urls,
        )

    async def get_transactions(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Transaction]:
        """获取交易记录"""
        return await self.db_manager.get_user_transactions(user_id, limit, offset)

    async def get_consumption_records(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ConsumptionRecord]:
        """获取消费记录"""
        return await self.db_manager.get_user_consumption_records(user_id, limit, offset)

    async def _process_referral_commission(
        self,
        user_id: str,
        consumed_amount: int,
        request_id: str
    ):
        """
        处理分销佣金

        当用户消费时，如果该用户有邀请人，则给邀请人返佣金（余额）

        Args:
            user_id: 消费用户ID
            consumed_amount: 消费金额（分）
            request_id: 请求ID
        """
        if consumed_amount <= 0:
            return

        # 获取用户账户信息
        account = await self.get_or_create_account(user_id)

        # 如果没有邀请人，不返佣
        if not account.inviter_id:
            return

        # 获取佣金配置
        import json
        from pathlib import Path
        config_path = Path(__file__).parent.parent / "config" / "billing_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                referral_config = config.get("referral_config", {})
                commission_rate = referral_config.get("commission_rate", 15)  # 默认15%
        except Exception as e:
            logger.warning(f"加载分销配置失败: {e}")
            commission_rate = 15

        # 计算佣金（单位：分）
        commission_amount = int(consumed_amount * commission_rate / 100)

        if commission_amount <= 0:
            return

        # 给邀请人增加余额
        inviter_account = await self.db_manager.get_account_by_user(account.inviter_id)
        if not inviter_account:
            logger.warning(f"邀请人账户不存在: {account.inviter_id}")
            return

        inviter_account.balance += commission_amount
        await self.db_manager.update_account(inviter_account)

        # 记录交易（增加余额）
        await self.db_manager.add_transaction(
            user_id=inviter_account.user_id,
            transaction_type="commission",
            points_change=0,  # 不增加积分
            amount=commission_amount,  # 增加余额（单位：分）
            description=f"分销佣金（用户 {user_id} 消费 ¥{consumed_amount/100:.2f}，获得 {commission_rate}% 佣金）",
            related_request_id=request_id,
        )

        logger.info(
            f"分销佣金: 用户 {user_id} 消费 ¥{consumed_amount/100:.2f}，"
            f"邀请人 {inviter_account.user_id} 获得 ¥{commission_amount/100:.2f} 余额"
        )


# 全局服务实例
_account_service: Optional[AccountService] = None


def get_account_service() -> AccountService:
    """获取账户服务实例"""
    global _account_service
    if _account_service is None:
        _account_service = AccountService()
    return _account_service
