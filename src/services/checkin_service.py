"""签到服务"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger

from ..database import get_db_manager, Account
from ..config.settings import settings


class CheckinService:
    """签到服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        self.daily_reward = 40  # 每日签到奖励40积分

    async def daily_checkin(self, user_id: str) -> Dict[str, Any]:
        """
        每日签到

        Args:
            user_id: 用户ID

        Returns:
            {
                "success": True,
                "reward_points": int,
                "consecutive_days": int,
                "gift_points": int,
                "gift_points_expiry": str,
            }
        """
        # 获取账户
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            raise ValueError("账户不存在")

        today = date.today()

        # 检查是否已签到
        if account.last_checkin_date == today:
            raise ValueError("今日已签到")

        # 检查赠送积分是否需要清零
        await self._check_and_reset_gift_points(account)

        # 计算连续天数
        yesterday = today - timedelta(days=1)
        if account.last_checkin_date == yesterday:
            account.consecutive_checkin_days += 1
        else:
            account.consecutive_checkin_days = 1

        # 发放签到奖励（40永久积分，不清零）
        account.points = (account.points or 0) + self.daily_reward
        account.total_points_earned = (account.total_points_earned or 0) + self.daily_reward
        account.last_checkin_date = today

        await self.db_manager.update_account(account)

        logger.info(
            f"用户 {user_id} 签到成功，连续 {account.consecutive_checkin_days} 天，"
            f"奖励 {self.daily_reward} 永久积分"
        )

        return {
            "success": True,
            "reward_points": self.daily_reward,
            "consecutive_days": account.consecutive_checkin_days,
            "gift_points": account.gift_points or 0,
            "gift_points_expiry": account.gift_points_expiry.isoformat() if account.gift_points_expiry else None,
        }

    async def get_checkin_status(self, user_id: str) -> Dict[str, Any]:
        """
        获取签到状态

        Args:
            user_id: 用户ID

        Returns:
            {
                "can_checkin": bool,
                "consecutive_days": int,
                "gift_points": int,
                "gift_points_expiry": str,
                "last_checkin_date": str,
            }
        """
        account = await self.db_manager.get_account_by_user(user_id)
        if not account:
            return {
                "can_checkin": False,
                "consecutive_days": 0,
                "gift_points": 0,
                "gift_points_expiry": None,
                "last_checkin_date": None,
            }

        today = date.today()

        # 检查赠送积分是否过期
        if account.gift_points_expiry and datetime.now() > account.gift_points_expiry:
            # 赠送积分已过期，需要清零（但不自动清零，只在下次操作时清零）
            pass

        return {
            "can_checkin": account.last_checkin_date != today,
            "consecutive_days": account.consecutive_checkin_days or 0,
            "gift_points": account.gift_points or 0,
            "gift_points_expiry": account.gift_points_expiry.isoformat() if account.gift_points_expiry else None,
            "last_checkin_date": account.last_checkin_date.isoformat() if account.last_checkin_date else None,
        }

    async def _check_and_reset_gift_points(self, account: Account):
        """
        检查并重置赠送积分

        如果当前时间已过赠送积分过期时间，则清零赠送积分
        """
        if account.gift_points_expiry and datetime.now() > account.gift_points_expiry:
            expired_points = account.gift_points or 0
            account.gift_points = 0
            account.gift_points_expiry = None
            logger.info(f"用户 {account.user_id} 的 {expired_points} 赠送积分已过期清零")


# 全局服务实例
_checkin_service: Optional[CheckinService] = None


def get_checkin_service() -> CheckinService:
    """获取签到服务实例"""
    global _checkin_service
    if _checkin_service is None:
        _checkin_service = CheckinService()
    return _checkin_service
