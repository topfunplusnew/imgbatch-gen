"""管理员后台API路由"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional
from loguru import logger
from datetime import datetime

from ...database import get_db_manager, User, Account
from ...services.account_service import get_account_service
from ...services.withdrawal_service import get_withdrawal_service
from ..auth import RequiredAuthDependency


router = APIRouter(prefix="/api/v1/admin", tags=["管理员后台"])


# ==================== 权限验证 ====================


async def require_admin(user: dict = Depends(RequiredAuthDependency())):
    """验证管理员权限"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ==================== 请求模型 ====================


class AdjustPointsRequest(BaseModel):
    """调整积分请求"""
    points_change: int = Field(..., description="积分变化（正数增加，负数减少）")
    reason: str = Field(..., description="调整原因")


class BanUserRequest(BaseModel):
    """封禁用户请求"""
    reason: str = Field(..., description="封禁原因")


# ==================== 响应模型 ====================


class UserListItemResponse(BaseModel):
    """用户列表项响应"""
    id: str
    phone: str
    username: str
    status: str
    role: str
    created_at: str
    last_login_at: str
    # 账户信息
    points: int
    balance: int
    gift_points: int
    total_generated: int
    total_spent: int
    invite_count: int


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    id: str
    phone: str
    username: str
    status: str
    role: str
    created_at: str
    last_login_at: str
    last_login_ip: str
    phone_verified: bool
    # 账户信息
    points: int
    balance: int
    gift_points: int
    total_generated: int
    total_spent: int
    invite_code: str
    invite_count: int
    inviter_id: str
    # 签到信息
    last_checkin_date: str
    consecutive_checkin_days: int


class StatisticsResponse(BaseModel):
    """统计数据响应"""
    total_users: int
    active_users: int
    total_generated: int
    total_revenue: int
    today_users: int
    today_generated: int
    today_revenue: int


# ==================== 路由 ====================


@router.get("/users", response_model=List[UserListItemResponse], summary="用户列表")
async def get_users(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """
    获取用户列表

    - 支持按手机号/用户名搜索
    - 支持按状态筛选
    - 支持按角色筛选
    - 分页查询
    """
    db_manager = get_db_manager()

    users = await db_manager.get_users_list(
        keyword=keyword,
        status=status,
        role=role,
        limit=limit,
        offset=offset
    )

    result = []
    for user in users:
        # 使用预加载的账户信息
        account = user.account if hasattr(user, 'account') else None
        result.append(UserListItemResponse(
            id=user.id,
            phone=user.phone or "",
            username=user.username or "",
            status=user.status,
            role=user.role,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else "",
            points=account.points if account else 0,
            balance=account.balance if account else 0,
            gift_points=account.gift_points if account else 0,
            total_generated=account.total_generated if account else 0,
            total_spent=account.total_spent if account else 0,
            invite_count=account.total_invite_count if account else 0,
        ))

    return result


@router.get("/users/count", summary="用户总数")
async def get_users_count(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    admin: dict = Depends(require_admin)
):
    """获取用户总数（用于分页）"""
    db_manager = get_db_manager()

    count = await db_manager.get_users_count(keyword=keyword, status=status, role=role)

    return {"count": count}


@router.get("/users/{user_id}", response_model=UserDetailResponse, summary="用户详情")
async def get_user_detail(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """获取用户详细信息"""
    from sqlalchemy import select
    from ...database import UserAuth

    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    account = await db_manager.get_account_by_user(user_id)

    # 查询手机验证状态
    phone_verified = False
    if user.phone:
        async with db_manager.get_session() as session:
            auth_result = await session.execute(
                select(UserAuth)
                .where(UserAuth.user_id == user.id)
                .where(UserAuth.auth_type == "phone")
                .where(UserAuth.auth_identifier == user.phone)
                .where(UserAuth.verified == True)
            )
            phone_verified = auth_result.scalar_one_or_none() is not None

    return UserDetailResponse(
        id=user.id,
        phone=user.phone or "",
        username=user.username or "",
        status=user.status,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else "",
        last_login_ip=user.last_login_ip or "",
        phone_verified=phone_verified,
        points=account.points if account else 0,
        balance=account.balance if account else 0,
        gift_points=account.gift_points if account else 0,
        total_generated=account.total_generated if account else 0,
        total_spent=account.total_spent if account else 0,
        invite_code=account.invite_code if account else "",
        invite_count=account.total_invite_count if account else 0,
        inviter_id=account.inviter_id if account and account.inviter_id else "",
        last_checkin_date=account.last_checkin_date.isoformat() if account and account.last_checkin_date else "",
        consecutive_checkin_days=account.consecutive_checkin_days if account else 0,
    )


@router.post("/users/{user_id}/points", summary="调整用户积分")
async def adjust_user_points(
    user_id: str,
    body: AdjustPointsRequest,
    admin: dict = Depends(require_admin)
):
    """
    手动调整用户积分

    - 正数增加积分
    - 负数扣除积分
    - 记录调整原因
    """
    db_manager = get_db_manager()

    account = await db_manager.get_account_by_user(user_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    # 检查积分是否足够（如果是扣除）
    if body.points_change < 0 and account.points < abs(body.points_change):
        raise HTTPException(status_code=400, detail="用户积分不足")

    # 调整积分
    old_points = account.points
    account.points += body.points_change
    await db_manager.update_account(account)

    # 记录交易
    transaction_type = "gift" if body.points_change > 0 else "system_adjust"
    await db_manager.add_transaction(
        user_id=user_id,
        transaction_type=transaction_type,
        points_change=body.points_change,
        amount=0,
        description=f"管理员调整: {body.reason}",
    )

    logger.info(
        f"管理员 {admin['id']} 调整用户 {user_id} 积分: "
        f"{old_points} -> {account.points} ({body.points_change:+d})"
    )

    return {
        "success": True,
        "old_points": old_points,
        "new_points": account.points,
        "points_change": body.points_change,
    }


@router.post("/users/{user_id}/balance", summary="调整用户余额")
async def adjust_user_balance(
    user_id: str,
    body: AdjustPointsRequest,
    admin: dict = Depends(require_admin)
):
    """
    手动调整用户余额（分）

    - 正数增加余额
    - 负数扣除余额
    - 记录调整原因
    """
    db_manager = get_db_manager()

    account = await db_manager.get_account_by_user(user_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")

    # 检查余额是否足够（如果是扣除）
    if body.points_change < 0 and account.balance < abs(body.points_change):
        raise HTTPException(status_code=400, detail="用户余额不足")

    # 调整余额
    old_balance = account.balance
    account.balance += body.points_change
    await db_manager.update_account(account)

    # 记录交易
    transaction_type = "recharge" if body.points_change > 0 else "system_adjust"
    await db_manager.add_transaction(
        user_id=user_id,
        transaction_type=transaction_type,
        amount=body.points_change,
        points_change=0,
        description=f"管理员调整: {body.reason}",
    )

    logger.info(
        f"管理员 {admin['id']} 调整用户 {user_id} 余额: "
        f"{old_balance} -> {account.balance} ({body.points_change:+d})"
    )

    return {
        "success": True,
        "old_balance": old_balance,
        "new_balance": account.balance,
        "balance_change": body.points_change,
    }


@router.post("/users/{user_id}/ban", summary="封禁用户")
async def ban_user(
    user_id: str,
    body: BanUserRequest,
    admin: dict = Depends(require_admin)
):
    """封禁用户"""
    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.status == "suspended":
        raise HTTPException(status_code=400, detail="用户已被封禁")

    # 不能封禁管理员
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="不能封禁管理员")

    old_status = user.status
    user.status = "suspended"
    await db_manager.update_user(user)

    logger.info(f"管理员 {admin['id']} 封禁用户 {user_id}, 原因: {body.reason}")

    return {
        "success": True,
        "old_status": old_status,
        "new_status": user.status,
    }


@router.post("/users/{user_id}/unban", summary="解封用户")
async def unban_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """解封用户"""
    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.status != "suspended":
        raise HTTPException(status_code=400, detail="用户未被封禁")

    old_status = user.status
    user.status = "active"
    await db_manager.update_user(user)

    logger.info(f"管理员 {admin['id']} 解封用户 {user_id}")

    return {
        "success": True,
        "old_status": old_status,
        "new_status": user.status,
    }


@router.post("/users/{user_id}/set-admin", summary="设置管理员")
async def set_admin(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """将用户设置为管理员"""
    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_role = user.role
    user.role = "admin"
    await db_manager.update_user(user)

    logger.info(f"管理员 {admin['id']} 将用户 {user_id} 设置为管理员")

    return {
        "success": True,
        "old_role": old_role,
        "new_role": user.role,
    }


@router.post("/users/{user_id}/remove-admin", summary="取消管理员")
async def remove_admin(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """取消用户的管理员权限"""
    db_manager = get_db_manager()

    user = await db_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role != "admin":
        raise HTTPException(status_code=400, detail="用户不是管理员")

    # 不能取消自己的管理员权限
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")

    old_role = user.role
    user.role = "user"
    await db_manager.update_user(user)

    logger.info(f"管理员 {admin['id']} 取消用户 {user_id} 的管理员权限")

    return {
        "success": True,
        "old_role": old_role,
        "new_role": user.role,
    }


@router.get("/statistics", response_model=StatisticsResponse, summary="统计数据")
async def get_statistics(admin: dict = Depends(require_admin)):
    """
    获取平台统计数据

    - 总用户数
    - 活跃用户数
    - 总生成次数
    - 总收入
    - 今日新增用户
    - 今日生成次数
    - 今日收入
    """
    db_manager = get_db_manager()

    stats = await db_manager.get_platform_statistics()

    return StatisticsResponse(**stats)


# ==================== 提现管理相关 ====================


class WithdrawalListItemResponse(BaseModel):
    """提现列表项响应"""
    id: str
    withdrawal_id: str
    user_id: str
    username: str
    phone: str
    amount: int
    amount_yuan: float
    withdrawal_method: str
    withdrawal_account: str
    withdrawal_name: str
    status: str
    user_note: Optional[str] = None
    admin_id: Optional[str] = None
    review_note: Optional[str] = None
    payment_proof: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    completed_at: Optional[str] = None


class ApproveWithdrawalRequest(BaseModel):
    """审核通过请求"""
    note: Optional[str] = Field(None, max_length=500, description="审核备注")


class RejectWithdrawalRequest(BaseModel):
    """审核拒绝请求"""
    reason: str = Field(..., min_length=1, max_length=500, description="拒绝原因")


class MarkPaidRequest(BaseModel):
    """标记已打款请求"""
    payment_proof: Optional[str] = Field(None, max_length=500, description="支付凭证URL/备注")


@router.get("/withdrawals", response_model=List[WithdrawalListItemResponse], summary="提现列表")
async def get_withdrawals(
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """
    获取提现列表

    - 支持按状态筛选: pending, approved, rejected, completed
    - 分页查询
    """
    withdrawal_service = get_withdrawal_service()

    try:
        withdrawals = await withdrawal_service.get_withdrawals_for_admin(
            status=status,
            limit=limit,
            offset=offset
        )

        return withdrawals

    except Exception as e:
        logger.error(f"获取提现列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取提现列表失败")


@router.get("/withdrawals/count", summary="提现记录总数")
async def get_withdrawals_count(
    status: Optional[str] = Query(None, description="状态筛选"),
    admin: dict = Depends(require_admin)
):
    """获取提现记录总数（用于分页）"""
    db_manager = get_db_manager()

    try:
        count = await db_manager.get_withdrawals_count(status=status)

        return {"count": count}

    except Exception as e:
        logger.error(f"获取提现记录总数失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取提现记录总数失败")


@router.post("/withdrawals/{withdrawal_id}/approve", summary="审核通过")
async def approve_withdrawal(
    withdrawal_id: str,
    body: ApproveWithdrawalRequest,
    admin: dict = Depends(require_admin)
):
    """
    审核通过提现申请

    - 审核通过后，用户余额被扣除
    - 状态变为 approved
    - 管理员需要线下打款后，再标记为 completed
    """
    withdrawal_service = get_withdrawal_service()

    try:
        result = await withdrawal_service.approve_withdrawal(
            withdrawal_id=withdrawal_id,
            admin_id=admin["id"],
            note=body.note
        )

        logger.info(f"管理员 {admin['id']} 审核通过提现: {withdrawal_id}")

        return {
            "success": True,
            "message": "提现申请已通过",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"审核通过提现失败: {str(e)}")
        raise HTTPException(status_code=500, detail="审核通过提现失败")


@router.post("/withdrawals/{withdrawal_id}/reject", summary="审核拒绝")
async def reject_withdrawal(
    withdrawal_id: str,
    body: RejectWithdrawalRequest,
    admin: dict = Depends(require_admin)
):
    """
    审核拒绝提现申请

    - 审核拒绝后，用户余额不变
    - 状态变为 rejected
    """
    withdrawal_service = get_withdrawal_service()

    try:
        result = await withdrawal_service.reject_withdrawal(
            withdrawal_id=withdrawal_id,
            admin_id=admin["id"],
            reason=body.reason
        )

        logger.info(f"管理员 {admin['id']} 审核拒绝提现: {withdrawal_id}, 原因: {body.reason}")

        return {
            "success": True,
            "message": "提现申请已拒绝",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"审核拒绝提现失败: {str(e)}")
        raise HTTPException(status_code=500, detail="审核拒绝提现失败")


@router.post("/withdrawals/{withdrawal_id}/mark-paid", summary="标记已打款")
async def mark_withdrawal_paid(
    withdrawal_id: str,
    body: MarkPaidRequest,
    admin: dict = Depends(require_admin)
):
    """
    标记提现为已打款

    - 管理员线下打款完成后调用
    - 状态变为 completed
    """
    withdrawal_service = get_withdrawal_service()

    try:
        result = await withdrawal_service.mark_as_paid(
            withdrawal_id=withdrawal_id,
            admin_id=admin["id"],
            payment_proof=body.payment_proof
        )

        logger.info(f"管理员 {admin['id']} 标记提现为已打款: {withdrawal_id}")

        return {
            "success": True,
            "message": "提现已标记为已打款",
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"标记已打款失败: {str(e)}")
        raise HTTPException(status_code=500, detail="标记已打款失败")


@router.get("/withdrawals/export", summary="导出待打款订单Excel")
async def export_withdrawals(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    admin: dict = Depends(require_admin)
):
    """
    导出待打款订单Excel

    - 导出状态为 approved（已审核通过但未打款）的订单
    - 包含收款信息，用于线下批量打款
    - 支持日期范围筛选
    """
    withdrawal_service = get_withdrawal_service()

    try:
        excel_data = await withdrawal_service.export_approved_withdrawals_to_excel(
            start_date=start_date,
            end_date=end_date
        )

        filename = f"withdrawals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"导出Excel失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出Excel失败")
