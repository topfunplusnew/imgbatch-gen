"""用户认证服务"""

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from loguru import logger

from ..database import get_db_manager, User, UserAuth, LoginLog
from ..config.settings import settings


# 密码加密上下文 - 使用 argon2 (更安全，无长度限制)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    """用户认证服务"""

    def __init__(self):
        self.db_manager = get_db_manager()
        # JWT 配置从 settings 读取
        self.jwt_secret_key = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    async def hash_password(self, password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_access_token(
        self, user_id: str, extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建访问令牌"""
        payload = {
            "user_id": user_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
        }
        if extra_data:
            payload.update(extra_data)
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    async def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except JWTError as e:
            logger.warning(f"无效的Token: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"解码Token失败: {str(e)}")
            return None

    async def register_by_username(
        self,
        username: str,
        password: str,
        invite_code: Optional[str] = None,
    ) -> User:
        """用户名+密码注册"""
        from datetime import date
        from ..database import Account

        # 检查用户名是否已存在
        existing = await self.db_manager.get_user_by_username(username)
        if existing:
            raise ValueError("用户名已被注册")

        # 哈希密码
        password_hash = await self.hash_password(password)

        # 创建用户
        user = User(
            username=username,
            password_hash=password_hash,
        )
        await self.db_manager.create_user(user)

        # 创建账户并赠送100永久积分
        account = await self.db_manager.create_user_account(user.id)

        # 注册赠送100永久积分
        account.points = 100
        account.total_points_earned = 100
        account.invite_code = self._generate_invite_code()

        logger.info(f"用户注册成功: {username}, 赠送100永久积分, user_id: {user.id}")

        # 处理邀请码（邀请注册双方各得50积分）
        if invite_code:
            try:
                await self._process_invite_code(account, invite_code)
            except Exception as e:
                logger.error(f"处理邀请码失败: {str(e)}")
                # 邀请码处理失败不影响注册流程，继续执行
                pass

        # 保存账户信息
        await self.db_manager.update_account(account)

        logger.info(f"用户注册成功: {username}, 赠送100积分, user_id: {user.id}")
        return user

    def _generate_invite_code(self) -> str:
        """生成邀请码"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    async def _process_invite_code(self, account: "Account", invite_code: str):
        """处理邀请码（双方各得50积分）"""
        from ..database import Account
        from sqlalchemy import select

        try:
            # 使用数据库会话处理邀请码
            async with self.db_manager.get_session() as session:
                # 查找邀请人
                stmt = select(Account).where(Account.invite_code == invite_code)
                result = await session.execute(stmt)
                inviter_account = result.scalar_one_or_none()

                if not inviter_account:
                    logger.warning(f"邀请码 {invite_code} 不存在")
                    return

                # 检查是否自己邀请自己
                if inviter_account.user_id == account.user_id:
                    logger.warning(f"用户不能使用自己的邀请码")
                    return

                reward = 50  # 邀请奖励50积分

                # 给邀请人奖励50永久积分
                inviter_account.points = (inviter_account.points or 0) + reward
                inviter_account.total_points_earned = (inviter_account.total_points_earned or 0) + reward
                inviter_account.total_invite_count = (inviter_account.total_invite_count or 0) + 1

                # 给被邀请者奖励50永久积分
                account.points = (account.points or 0) + reward
                account.total_points_earned = (account.total_points_earned or 0) + reward

                # 设置当前用户的邀请人
                account.inviter_id = inviter_account.user_id

                # 记录交易
                await self.db_manager.add_transaction(
                    user_id=inviter_account.user_id,
                    transaction_type="gift",
                    points_change=reward,
                    amount=0,
                    description=f"邀请奖励（用户 {account.user_id} 使用您的邀请码注册）",
                )

                await self.db_manager.add_transaction(
                    user_id=account.user_id,
                    transaction_type="gift",
                    points_change=reward,
                    amount=0,
                    description=f"注册奖励（使用邀请码 {invite_code}）",
                )

                # 提交邀请人账户的更改到数据库
                await session.commit()

                logger.info(
                    f"用户 {account.user_id} 使用邀请码 {invite_code}，"
                    f"邀请人 {inviter_account.user_id} 获得 {reward} 积分，"
                    f"被邀请人 {account.user_id} 获得 {reward} 积分"
                )

        except Exception as e:
            logger.error(f"处理邀请码时发生错误: {str(e)}")
            # 邀请码处理失败不影响注册流程，只记录错误，不抛出异常
            pass

    async def register_by_email(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        invite_code: Optional[str] = None,
    ) -> User:
        """邮箱注册（需先验证邮箱验证码）"""
        from datetime import date
        from ..database import Account

        # 检查邮箱是否已注册
        existing = await self.db_manager.get_user_by_email(email)
        if existing:
            raise ValueError("该邮箱已被注册")

        # 自动生成用户名（如果未提供）
        if not username:
            # 用邮箱前缀作为用户名
            prefix = email.split("@")[0]
            username = prefix
            # 检查是否重复，如果重复则加随机后缀
            import random
            import string
            existing_name = await self.db_manager.get_user_by_username(username)
            if existing_name:
                username = prefix + ''.join(random.choices(string.digits, k=4))
        else:
            existing_name = await self.db_manager.get_user_by_username(username)
            if existing_name:
                raise ValueError("用户名已被注册")

        # 哈希密码
        password_hash = await self.hash_password(password)

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )
        await self.db_manager.create_user(user)

        # 创建账户并赠送100永久积分
        account = await self.db_manager.create_user_account(user.id)
        account.points = 100
        account.total_points_earned = 100
        account.invite_code = self._generate_invite_code()

        # 创建邮箱认证记录
        email_auth = UserAuth(
            user_id=user.id,
            auth_type="email",
            auth_identifier=email,
            verified=True,
        )
        await self.db_manager.create_user_auth(email_auth)

        logger.info(f"邮箱注册成功: {email}, username={username}, 赠送100永久积分, user_id: {user.id}")

        # 处理邀请码
        if invite_code:
            try:
                await self._process_invite_code(account, invite_code)
            except Exception as e:
                logger.error(f"处理邀请码失败: {str(e)}")

        await self.db_manager.update_account(account)
        return user

    async def login_by_username(
        self, username: str, password: str, client_ip: str, user_agent: str
    ) -> Dict[str, Any]:
        """用户名或邮箱+密码登录"""
        # 先尝试用户名查找，再尝试邮箱查找
        user = await self.db_manager.get_user_by_username(username)
        if not user and "@" in username:
            user = await self.db_manager.get_user_by_email(username)
        if not user:
            await self._log_login(None, "username", "failed", "用户不存在", client_ip, user_agent)
            raise ValueError("用户名或密码错误")

        # 验证密码
        if not await self.verify_password(password, user.password_hash):
            await self._log_login(user.id, "username", "failed", "密码错误", client_ip, user_agent)
            raise ValueError("用户名或密码错误")

        # 检查用户状态
        if user.status != "active":
            await self._log_login(user.id, "username", "failed", "用户已被禁用", client_ip, user_agent)
            raise ValueError("用户已被禁用")

        # 生成Token
        access_token = await self.create_access_token(user.id)
        refresh_token = await self.create_refresh_token(user.id)

        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        await self.db_manager.update_user(user)

        # 记录登录日志
        await self._log_login(user.id, "username", "success", None, client_ip, user_agent)

        logger.info(f"用户登录成功: {username}, user_id: {user.id}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": getattr(user, 'email', None),
                "phone": user.phone,
                "status": user.status,
                "role": user.role,
                "force_password_change": getattr(user, 'force_password_change', False),
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌"""
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")

        user_id = payload.get("user_id")
        user = await self.db_manager.get_user_by_id(user_id)
        if not user or user.status != "active":
            raise ValueError("用户不存在或已被禁用")

        # 生成新的访问令牌
        access_token = await self.create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        payload = self.decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("user_id")
        user = await self.db_manager.get_user_by_id(user_id)
        if not user or user.status != "active":
            return None

        return user

    async def verify_code(self, auth: UserAuth, code: str) -> bool:
        """验证验证码"""
        if not auth.verify_code:
            return False

        if auth.verify_code != code:
            return False

        if auth.verify_code_expiry and datetime.utcnow() > auth.verify_code_expiry:
            return False

        return True

    async def _log_login(
        self,
        user_id: Optional[str],
        login_type: str,
        status: str,
        fail_reason: Optional[str],
        client_ip: str,
        user_agent: str,
    ):
        """记录登录日志"""
        log = LoginLog(
            user_id=user_id,
            login_type=login_type,
            login_ip=client_ip,
            user_agent=user_agent,
            status=status,
            fail_reason=fail_reason,
        )
        await self.db_manager.create_login_log(log)


# 全局服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
