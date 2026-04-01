"""任务模型定义"""

from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from .image import ImageParams, ImageResult


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStage(str, Enum):
    """任务处理阶段枚举"""

    REQUEST_RECEIVED = "request_received"
    QUEUED = "queued"
    EXTRACTING_PROMPT = "extracting_prompt"
    SEMANTIC_UNDERSTANDING = "semantic_understanding"
    GENERATING_IMAGES = "generating_images"
    VALIDATING_IMAGES = "validating_images"
    SAVING_IMAGES = "saving_images"
    RECORDING_RESULT = "recording_result"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"


TASK_STAGE_LABELS: Dict[TaskStage, str] = {
    TaskStage.REQUEST_RECEIVED: "请求已接收",
    TaskStage.QUEUED: "排队中",
    TaskStage.EXTRACTING_PROMPT: "提示词提取中",
    TaskStage.SEMANTIC_UNDERSTANDING: "语义理解中",
    TaskStage.GENERATING_IMAGES: "生图请求中",
    TaskStage.VALIDATING_IMAGES: "结果校验中",
    TaskStage.SAVING_IMAGES: "图片保存中",
    TaskStage.RECORDING_RESULT: "结果记录中",
    TaskStage.RETRYING: "重试等待中",
    TaskStage.COMPLETED: "已完成",
    TaskStage.FAILED: "失败",
}


TASK_STAGE_DEFAULT_MESSAGES: Dict[TaskStage, str] = {
    TaskStage.REQUEST_RECEIVED: "请求已接收，等待进入任务队列。",
    TaskStage.QUEUED: "任务已进入队列，等待工作线程处理。",
    TaskStage.EXTRACTING_PROMPT: "正在从输入内容中提取可执行提示词。",
    TaskStage.SEMANTIC_UNDERSTANDING: "正在进行语义理解和参数增强。",
    TaskStage.GENERATING_IMAGES: "正在调用生图模型生成图片。",
    TaskStage.VALIDATING_IMAGES: "正在校验返回的图片结果。",
    TaskStage.SAVING_IMAGES: "正在保存图片与元数据。",
    TaskStage.RECORDING_RESULT: "正在记录结果并更新关联数据。",
    TaskStage.RETRYING: "任务处理中断，正在等待下一次重试。",
    TaskStage.COMPLETED: "任务已完成，图片已可查看。",
    TaskStage.FAILED: "任务执行失败。",
}


BATCH_STAGE_PRIORITY: List[TaskStage] = [
    TaskStage.GENERATING_IMAGES,
    TaskStage.SAVING_IMAGES,
    TaskStage.VALIDATING_IMAGES,
    TaskStage.RECORDING_RESULT,
    TaskStage.SEMANTIC_UNDERSTANDING,
    TaskStage.EXTRACTING_PROMPT,
    TaskStage.RETRYING,
    TaskStage.QUEUED,
    TaskStage.REQUEST_RECEIVED,
]


def _normalize_stage(stage: TaskStage | str) -> TaskStage:
    if isinstance(stage, TaskStage):
        return stage
    return TaskStage(str(stage))


def get_stage_label(stage: TaskStage | str) -> str:
    normalized_stage = _normalize_stage(stage)
    return TASK_STAGE_LABELS.get(normalized_stage, normalized_stage.value)


def get_stage_default_message(stage: TaskStage | str) -> str:
    normalized_stage = _normalize_stage(stage)
    return TASK_STAGE_DEFAULT_MESSAGES.get(normalized_stage, normalized_stage.value)


def _isoformat(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")


def _sanitize_for_response(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _isoformat(value)
    if isinstance(value, BaseModel):
        return _sanitize_for_response(value.model_dump())
    if isinstance(value, dict):
        sanitized: Dict[str, Any] = {}
        for key, item in value.items():
            cleaned = _sanitize_for_response(item)
            if cleaned is not None:
                sanitized[key] = cleaned
        return sanitized
    if isinstance(value, list):
        sanitized_list: List[Any] = []
        for item in value:
            cleaned = _sanitize_for_response(item)
            if cleaned is not None:
                sanitized_list.append(cleaned)
        return sanitized_list
    if isinstance(value, tuple):
        sanitized_tuple: List[Any] = []
        for item in value:
            cleaned = _sanitize_for_response(item)
            if cleaned is not None:
                sanitized_tuple.append(cleaned)
        return sanitized_tuple
    return value


class TaskStageEvent(BaseModel):
    """单个任务阶段事件"""

    stage: TaskStage = Field(..., description="阶段代码")
    label: str = Field(..., description="阶段显示名称")
    message: str = Field(..., description="阶段说明")
    status: TaskStatus = Field(..., description="事件发生时的任务状态")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="事件发生时的进度")
    attempt: int = Field(0, description="对应尝试次数")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间")


class BatchStageOverviewItem(BaseModel):
    """批量任务的阶段分布摘要"""

    stage: str = Field(..., description="阶段代码")
    label: str = Field(..., description="阶段显示名称")
    count: int = Field(..., description="该阶段任务数")


class BatchStatusDetail(BaseModel):
    """批量任务的聚合状态详情"""

    current_stage: str = Field("", description="当前批量阶段代码")
    current_stage_label: str = Field("", description="当前批量阶段名称")
    current_stage_message: str = Field("", description="当前批量阶段说明")
    progress_percent: int = Field(0, description="整体进度百分比")
    pending_tasks: int = Field(0, description="待处理任务数")
    running_tasks: int = Field(0, description="运行中任务数")
    completed_tasks: int = Field(0, description="已完成任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    stage_overview: List[BatchStageOverviewItem] = Field(default_factory=list, description="阶段分布")


class ImageTask(BaseModel):
    """生图任务模型"""
    task_id: str = Field(..., description="任务ID")
    user_id: Optional[str] = Field(None, description="用户ID")
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
    updated_at: datetime = Field(default_factory=datetime.now, description="最近状态更新时间")
    stage: TaskStage = Field(TaskStage.REQUEST_RECEIVED, description="当前处理阶段")
    stage_label: str = Field(TASK_STAGE_LABELS[TaskStage.REQUEST_RECEIVED], description="阶段显示名称")
    stage_message: str = Field(
        TASK_STAGE_DEFAULT_MESSAGES[TaskStage.REQUEST_RECEIVED],
        description="阶段说明",
    )
    attempt: int = Field(0, description="当前尝试次数")
    stage_history: List[TaskStageEvent] = Field(default_factory=list, description="阶段事件历史")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任务元数据")

    def model_post_init(self, __context: Any) -> None:
        self.stage_label = get_stage_label(self.stage)
        if not self.stage_message:
            self.stage_message = get_stage_default_message(self.stage)
        if not self.stage_history:
            self.stage_history.append(
                TaskStageEvent(
                    stage=self.stage,
                    label=self.stage_label,
                    message=self.stage_message,
                    status=self.status,
                    progress=self.progress,
                    attempt=self.attempt,
                    timestamp=self.updated_at,
                )
            )

    def update_status(self, status: TaskStatus):
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.now()
        if status == TaskStatus.RUNNING and not self.started_at:
            self.started_at = self.updated_at
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = self.updated_at

    def set_stage(
        self,
        stage: TaskStage | str,
        *,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        attempt: Optional[int] = None,
    ) -> None:
        """设置任务处理阶段并记录事件。"""

        normalized_stage = _normalize_stage(stage)
        next_message = (message or get_stage_default_message(normalized_stage)).strip()
        next_progress = self.progress if progress is None else max(0.0, min(1.0, float(progress)))
        next_attempt = self.attempt if attempt is None else max(0, int(attempt))

        stage_changed = (
            self.stage != normalized_stage
            or self.stage_message != next_message
            or self.progress != next_progress
            or self.attempt != next_attempt
        )

        self.stage = normalized_stage
        self.stage_label = get_stage_label(normalized_stage)
        self.stage_message = next_message
        self.progress = next_progress
        self.attempt = next_attempt
        self.updated_at = datetime.now()

        if stage_changed:
            self.stage_history.append(
                TaskStageEvent(
                    stage=self.stage,
                    label=self.stage_label,
                    message=self.stage_message,
                    status=self.status,
                    progress=self.progress,
                    attempt=self.attempt,
                    timestamp=self.updated_at,
                )
            )

    def to_response_dict(self) -> Dict[str, Any]:
        """转换为响应格式（包含images字段）"""
        params_data = _sanitize_for_response(self.params.model_dump())
        metadata_data = _sanitize_for_response(self.metadata)
        response_data = {
            "task_id": self.task_id,
            "status": self.status.value,
            "params": params_data,
            "result": _sanitize_for_response(self.result),
            "error": self.error,
            "progress": self.progress,
            "created_at": _isoformat(self.created_at),
            "started_at": _isoformat(self.started_at),
            "completed_at": _isoformat(self.completed_at),
            "updated_at": _isoformat(self.updated_at),
            "stage": self.stage.value,
            "stage_label": self.stage_label,
            "stage_message": self.stage_message,
            "attempt": self.attempt,
            "stage_history": [
                {
                    "stage": event.stage.value,
                    "label": event.label,
                    "message": event.message,
                    "status": event.status.value,
                    "progress": event.progress,
                    "attempt": event.attempt,
                    "timestamp": _isoformat(event.timestamp),
                }
                for event in self.stage_history
            ],
            "metadata": metadata_data
        }

        # 如果有result，添加images字段
        if self.result:
            response_data["images"] = [
                {"url": img.url, "thumbnail_url": img.thumbnail_url or img.url, "alt": f"生成的图像"}
                for img in self.result
                if img.url
            ]

        # 添加计费信息
        billing_result = self.metadata.get("billing_result")
        if billing_result:
            response_data["billing"] = billing_result

        return response_data


class BatchTask(BaseModel):
    """批量任务模型"""
    batch_id: str = Field(..., description="批量任务ID")
    user_request_id: Optional[str] = Field(None, description="关联的用户请求ID")
    tasks: List[ImageTask] = Field(default_factory=list, description="子任务列表")
    total: int = Field(0, description="总任务数")
    completed: int = Field(0, description="已完成数")
    failed: int = Field(0, description="失败数")
    pending: int = Field(0, description="待处理任务数")
    running: int = Field(0, description="运行中任务数")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="整体进度（0-1）")
    status: TaskStatus = Field(TaskStatus.PENDING, description="批量任务状态")
    stage: TaskStage = Field(TaskStage.REQUEST_RECEIVED, description="当前批量阶段")
    stage_label: str = Field(TASK_STAGE_LABELS[TaskStage.REQUEST_RECEIVED], description="批量阶段显示名称")
    stage_message: str = Field(
        "批量任务已创建，等待进入处理流程。",
        description="批量阶段说明",
    )
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最近状态更新时间")
    status_detail: BatchStatusDetail = Field(default_factory=BatchStatusDetail, description="批量状态详情")

    def _pick_current_stage(self, stage_counter: Counter[TaskStage]) -> TaskStage:
        if self.total > 0 and self.completed >= self.total and self.failed == 0:
            return TaskStage.COMPLETED
        if self.total > 0 and self.completed + self.failed >= self.total and self.completed == 0:
            return TaskStage.FAILED
        for stage in BATCH_STAGE_PRIORITY:
            if stage_counter.get(stage, 0) > 0:
                return stage
        if self.completed > 0 and self.completed + self.failed >= self.total:
            return TaskStage.COMPLETED
        if self.failed > 0 and self.completed == 0 and self.completed + self.failed >= self.total:
            return TaskStage.FAILED
        return TaskStage.QUEUED if self.total else TaskStage.REQUEST_RECEIVED

    def _build_stage_message(self, current_stage: TaskStage, stage_counter: Counter[TaskStage]) -> str:
        count = stage_counter.get(current_stage, 0)
        if current_stage == TaskStage.QUEUED:
            return f"正在排队：{count} 个任务等待处理，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.EXTRACTING_PROMPT:
            return f"正在提取提示词：{count} 个任务分析输入内容，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.SEMANTIC_UNDERSTANDING:
            return f"正在语义理解：{count} 个任务进行语义分析，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.GENERATING_IMAGES:
            return f"正在生图：{count} 个任务调用模型生成图片，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.VALIDATING_IMAGES:
            return f"正在校验结果：{count} 个任务检查图片返回内容，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.SAVING_IMAGES:
            return f"正在保存图片：{count} 个任务写入存储，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.RECORDING_RESULT:
            return f"正在记录结果：{count} 个任务回写结果数据，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.RETRYING:
            return f"正在等待重试：{count} 个任务准备再次执行，已完成 {self.completed}/{self.total}。"
        if current_stage == TaskStage.COMPLETED:
            if self.failed > 0:
                return f"批量任务已结束：成功 {self.completed}，失败 {self.failed}。"
            return f"批量任务已完成：共成功生成 {self.completed} 张图片。"
        if current_stage == TaskStage.FAILED:
            return f"批量任务失败：{self.failed} 个任务执行失败。"
        return "批量任务已创建，等待进入处理流程。"

    def update_progress(self):
        """刷新批量任务进度和聚合状态。"""

        self.total = len(self.tasks)
        self.completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        self.failed = sum(1 for t in self.tasks if t.status in {TaskStatus.FAILED, TaskStatus.CANCELLED})
        self.running = sum(1 for t in self.tasks if t.status == TaskStatus.RUNNING)
        self.pending = max(self.total - self.completed - self.failed - self.running, 0)

        terminal_count = self.completed + self.failed
        self.progress = (terminal_count / self.total) if self.total else 0.0

        if self.total == 0:
            self.status = TaskStatus.PENDING
        elif terminal_count >= self.total:
            self.status = TaskStatus.COMPLETED if self.completed > 0 else TaskStatus.FAILED
            if not self.completed_at:
                self.completed_at = datetime.now()
        elif self.running > 0 or terminal_count > 0:
            self.status = TaskStatus.RUNNING
        else:
            self.status = TaskStatus.PENDING
            self.completed_at = None

        stage_counter: Counter[TaskStage] = Counter(task.stage for task in self.tasks)
        current_stage = self._pick_current_stage(stage_counter)
        self.stage = current_stage
        self.stage_label = get_stage_label(current_stage)
        self.stage_message = self._build_stage_message(current_stage, stage_counter)
        self.updated_at = datetime.now()
        self.status_detail = BatchStatusDetail(
            current_stage=self.stage.value,
            current_stage_label=self.stage_label,
            current_stage_message=self.stage_message,
            progress_percent=int(round(self.progress * 100)),
            pending_tasks=self.pending,
            running_tasks=self.running,
            completed_tasks=self.completed,
            failed_tasks=self.failed,
            stage_overview=[
                BatchStageOverviewItem(
                    stage=stage.value,
                    label=get_stage_label(stage),
                    count=count,
                )
                for stage in BATCH_STAGE_PRIORITY + [TaskStage.COMPLETED, TaskStage.FAILED]
                for count in [stage_counter.get(stage, 0)]
                if count > 0
            ],
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """转换为安全的批量任务响应格式。"""
        return {
            "batch_id": self.batch_id,
            "user_request_id": self.user_request_id,
            "tasks": [task.to_response_dict() for task in self.tasks],
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "pending": self.pending,
            "running": self.running,
            "progress": self.progress,
            "status": self.status.value,
            "stage": self.stage.value,
            "stage_label": self.stage_label,
            "stage_message": self.stage_message,
            "created_at": _isoformat(self.created_at),
            "completed_at": _isoformat(self.completed_at),
            "updated_at": _isoformat(self.updated_at),
            "status_detail": _sanitize_for_response(self.status_detail),
        }
