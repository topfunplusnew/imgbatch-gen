"""用户认证API路由（用户名+密码登录）"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from loguru import logger

from ...services.auth_service import get_auth_service, AuthService
from ...database import get_db_manager
from ..auth import OptionalAuthDependency, RequiredAuthDependency
from datetime import datetime


router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# ==================== 请求模型 ====================


class RegisterUsernameRequest(BaseModel):
    """用户名注册请求"""
    username: str = Field(..., min_length=2, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    password_confirmation: str = Field(..., min_length=6, max_length=50, description="确认密码")
    invite_code: Optional[str] = Field(None, description="邀请码")

    @validator('password_confirmation')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class LoginUsernameRequest(BaseModel):
    """用户名/邮箱登录请求"""
    username: str = Field(..., min_length=2, max_length=255, description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class UpdateProfileRequest(BaseModel):
    """更新个人资料请求"""
    username: Optional[str] = Field(None, min_length=2, max_length=20, description="用户名")
    phone: Optional[str] = Field(None, pattern=r'^\d{11}$', description="手机号")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class SendVerifyCodeRequest(BaseModel):
    """发送验证码请求"""
    identifier: str = Field(..., description="邮箱或手机号")
    auth_type: str = Field(..., pattern=r'^(email|phone)$', description="认证类型")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    identifier: str = Field(..., description="邮箱或手机号")
    code: str = Field(..., min_length=4, max_length=10, description="验证码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    auth_type: str = Field(..., pattern=r'^(email|phone)$', description="认证类型")


class RegisterEmailRequest(BaseModel):
    """邮箱注册请求"""
    email: str = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=4, max_length=10, description="验证码")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    password_confirmation: str = Field(..., min_length=6, max_length=50, description="确认密码")
    username: Optional[str] = Field(None, max_length=20, description="用户名(可选)")
    invite_code: Optional[str] = Field(None, description="邀请码")

    @validator('password_confirmation')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    role: str
    force_password_change: bool = False
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse


# ==================== 路由 ====================


@router.post("/register", response_model=LoginResponse, summary="用户名注册")
async def register_by_username(request: Request, body: RegisterUsernameRequest):
    """用户名+密码注册（自动登录）"""
    auth_service = get_auth_service()

    try:
        user = await auth_service.register_by_username(
            username=body.username,
            password=body.password,
            invite_code=body.invite_code,
        )

        # 生成Token
        access_token = await auth_service.create_access_token(user.id)
        refresh_token = await auth_service.create_refresh_token(user.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=getattr(user, 'email', None),
                phone=user.phone,
                status=user.status,
                role=user.role,
                force_password_change=getattr(user, 'force_password_change', False),
                created_at=user.created_at.isoformat() if user.created_at else None,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户名注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")


@router.post("/register/email", response_model=LoginResponse, summary="邮箱注册")
async def register_by_email(request: Request, body: RegisterEmailRequest):
    """邮箱+验证码注册（自动登录）"""
    auth_service = get_auth_service()

    try:
        # 验证邮箱验证码（优先从内存缓存检查，再查数据库）
        cache_key = f"email:{body.email}"
        cached = _verify_code_cache.get(cache_key)

        code_valid = False
        if cached and cached["code"] == body.code and datetime.utcnow() <= cached["expiry"]:
            code_valid = True
            _verify_code_cache.pop(cache_key, None)
        else:
            # 回退到数据库查询（已注册用户可能有user_auth记录）
            from ...database import UserAuth
            from sqlalchemy import select
            db_manager = get_db_manager()
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(UserAuth)
                    .where(UserAuth.auth_identifier == body.email)
                    .where(UserAuth.auth_type == "email")
                )
                auth_record = result.scalar_one_or_none()
                if auth_record:
                    code_valid = await auth_service.verify_code(auth_record, body.code)
                    if code_valid:
                        auth_record.verify_code = None
                        auth_record.verify_code_expiry = None
                        await session.commit()

        if not code_valid:
            raise ValueError("验证码错误或已过期")

        # 注册
        user = await auth_service.register_by_email(
            email=body.email,
            password=body.password,
            username=body.username or None,
            invite_code=body.invite_code,
        )

        # 生成Token
        access_token = await auth_service.create_access_token(user.id)
        refresh_token = await auth_service.create_refresh_token(user.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=getattr(user, 'email', None),
                phone=user.phone,
                status=user.status,
                role=user.role,
                force_password_change=getattr(user, 'force_password_change', False),
                created_at=user.created_at.isoformat() if user.created_at else None,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"邮箱注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")


@router.post("/login", response_model=LoginResponse, summary="用户名登录")
async def login_by_username(request: Request, body: LoginUsernameRequest):
    """用户名+密码登录"""
    auth_service = get_auth_service()

    try:
        result = await auth_service.login_by_username(
            username=body.username,
            password=body.password,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
        )

        return LoginResponse(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            token_type=result.get("token_type", "bearer"),
            user=UserResponse(**result["user"]),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户名登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")


@router.post("/refresh", summary="刷新Token")
async def refresh_token(body: RefreshTokenRequest):
    """刷新访问令牌"""
    auth_service = get_auth_service()

    try:
        result = await auth_service.refresh_token(body.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(user: dict = Depends(RequiredAuthDependency())):
    """获取当前登录用户信息"""
    db_manager = get_db_manager()
    user_obj = await db_manager.get_user_by_id(user["id"])
    if user_obj:
        user["force_password_change"] = getattr(user_obj, 'force_password_change', False)
        user["email"] = getattr(user_obj, 'email', None)
    return UserResponse(**user)


@router.patch("/profile", response_model=UserResponse, summary="更新个人资料")
async def update_profile(
    request: Request,
    body: UpdateProfileRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """更新当前用户资料"""
    db_manager = get_db_manager()

    # 获取用户
    user_obj = await db_manager.get_user_by_id(user["id"])
    if not user_obj:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查用户名是否被占用
    if body.username and body.username != user_obj.username:
        existing = await db_manager.get_user_by_username(body.username)
        if existing and existing.id != user_obj.id:
            raise HTTPException(status_code=400, detail="用户名已被使用")

    # 检查手机号是否被占用
    if body.phone and body.phone != user_obj.phone:
        existing = await db_manager.get_user_by_phone(body.phone)
        if existing and existing.id != user_obj.id:
            raise HTTPException(status_code=400, detail="手机号已被使用")

    # 更新用户信息
    if body.username is not None:
        user_obj.username = body.username
    if body.phone is not None:
        user_obj.phone = body.phone

    await db_manager.update_user(user_obj)

    logger.info(f"用户资料更新: user_id={user_obj.id}, username={body.username}")

    return UserResponse(
        id=user_obj.id,
        username=user_obj.username,
        email=getattr(user_obj, 'email', None),
        phone=user_obj.phone,
        status=user_obj.status,
        role=user_obj.role,
        force_password_change=getattr(user_obj, 'force_password_change', False),
        created_at=user_obj.created_at.isoformat() if user_obj.created_at else None,
    )


@router.post("/logout", summary="登出")
async def logout(user: dict = Depends(RequiredAuthDependency())):
    """
    登出

    客户端应删除本地存储的token
    """
    return {"success": True, "message": "登出成功"}


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: dict = Depends(RequiredAuthDependency())
):
    """
    修改当前用户密码

    需要提供旧密码进行验证
    """
    auth_service = get_auth_service()
    db_manager = get_db_manager()

    try:
        # 获取用户
        user_obj = await db_manager.get_user_by_id(user["id"])
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 验证旧密码
        if not await auth_service.verify_password(body.old_password, user_obj.password_hash):
            raise HTTPException(status_code=400, detail="旧密码错误")

        # 检查新密码是否与旧密码相同
        if body.old_password == body.new_password:
            raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

        # 更新密码
        password_hash = await auth_service.hash_password(body.new_password)
        user_obj.password_hash = password_hash

        # 清除强制修改密码标记（如果有）
        if hasattr(user_obj, 'force_password_change'):
            user_obj.force_password_change = False

        await db_manager.update_user(user_obj)

        logger.info(f"用户修改密码成功: user_id={user_obj.id}, username={user_obj.username}")

        return {"success": True, "message": "密码修改成功，请重新登录"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="修改密码失败，请稍后重试")


# 内存验证码存储（key: "type:identifier" -> {"code": str, "expiry": datetime}）
_verify_code_cache: dict = {}


@router.post("/send-code", summary="发送验证码")
async def send_verify_code(request: Request, body: SendVerifyCodeRequest):
    """
    发送验证码到邮箱或手机

    用于注册、绑定、密码找回等场景
    """
    from datetime import timedelta

    try:
        # 生成6位验证码
        import random
        code = ''.join(random.choices('0123456789', k=6))

        # 保存验证码到内存缓存（有效期10分钟）
        cache_key = f"{body.auth_type}:{body.identifier}"
        expiry = datetime.utcnow() + timedelta(minutes=10)
        _verify_code_cache[cache_key] = {"code": code, "expiry": expiry}
        logger.info(f"验证码已生成: {body.identifier} -> {code}")

        # 同时尝试更新已有的user_auth记录（用于已注册用户的密码重置）
        try:
            from ...database import get_db_manager, UserAuth
            from sqlalchemy import select
            db_manager = get_db_manager()
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(UserAuth)
                    .where(UserAuth.auth_identifier == body.identifier)
                    .where(UserAuth.auth_type == body.auth_type)
                )
                auth_record = result.scalar_one_or_none()
                if auth_record:
                    auth_record.verify_code = code
                    auth_record.verify_code_expiry = expiry
                    await session.commit()
        except Exception:
            pass  # 非致命：内存缓存已保存

        # 发送验证码
        if body.auth_type == 'email':
            from ...services.email_service import get_email_service
            email_service = get_email_service()
            success = await email_service.send_verify_code(body.identifier, code)
            if not success:
                raise HTTPException(status_code=500, detail="邮件发送失败，请稍后重试")
        else:  # phone
            from ...services.sms_service import get_sms_service
            sms_service = get_sms_service()
            await sms_service.send_verify_code(body.identifier, code)

        return {"success": True, "message": "验证码已发送"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="发送验证码失败，请稍后重试")


@router.post("/reset-password", summary="重置密码")
async def reset_password(request: Request, body: ResetPasswordRequest):
    """
    通过邮箱或手机号重置密码

    流程：
    1. 用户输入邮箱/手机号
    2. 发送验证码
    3. 验证码验证通过
    4. 设置新密码
    """
    auth_service = get_auth_service()
    db_manager = get_db_manager()

    try:
        # 验证验证码（先查内存缓存，再查数据库）
        cache_key = f"{body.auth_type}:{body.identifier}"
        cached = _verify_code_cache.get(cache_key)
        code_valid = False

        if cached and cached["code"] == body.code and datetime.utcnow() <= cached["expiry"]:
            code_valid = True
            _verify_code_cache.pop(cache_key, None)

        # 查找用户（通过邮箱或user_auth）
        user = None
        if body.auth_type == "email":
            user = await db_manager.get_user_by_email(body.identifier)

        if not user:
            # 回退到user_auth表查找
            from ...database import UserAuth
            from sqlalchemy import select
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(UserAuth)
                    .where(UserAuth.auth_identifier == body.identifier)
                    .where(UserAuth.auth_type == body.auth_type)
                )
                auth_record = result.scalar_one_or_none()
                if auth_record and auth_record.user_id:
                    user = await db_manager.get_user_by_id(auth_record.user_id)
                    # 也检查数据库中的验证码
                    if not code_valid:
                        code_valid = await auth_service.verify_code(auth_record, body.code)
                    if code_valid:
                        auth_record.verify_code = None
                        auth_record.verify_code_expiry = None
                        await session.commit()

        if not user:
            raise HTTPException(status_code=404, detail="该邮箱/手机号未注册")

        if not code_valid:
            raise HTTPException(status_code=400, detail="验证码错误或已过期")

        # 重置密码
        password_hash = await auth_service.hash_password(body.new_password)
        user.password_hash = password_hash
        await db_manager.update_user(user)

        logger.info(f"密码重置成功: user_id={user.id}, auth_type={body.auth_type}")

        return {"success": True, "message": "密码重置成功，请使用新密码登录"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置密码失败: {str(e)}")
        raise HTTPException(status_code=500, detail="重置密码失败，请稍后重试")
