"""JWT认证中间件"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from ..services.auth_service import get_auth_service


security = HTTPBearer(auto_error=False)


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    获取当前用户（可选，不强制登录）

    如果请求中包含有效的token，返回用户信息
    否则返回None
    """
    try:
        auth_service = get_auth_service()
        token = None
        token_source = None

        # 从 Authorization header 获取 token
        authorization: HTTPAuthorizationCredentials = await security(request)
        if authorization is None:
            # 尝试从 cookie 获取
            token = request.cookies.get("access_token")
            if token:
                token_source = "cookie"
                logger.debug(f"[Auth] Token from cookie")
            if not token:
                # 尝试从查询参数获取（用于SSE连接）
                token = request.query_params.get("token")
                if token:
                    token_source = "query"
                    logger.debug(f"[Auth] Token from query parameter (SSE)")
        else:
            token = authorization.credentials
            token_source = "header"
            logger.debug(f"[Auth] Token from Authorization header")

        if not token:
            logger.debug("[Auth] No token found")
            return None

        # 验证 token
        user = await auth_service.get_current_user(token)
        if not user:
            logger.warning(f"[Auth] Invalid token (source: {token_source})")
            return None

        logger.info(f"[Auth] ✅ User authenticated: {user.id} (source: {token_source})")
        return {
            "id": user.id,
            "email": getattr(user, 'email', None),
            "phone": user.phone,
            "username": user.username,
            "status": user.status,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    except Exception as e:
        logger.error(f"[Auth] ❌ Error: {str(e)}")
        return None


async def get_current_user(request: Request) -> dict:
    """
    获取当前用户（必须登录）

    如果未登录，抛出 401 异常
    """
    user = await get_current_user_optional(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_id(request: Request) -> str:
    """
    获取当前用户ID（必须登录）

    如果未登录，抛出 401 异常
    """
    user = await get_current_user(request)
    return user["id"]


async def get_current_user_id_optional(request: Request) -> Optional[str]:
    """
    获取当前用户ID（可选）

    如果未登录，返回 None
    """
    user = await get_current_user_optional(request)
    return user["id"] if user else None


def require_auth(*, allow_guest: bool = False):
    """
    认证装饰器工厂

    Args:
        allow_guest: 是否允许游客访问
    """
    if allow_guest:
        return get_current_user_optional
    else:
        return get_current_user


class OptionalAuthDependency:
    """
    可选认证依赖类

    使用方式:
        @router.get("/api/some-endpoint")
        async def some_endpoint(user: Optional[dict] = Depends(OptionalAuthDependency())):
            if user:
                # 已登录用户
                pass
            else:
                # 游客
                pass
    """

    async def __call__(self, request: Request) -> Optional[dict]:
        return await get_current_user_optional(request)


class RequiredAuthDependency:
    """
    必须认证依赖类

    使用方式:
        @router.get("/api/protected")
        async def protected_endpoint(user: dict = Depends(RequiredAuthDependency())):
            # user 一定不为 None
            pass
    """

    async def __call__(self, request: Request) -> dict:
        return await get_current_user(request)
