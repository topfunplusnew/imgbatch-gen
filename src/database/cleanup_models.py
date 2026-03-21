"""数据保留清理相关数据库模型"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, BigInteger, Float, Text
from .base import Base, BaseModel
from datetime import datetime


class CleanupHistory(BaseModel):
    """清理操作历史记录表"""
    __tablename__ = "cleanup_history"

    # 配置信息
    retention_days = Column(Integer, comment="保留天数")
    cutoff_date = Column(DateTime, comment="截止日期")
    dry_run = Column(Boolean, default=False, comment="是否为dry-run")

    # 统计信息 - 数据库记录
    total_image_records_deleted = Column(Integer, default=0, comment="删除的图片记录数")
    total_chat_records_deleted = Column(Integer, default=0, comment="删除的对话记录数")
    total_user_requests_deleted = Column(Integer, default=0, comment="删除的用户请求数")

    # 统计信息 - 文件
    total_image_files_deleted = Column(Integer, default=0, comment="删除的图片文件数")
    total_storage_freed_bytes = Column(BigInteger, default=0, comment="释放的存储空间（字节）")

    # 错误信息
    error_count = Column(Integer, default=0, comment="错误数量")
    errors = Column(JSON, comment="错误列表")
    failed_image_deletions = Column(JSON, comment="失败的图片删除详情")

    # 执行信息
    triggered_by = Column(String(100), comment="触发者: scheduler/manual/startup")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration_seconds = Column(Float, comment="耗时（秒）")

    # 状态
    status = Column(String(20), default="running", comment="状态: running/completed/failed")

    def __repr__(self):
        return f"<CleanupHistory(id={self.id}, status={self.status}, retention_days={self.retention_days})>"
