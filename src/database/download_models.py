"""下载记录相关数据库模型"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from datetime import datetime
from .base import Base, BaseModel


class DownloadRecord(BaseModel):
    """下载记录表"""
    __tablename__ = "download_records"

    # 关联用户
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")

    # 图片信息
    image_url = Column(Text, comment="图片URL")
    file_name = Column(String(255), comment="下载文件名")
    file_size = Column(Integer, comment="文件大小(字节)")

    # 关联信息
    request_id = Column(String(100), comment="关联请求ID")
    consumption_record_id = Column(String(100), ForeignKey("consumption_records.id"), comment="关联消费记录ID")

    # 客户端信息
    download_ip = Column(String(50), comment="下载IP")
    user_agent = Column(String(500), comment="用户代理")

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="下载时间")

    def __repr__(self):
        return f"<DownloadRecord(id={self.id}, user_id={self.user_id}, file_name={self.file_name})>"
