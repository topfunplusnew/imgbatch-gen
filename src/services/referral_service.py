"""邀请码服务"""

import random
import string
from typing import Dict, Any, List, Optional
from loguru import logger

from ..database import get_db_manager, Account, User


class ReferralService:
    """邀请服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.reward_points = 50  # 邀请奖励50积分

    def _generate_invite_code(self) -> str:
        """生成8位邀请码（大写字母+数字）"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    async def get_my_invite_code(self, user_id: str) -> str:
        """
        获取我的邀请码

        如果没有邀请码，则自动生成一个
        """
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            raise ValueError("账户不存在")

        if not account.invite_code:
            account.invite_code = self._generate_invite_code()
            await self.db_manager.update_account(account)
            logger.info(f"用户 {user_id} 生成邀请码: {account.invite_code}")

        return account.invite_code

    async def apply_invite_code(self, user_id: str, invite_code: str) -> Dict[str, Any]:
        """
        使用邀请码（新用户注册时调用）

        给邀请人奖励50积分
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
        inviter_account.points += self.reward_points
        inviter_account.total_invite_count += 1
        await self.db_manager.update_account(inviter_account)

        # 记录交易
        await self.db_manager.add_transaction(
            user_id=inviter_account.user_id,
            transaction_type="gift",
            points_change=self.reward_points,
            amount=0,
            description=f"邀请奖励（用户 {user_id} 使用您的邀请码）",
        )

        logger.info(
            f"用户 {user_id} 使用邀请码 {invite_code}，"
            f"邀请人 {inviter_account.user_id} 获得 {self.reward_points} 积分"
        )

        return {
            "success": True,
            "inviter_id": inviter_account.user_id,
            "reward_points": self.reward_points,
        }

    async def get_invite_records(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取邀请记录

        返回所有使用我邀请码注册的用户列表
        """
        async with self.db_manager.get_session() as session:
            from sqlalchemy import select
            from ..database import Account

            stmt = select(Account).where(Account.inviter_id == user_id)
            result = await session.execute(stmt)
            accounts = list(result.scalars().all())

        # 获取用户详情
        records = []
        for acc in accounts:
            user = await self.db_manager.get_user_by_id(acc.user_id)
            records.append({
                "user_id": acc.user_id,
                "username": user.username if user else "",
                "phone": user.phone if (user and user.phone) else None,
                "created_at": acc.created_at.isoformat() if acc.created_at else "",
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
        total_reward = actual_invite_count * self.reward_points

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
