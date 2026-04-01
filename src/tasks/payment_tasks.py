"""支付相关定时任务"""

from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select

from ..database import get_db_manager, PaymentOrder
from ..services.payment_service import get_wechat_pay_service


async def poll_pending_orders():
    """
    轮询查询pending状态的订单

    目的：防止因回调失败（网络问题、服务器宕机等）导致的支付丢失

    调度：建议每5-10分钟运行一次
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=5)
    db_manager = get_db_manager()
    wechat_service = get_wechat_pay_service()

    try:
        async with db_manager.get_session() as session:
            # 查询创建超过5分钟且状态为pending的订单
            stmt = select(PaymentOrder).where(
                PaymentOrder.status == "pending",
                PaymentOrder.created_at < cutoff_time
            )
            result = await session.execute(stmt)
            pending_orders = result.scalars().all()

        if not pending_orders:
            logger.debug("轮询补偿: 没有需要检查的pending订单")
            return

        logger.info(f"轮询补偿: 检查 {len(pending_orders)} 个pending订单")

        from ..services.payment_service import get_payment_service
        payment_service = get_payment_service()

        for order in pending_orders:
            try:
                # 只处理微信支付订单
                if order.payment_method != "wechat":
                    continue

                logger.info(f"轮询查询: order={order.order_id}")

                # 调用微信支付查询接口
                status = await wechat_service.query_order(order_id=order.order_id)

                trade_state = status.get('trade_state')
                transaction_id = status.get('transaction_id')

                logger.info(f"轮询查询结果: order={order.order_id}, state={trade_state}")

                # 如果支付成功但回调丢失，手动触发处理
                if trade_state == 'SUCCESS':
                    success = await payment_service.handle_payment_success(
                        order_id=order.order_id,
                        transaction_id=transaction_id,
                        notify_data=status,
                    )
                    if success:
                        logger.info(f"轮询补偿成功: 订单 {order.order_id} 支付成功（回调丢失）")
                    else:
                        logger.warning(f"轮询补偿失败: 订单 {order.order_id} 处理失败")
                elif trade_state in ('CLOSED', 'REVOKED', 'PAYERROR'):
                    # 订单已关闭或支付失败
                    await payment_service.update_order_status(
                        order_id=order.order_id,
                        status='failed' if trade_state == 'PAYERROR' else 'cancelled'
                    )
                    logger.info(f"轮询更新: 订单 {order.order_id} 状态为 {trade_state}")
                elif trade_state == 'NOTPAY':
                    # 未支付，继续等待
                    logger.debug(f"轮询等待: 订单 {order.order_id} 尚未支付")

            except Exception as e:
                logger.error(f"轮询查询失败: {order.order_id}, {str(e)}")
                continue

    except Exception as e:
        logger.error(f"轮询任务执行失败: {str(e)}")


async def check_expired_orders():
    """
    检查并更新过期订单状态

    调度：建议每小时运行一次
    """
    db_manager = get_db_manager()

    try:
        async with db_manager.get_session() as session:
            # 查询已过期但状态仍为pending的订单
            now = datetime.utcnow()
            stmt = select(PaymentOrder).where(
                PaymentOrder.status == "pending",
                PaymentOrder.expire_time < now
            )
            result = await session.execute(stmt)
            expired_orders = result.scalars().all()

        if not expired_orders:
            logger.debug("过期订单检查: 没有过期订单")
            return

        logger.info(f"过期订单检查: 更新 {len(expired_orders)} 个过期订单")

        from ..services.payment_service import get_payment_service
        payment_service = get_payment_service()

        for order in expired_orders:
            try:
                await payment_service.update_order_status(order.order_id, "timeout")
                logger.info(f"过期订单: {order.order_id} 已更新为timeout状态")
            except Exception as e:
                logger.error(f"更新过期订单失败: {order.order_id}, {str(e)}")

    except Exception as e:
        logger.error(f"过期订单检查任务执行失败: {str(e)}")


# ==================== 任务注册 ====================

# 注意：这些任务现在由 BackgroundScheduler 调度，不再需要 APScheduler
# 请在 src/api/main.py 中注册这些任务
