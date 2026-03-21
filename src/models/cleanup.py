"""数据保留清理模型定义"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CleanupReport(BaseModel):
    """清理操作报告"""

    # 配置信息
    retention_days: int = Field(..., description="保留天数")
    cutoff_date: datetime = Field(..., description="截止日期")
    dry_run: bool = Field(default=False, description="是否为dry-run模式")

    # 统计信息 - 数据库记录
    total_image_records_deleted: int = Field(default=0, description="删除的图片记录数")
    total_chat_records_deleted: int = Field(default=0, description="删除的对话记录数")
    total_user_requests_deleted: int = Field(default=0, description="删除的用户请求数")

    # 统计信息 - 文件
    total_image_files_deleted: int = Field(default=0, description="删除的图片文件数")
    total_storage_freed_bytes: int = Field(default=0, description="释放的存储空间（字节）")

    # 错误信息
    errors: List[str] = Field(default_factory=list, description="错误列表")
    failed_image_deletions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="失败的图片删除详情"
    )

    # 执行信息
    triggered_by: str = Field(default="scheduler", description="触发者: scheduler/manual/startup")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    duration_seconds: float = Field(default=0.0, description="耗时（秒）")

    # 状态
    status: str = Field(default="running", description="状态: running/completed/failed")

    def mark_completed(self):
        """标记为完成"""
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.status = "completed"

    def mark_failed(self, error: str):
        """标记为失败"""
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.status = "failed"
        self.errors.append(error)

    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)

    def add_failed_deletion(self, image_id: str, error: str, storage_type: str = "unknown"):
        """添加失败的删除记录"""
        self.failed_image_deletions.append({
            "image_id": image_id,
            "error": error,
            "storage_type": storage_type,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_storage_freed_mb(self) -> float:
        """获取释放的存储空间（MB）"""
        return self.total_storage_freed_bytes / (1024 * 1024)

    def get_storage_freed_gb(self) -> float:
        """获取释放的存储空间（GB）"""
        return self.get_storage_freed_mb() / 1024

    class Config:
        json_schema_extra = {
            "example": {
                "retention_days": 90,
                "cutoff_date": "2025-12-21T00:00:00",
                "dry_run": False,
                "total_image_records_deleted": 150,
                "total_chat_records_deleted": 300,
                "total_user_requests_deleted": 50,
                "total_image_files_deleted": 150,
                "total_storage_freed_bytes": 2684354560,
                "errors": [],
                "failed_image_deletions": [],
                "triggered_by": "scheduler",
                "status": "completed"
            }
        }


class CleanupStatus(BaseModel):
    """清理任务状态"""

    # 调度器状态
    scheduler_running: bool = Field(..., description="调度器是否运行中")
    cleanup_interval_hours: int = Field(..., description="清理间隔（小时）")
    retention_days: int = Field(..., description="保留天数")

    # 最近一次清理信息
    last_cleanup_time: Optional[datetime] = Field(default=None, description="最近一次清理时间")
    last_cleanup_status: Optional[str] = Field(default=None, description="最近一次清理状态")
    last_cleanup_records_deleted: Optional[int] = Field(default=None, description="最近一次清理删除的记录数")
    last_cleanup_storage_freed: Optional[int] = Field(default=None, description="最近一次清理释放的存储空间（字节）")

    # 下一次清理信息
    next_cleanup_time: Optional[datetime] = Field(default=None, description="下一次清理时间")

    # 配置信息
    cleanup_dry_run: bool = Field(default=False, description="是否启用dry-run模式")
    cleanup_on_startup: bool = Field(default=False, description="是否在启动时运行清理")

    class Config:
        json_schema_extra = {
            "example": {
                "scheduler_running": True,
                "cleanup_interval_hours": 24,
                "retention_days": 90,
                "last_cleanup_time": "2025-03-20T02:00:00",
                "last_cleanup_status": "completed",
                "last_cleanup_records_deleted": 150,
                "last_cleanup_storage_freed": 2684354560,
                "next_cleanup_time": "2025-03-21T02:00:00",
                "cleanup_dry_run": False,
                "cleanup_on_startup": False
            }
        }
