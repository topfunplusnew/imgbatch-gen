"""异步任务数据库模型"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Float, JSON
from datetime import datetime
from .base import Base

class AsyncTask(Base):
    """异步任务表"""
    __tablename__ = "async_tasks"

    id = Column(String(36), primary_key=True, comment="任务ID")
    platform_task_id = Column(String(200), index=True, comment="平台返回的任务ID")

    # 任务信息
    task_type = Column(String(50), default="image_generation", comment="任务类型")
    platform = Column(String(50), index=True, comment="平台名称")
    model = Column(String(100), comment="模型名称")

    # 任务参数
    prompt = Column(Text, comment="提示词")
    params = Column(JSON, comment="完整参数")

    # 任务状态
    status = Column(String(50), default="pending", index=True, comment="pending/processing/completed/failed")
    progress = Column(Float, default=0.0, comment="进度0-100")

    # 结果
    result_urls = Column(JSON, comment="结果图片URL列表")
    error = Column(Text, comment="错误信息")

    # 时间记录
    submit_time = Column(DateTime, default=datetime.now, comment="提交时间")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")

    # 元数据
    task_metadata = Column(JSON, comment="其他元数据")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
