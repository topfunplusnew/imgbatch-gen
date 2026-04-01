"""用户认证相关数据库模型"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = "users"

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    phone = Column(String(20), unique=True, nullable=True, comment="手机号(可选)")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")

    # 状态信息
    status = Column(String(20), default="active", comment="状态: active, suspended, deleted")
    role = Column(String(20), default="user", comment="角色: user, admin")
    force_password_change = Column(Boolean, default=False, comment="是否强制修改密码")

    # 时间信息
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")

    # 关联关系
    auth_methods = relationship("UserAuth", back_populates="user", cascade="all, delete-orphan")
    account = relationship("Account", back_populates="user", uselist=False, cascade="all, delete-orphan",
                          foreign_keys="Account.user_id")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, phone={self.phone})>"


class UserAuth(BaseModel):
    """用户认证信息表"""
    __tablename__ = "user_auth"

    # 关联用户
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, comment="用户ID")
    user = relationship("User", back_populates="auth_methods")

    # 认证类型
    auth_type = Column(String(20), nullable=False, comment="认证类型: email, phone, oauth")
    auth_identifier = Column(String(255), nullable=False, comment="认证标识(邮箱/手机号/openid)")

    # 验证信息
    verified = Column(Boolean, default=False, comment="是否已验证")
    verify_code = Column(String(10), nullable=True, comment="验证码")
    verify_code_expiry = Column(DateTime, nullable=True, comment="验证码过期时间")

    # OAuth 信息(如果使用第三方登录)
    oauth_provider = Column(String(50), nullable=True, comment="OAuth提供商: wechat, github")
    oauth_openid = Column(String(255), nullable=True, comment="OAuth OpenID")
    oauth_unionid = Column(String(255), nullable=True, comment="OAuth UnionID(微信)")

    # 索引
    __table_args__ = (
        Index("ix_user_auth_type_identifier", "auth_type", "auth_identifier"),
    )

    def __repr__(self):
        return f"<UserAuth(id={self.id}, user_id={self.user_id}, type={self.auth_type})>"


class LoginLog(BaseModel):
    """登录日志表"""
    __tablename__ = "login_logs"

    # 用户信息
    user_id = Column(String(100), ForeignKey("users.id"), nullable=True, comment="用户ID(游客为NULL)")

    # 登录信息
    login_type = Column(String(20), comment="登录类型: email, phone, oauth")
    login_ip = Column(String(50), comment="登录IP")
    login_location = Column(String(100), comment="登录地点(可选)")
    user_agent = Column(String(500), comment="用户代理")

    # 状态信息
    status = Column(String(20), default="success", comment="状态: success, failed")
    fail_reason = Column(String(255), nullable=True, comment="失败原因")

    # 时间信息
    logout_at = Column(DateTime, nullable=True, comment="登出时间")

    def __repr__(self):
        return f"<LoginLog(id={self.id}, user_id={self.user_id}, status={self.status})>"
