"""系统配置数据库模型"""

from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean
from datetime import datetime
from .base import Base, BaseModel


class SystemConfig(BaseModel):
    """系统配置表"""
    __tablename__ = "system_configs"

    # 配置基本信息
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment="配置键")
    config_value = Column(Text, nullable=True, comment="配置值（JSON字符串）")
    config_type = Column(String(50), default="string", comment="配置类型: string, number, boolean, json")
    category = Column(String(50), default="general", comment="配置分类: api, storage, general, etc")
    description = Column(Text, nullable=True, comment="配置说明")

    # 配置元数据
    is_encrypted = Column(Boolean, default=False, comment="是否加密存储")
    is_public = Column(Boolean, default=False, comment="是否公开（前端可读取）")

    # 更新信息
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    updated_by = Column(String(100), nullable=True, comment="更新者用户ID")

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key}, type={self.config_type})>"
