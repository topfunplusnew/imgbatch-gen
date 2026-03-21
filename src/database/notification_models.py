"""通知系统相关数据库模型"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, BaseModel


class Announcement(BaseModel):
    """系统公告表"""
    __tablename__ = "announcements"

    # 基本信息
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容（富文本HTML）")

    # 优先级和类型
    priority = Column(String(20), default="normal", index=True, comment="优先级: low, normal, high, urgent")
    announcement_type = Column(String(50), default="system", comment="公告类型: system, maintenance, feature, promotion")

    # 显示控制
    is_pinned = Column(Boolean, default=False, index=True, comment="是否置顶")
    is_published = Column(Boolean, default=True, index=True, comment="是否发布")

    # 时间控制
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    expires_at = Column(DateTime, nullable=True, index=True, comment="过期时间（可选）")

    # 图片附件
    cover_image_url = Column(String(500), comment="封面图片URL")
    cover_image_path = Column(String(500), comment="封面图片存储路径")

    # 目标受众
    target_audience = Column(String(50), default="all", comment="目标受众: all, users_only, admins_only")

    # 统计
    view_count = Column(Integer, default=0, comment="浏览次数")
    click_count = Column(Integer, default=0, comment="点击次数")

    # 创建者
    created_by = Column(String(100), comment="创建者ID（管理员）")
    updated_by = Column(String(100), comment="更新者ID（管理员）")

    # 关联用户通知记录
    user_notifications = relationship("UserNotification", back_populates="announcement", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('ix_announcements_priority_pinned', 'priority', 'is_pinned'),
        Index('ix_announcements_published_expires', 'is_published', 'expires_at'),
    )

    def __repr__(self):
        return f"<Announcement(id={self.id}, title={self.title}, priority={self.priority})>"

    def to_dict(self):
        """转换为字典，包含用户友好的字段"""
        data = super().to_dict()
        # 添加过期状态
        if self.expires_at:
            data['is_expired'] = datetime.utcnow() > self.expires_at
        else:
            data['is_expired'] = False
        return data


class UserNotification(BaseModel):
    """用户通知读取记录表"""
    __tablename__ = "user_notifications"

    # 关联公告
    announcement_id = Column(String(36), ForeignKey("announcements.id"), nullable=False, index=True)
    announcement = relationship("Announcement", back_populates="user_notifications")

    # 用户信息
    user_id = Column(String(100), nullable=False, index=True, comment="用户ID")

    # 读取状态
    is_read = Column(Boolean, default=False, index=True, comment="是否已读")
    read_at = Column(DateTime, comment="读取时间")

    # 交互记录
    is_clicked = Column(Boolean, default=False, comment="是否点击查看详情")
    clicked_at = Column(DateTime, comment="点击时间")

    # 通知推送状态
    is_pushed = Column(Boolean, default=False, comment="是否已推送")
    pushed_at = Column(DateTime, comment="推送时间")
    push_method = Column(String(20), comment="推送方式: sse, email, sms")

    # 唯一约束（一个用户对一个公告只有一条记录）
    __table_args__ = (
        UniqueConstraint('announcement_id', 'user_id', name='unique_user_announcement'),
        Index('ix_user_notifications_user_read', 'user_id', 'is_read'),
        Index('ix_user_notifications_announcement_read', 'announcement_id', 'is_read'),
    )

    def __repr__(self):
        return f"<UserNotification(id={self.id}, user_id={self.user_id}, announcement_id={self.announcement_id}, is_read={self.is_read})>"
