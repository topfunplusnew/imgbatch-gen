from src.models.image import ImageParams
from src.models.task import BatchTask, ImageTask, TaskStage, TaskStatus


def test_image_task_records_stage_history():
    task = ImageTask(
        task_id="task-1",
        params=ImageParams(prompt="test prompt"),
    )

    assert task.stage == TaskStage.REQUEST_RECEIVED
    assert len(task.stage_history) == 1

    task.update_status(TaskStatus.RUNNING)
    task.set_stage(
        TaskStage.SEMANTIC_UNDERSTANDING,
        message="正在进行语义理解与参数增强。",
        progress=0.2,
        attempt=1,
    )

    assert task.stage == TaskStage.SEMANTIC_UNDERSTANDING
    assert task.stage_label == "语义理解中"
    assert task.stage_message == "正在进行语义理解与参数增强。"
    assert task.progress == 0.2
    assert task.attempt == 1
    assert len(task.stage_history) == 2
    assert task.stage_history[-1].stage == TaskStage.SEMANTIC_UNDERSTANDING


def test_batch_task_aggregates_active_stage_detail():
    generating_task = ImageTask(
        task_id="task-generating",
        params=ImageParams(prompt="generate me"),
        status=TaskStatus.RUNNING,
    )
    generating_task.set_stage(
        TaskStage.GENERATING_IMAGES,
        message="正在调用 provider 执行生图请求。",
        progress=0.35,
        attempt=1,
    )

    semantic_task = ImageTask(
        task_id="task-semantic",
        params=ImageParams(prompt="understand me"),
        status=TaskStatus.RUNNING,
    )
    semantic_task.set_stage(
        TaskStage.SEMANTIC_UNDERSTANDING,
        message="正在进行语义理解与参数增强。",
        progress=0.18,
        attempt=1,
    )

    completed_task = ImageTask(
        task_id="task-completed",
        params=ImageParams(prompt="done"),
        status=TaskStatus.COMPLETED,
    )
    completed_task.set_stage(
        TaskStage.COMPLETED,
        message="任务已完成，共生成 1 张图片。",
        progress=1.0,
        attempt=1,
    )

    batch = BatchTask(batch_id="batch-1", tasks=[generating_task, semantic_task, completed_task])
    batch.update_progress()

    assert batch.status == TaskStatus.RUNNING
    assert batch.stage == TaskStage.GENERATING_IMAGES
    assert batch.completed == 1
    assert batch.running == 2
    assert batch.pending == 0
    assert batch.status_detail.current_stage == TaskStage.GENERATING_IMAGES.value
    assert "正在生图" in batch.status_detail.current_stage_message
    assert {item.stage: item.count for item in batch.status_detail.stage_overview} == {
        TaskStage.GENERATING_IMAGES.value: 1,
        TaskStage.SEMANTIC_UNDERSTANDING.value: 1,
        TaskStage.COMPLETED.value: 1,
    }


def test_batch_task_marks_failed_when_all_tasks_fail():
    failed_task = ImageTask(
        task_id="task-failed",
        params=ImageParams(prompt="fail me"),
        status=TaskStatus.FAILED,
    )
    failed_task.set_stage(
        TaskStage.FAILED,
        message="任务失败：provider error",
        progress=0.35,
        attempt=2,
    )

    batch = BatchTask(batch_id="batch-failed", tasks=[failed_task])
    batch.update_progress()

    assert batch.status == TaskStatus.FAILED
    assert batch.stage == TaskStage.FAILED
    assert batch.failed == 1
    assert batch.status_detail.current_stage == TaskStage.FAILED.value
