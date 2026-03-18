"""任务模型定义"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .image import ImageParams, ImageResult


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageTask(BaseModel):
    """生图任务模型"""
    task_id: str = Field(..., description="任务ID")
    user_request_id: Optional[str] = Field(None, description="关联的用户请求ID")
    status: TaskStatus = Field(TaskStatus.PENDING, description="任务状态")
    params: ImageParams = Field(..., description="生图参数")
    result: Optional[List[ImageResult]] = Field(None, description="生成结果")
    images: Optional[List[Dict[str, Any]]] = Field(None, description="图像数据（兼容前端）")
    error: Optional[str] = Field(None, description="错误信息")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="进度（0-1）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任务元数据")

    def update_status(self, status: TaskStatus):
        """更新任务状态"""
        self.status = status
        if status == TaskStatus.RUNNING and not self.started_at:
            self.started_at = datetime.now()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = datetime.now()

    def to_response_dict(self) -> Dict[str, Any]:
        """转换为响应格式（包含images字段）"""
        response_data = {
            "task_id": self.task_id,
            "status": self.status,
            "params": self.params,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }

        # 如果有result，添加images字段
        if self.result:
            response_data["images"] = [
                {"url": img.url, "thumbnail_url": img.thumbnail_url or img.url, "alt": f"生成的图像"}
                for img in self.result
                if img.url
            ]

        return response_data


class BatchTask(BaseModel):
    """批量任务模型"""
    batch_id: str = Field(..., description="批量任务ID")
    user_request_id: Optional[str] = Field(None, description="关联的用户请求ID")
    tasks: List[ImageTask] = Field(default_factory=list, description="子任务列表")
    total: int = Field(0, description="总任务数")
    completed: int = Field(0, description="已完成数")
    failed: int = Field(0, description="失败数")
    status: TaskStatus = Field(TaskStatus.PENDING, description="批量任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    def update_progress(self):
        """更新批量任务进度"""
        self.completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        self.failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        
        if self.completed + self.failed == self.total:
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now()
        elif any(t.status == TaskStatus.RUNNING for t in self.tasks):
            self.status = TaskStatus.RUNNING
        elif any(t.status == TaskStatus.FAILED for t in self.tasks) and self.completed + self.failed == self.total:
            self.status = TaskStatus.FAILED


