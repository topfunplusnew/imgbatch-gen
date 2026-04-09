"""积分相关定时任务"""

import asyncio
from datetime import datetime, date
from loguru import logger

from ..database import get_db_manager
from ..database.billing_models import Account
from sqlalchemy import select, update


async def reset_daily_gift_points():
    """
    每日清零赠送积分
    每天0点执行，将所有用户的赠送积分清零
    """
    logger.info("开始执行每日赠送积分清零任务...")

    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                update(Account)
                .where(Account.gift_points > 0)
                .values(gift_points=0, gift_points_expiry=None, gift_points_date=None)
            )
            await session.commit()
            reset_count = result.rowcount

        logger.info(f"每日赠送积分清零任务完成，共清零 {reset_count} 个用户的赠送积分")
        return {"status": "success", "reset_count": reset_count}

    except Exception as e:
        logger.error(f"每日赠送积分清零任务失败: {str(e)}")
        raise


async def check_and_reset_gift_points_on_operation(user_id: str):
    """
    用户操作时检查并重置赠送积分
    如果上次记录日期不是今天，则清零赠送积分
    """
    db_manager = get_db_manager()
    account = await db_manager.get_account_by_user(user_id)

    if not account:
        return

    today = date.today()
    last_date = account.gift_points_date

    if last_date is None or last_date != today:
        if account.gift_points and account.gift_points > 0:
            logger.info(f"用户 {user_id} 赠送积分日期重置，清零积分: {account.gift_points}")
            account.gift_points = 0
            account.gift_points_expiry = None

        account.gift_points_date = today
        await db_manager.update_account(account)
