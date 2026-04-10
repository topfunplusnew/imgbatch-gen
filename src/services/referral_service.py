"""邀请码服务"""

import random
import string
from typing import Dict, Any, List, Optional
from loguru import logger
from sqlalchemy import select, func

from ..database import get_db_manager, Account, User, PaymentOrder


class ReferralService:
    """邀请服务（分销系统）"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.register_reward_points = 50  # 注册奖励50积分（不可提现）
        self.commission_rate = 15  # 默认佣金比例15%（计入余额，可提现）

    async def _generate_invite_code(self) -> str:
        """
        生成唯一的8位邀请码（大写字母+数字）

        通过循环检测确保生成的邀请码在数据库中不存在
        """
        import asyncio

        max_attempts = 10  # 最大尝试次数
        for attempt in range(max_attempts):
            # 生成8位随机码
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # 检查是否已存在
            existing = await self.db_manager.get_account_by_invite_code(code)
            if not existing:
                logger.info(f"生成唯一邀请码: {code} (尝试 {attempt + 1}次)")
                return code

            # 如果存在，记录并重试
            logger.warning(f"邀请码冲突: {code} 已存在，重新生成...")

        # 如果10次都失败了，抛出异常
        raise RuntimeError("无法生成唯一邀请码，请稍后重试")

    async def get_my_invite_code(self, user_id: str) -> str:
        """
        获取我的邀请码

        如果没有邀请码，则自动生成一个唯一的邀请码
        """
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            raise ValueError("账户不存在")

        if not account.invite_code:
            account.invite_code = await self._generate_invite_code()
            await self.db_manager.update_account(account)
            logger.info(f"用户 {user_id} 生成邀请码: {account.invite_code}")

        return account.invite_code

    async def apply_invite_code(self, user_id: str, invite_code: str) -> Dict[str, Any]:
        """
        使用邀请码（新用户注册时调用）

        - 邀请人获得50积分（不可提现）
        - 新用户也获得50积分（不可提现）
        """
        # 查找邀请人
        inviter_account = await self.db_manager.get_account_by_invite_code(invite_code)
        if not inviter_account:
            raise ValueError("邀请码不存在")

        # 检查是否自己邀请自己
        if inviter_account.user_id == user_id:
            raise ValueError("不能使用自己的邀请码")

        # 更新当前用户的邀请人
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            raise ValueError("账户不存在")

        if account.inviter_id:
            raise ValueError("已经使用过邀请码")

        account.inviter_id = inviter_account.user_id
        await self.db_manager.update_account(account)

        # 给邀请人奖励积分
        inviter_account.points += self.register_reward_points
        inviter_account.total_invite_count += 1
        await self.db_manager.update_account(inviter_account)

        # 记录邀请人奖励交易（积分）
        await self.db_manager.add_transaction(
            user_id=inviter_account.user_id,
            transaction_type="gift",
            points_change=self.register_reward_points,
            amount=0,  # 不增加余额
            description=f"邀请注册奖励（用户 {user_id} 使用您的邀请码）",
            apply_account_change=False,
            balance_after=inviter_account.balance,
            points_after=inviter_account.points,
        )

        # 给新用户也奖励积分
        account.points += self.register_reward_points
        await self.db_manager.update_account(account)

        # 记录新用户奖励交易（积分）
        await self.db_manager.add_transaction(
            user_id=account.user_id,
            transaction_type="gift",
            points_change=self.register_reward_points,
            amount=0,  # 不增加余额
            description=f"使用邀请码注册奖励",
            apply_account_change=False,
            balance_after=account.balance,
            points_after=account.points,
        )

        logger.info(
            f"用户 {user_id} 使用邀请码 {invite_code}，"
            f"邀请人 {inviter_account.user_id} 获得 {self.register_reward_points} 积分，"
            f"新用户获得 {self.register_reward_points} 积分"
        )

        return {
            "success": True,
            "inviter_id": inviter_account.user_id,
            "reward_points": self.register_reward_points,
        }

    async def get_invite_records(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取邀请记录

        返回所有使用我邀请码注册的用户列表
        """
        async with self.db_manager.get_session() as session:
            stmt = select(Account).where(Account.inviter_id == user_id)
            result = await session.execute(stmt)
            accounts = list(result.scalars().all())

            invited_user_ids = [acc.user_id for acc in accounts if acc.user_id]
            recharge_summary: Dict[str, Dict[str, Any]] = {}

            if invited_user_ids:
                recharge_stmt = (
                    select(
                        PaymentOrder.user_id,
                        func.count(PaymentOrder.id).label("recharge_count"),
                        func.coalesce(func.sum(PaymentOrder.amount), 0).label("total_recharge_amount"),
                        func.max(PaymentOrder.paid_at).label("last_recharge_at"),
                    )
                    .where(PaymentOrder.user_id.in_(invited_user_ids))
                    .where(PaymentOrder.order_type == "recharge")
                    .where(PaymentOrder.status == "paid")
                    .group_by(PaymentOrder.user_id)
                )
                recharge_result = await session.execute(recharge_stmt)
                recharge_summary = {
                    row.user_id: {
                        "recharge_count": int(row.recharge_count or 0),
                        "total_recharge_amount": int(row.total_recharge_amount or 0),
                        "last_recharge_at": row.last_recharge_at.isoformat() if row.last_recharge_at else "",
                    }
                    for row in recharge_result
                }

        # 获取用户详情
        records = []
        for acc in accounts:
            user = await self.db_manager.get_user_by_id(acc.user_id)
            recharge_info = recharge_summary.get(acc.user_id, {})
            records.append({
                "user_id": acc.user_id,
                "username": user.username if user else "",
                "phone": user.phone if (user and user.phone) else None,
                "created_at": acc.created_at.isoformat() if acc.created_at else "",
                "recharge_count": recharge_info.get("recharge_count", 0),
                "total_recharge_amount": recharge_info.get("total_recharge_amount", 0),
                "last_recharge_at": recharge_info.get("last_recharge_at", ""),
                "has_recharged": recharge_info.get("recharge_count", 0) > 0,
            })

        return records

    async def get_invite_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取邀请统计

        返回邀请人数、累计奖励积分（通过实际查询计算，确保数据准确）
        """
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            return {
                "invite_code": "",
                "total_invite_count": 0,
                "total_reward_points": 0,
            }

        # 实际查询邀请人数，而不是依赖 total_invite_count 字段
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select, func
            from ..database import Account

            # 统计 inviter_id == user_id 的账户数量
            stmt = select(func.count(Account.id)).where(Account.inviter_id == user_id)
            result = await session.execute(stmt)
            actual_invite_count = result.scalar() or 0

        # 计算累计奖励积分
        total_reward = actual_invite_count * self.register_reward_points

        return {
            "invite_code": account.invite_code or "",
            "total_invite_count": actual_invite_count,
            "total_reward_points": total_reward,
        }


# 全局服务实例
_referral_service: Optional[ReferralService] = None


def get_referral_service() -> ReferralService:
    """获取邀请服务实例"""
    global _referral_service
    if _referral_service is None:
        _referral_service = ReferralService()
    return _referral_service
