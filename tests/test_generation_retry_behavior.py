from types import SimpleNamespace

import pytest

from src.config.settings import settings
from src.engine.worker import Worker
from src.models.image import ImageParams
from src.models.task import ImageTask, TaskStage, TaskStatus
from src.providers.openai_async_provider import OpenAIAsyncProvider
from src.providers.openai_relay_provider import OpenAIRelayProvider


class DummyStorage:
    pass


class DummyMetadataManager:
    def save_metadata(self, result, params):
        return None


class FlakyProvider:
    def __init__(self):
        self.calls = 0

    async def generate(self, params):
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("temporary timeout")
        return [b"image-bytes"]


@pytest.mark.asyncio
async def test_worker_retries_generation_immediately_without_sleep(monkeypatch):
    provider = FlakyProvider()
    worker = Worker(
        worker_id=1,
        storage=DummyStorage(),
        metadata_manager=DummyMetadataManager(),
    )
    task = ImageTask(
        task_id="task-retry-now",
        params=ImageParams(prompt="draw a cat"),
    )

    sleep_calls = []

    async def fake_sleep(delay):
        sleep_calls.append(delay)

    async def fake_get_provider(provider_name):
        return provider

    async def fake_enhance_params(self, task):
        return task

    async def fake_save_images(self, task, images):
        return [
            SimpleNamespace(
                url="https://example.com/image.png",
                file_path="/tmp/image.png",
            )
        ]

    async def fake_handle_success(self, task, results):
        return None

    async def fake_save_to_database(self, task, results):
        return None

    monkeypatch.setattr("src.engine.worker.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("src.engine.worker.get_provider", fake_get_provider)
    monkeypatch.setattr(Worker, "_enhance_params", fake_enhance_params)
    monkeypatch.setattr(Worker, "_save_images", fake_save_images)
    monkeypatch.setattr(Worker, "_handle_success", fake_handle_success)
    monkeypatch.setattr(Worker, "_save_to_database", fake_save_to_database)
    monkeypatch.setattr(settings, "max_generation_retries", 1)
    monkeypatch.setattr(settings, "generation_retry_base_delay", 0.0)
    monkeypatch.setattr(settings, "generation_retry_max_delay", 0.0)
    monkeypatch.setattr(settings, "default_image_provider", "openai")

    result = await worker.process_task(task)

    assert result.status == TaskStatus.COMPLETED
    assert provider.calls == 2
    assert sleep_calls == []
    retry_events = [event for event in result.stage_history if event.stage == TaskStage.RETRYING]
    assert retry_events
    assert "立即开始第 2 次重试" in retry_events[-1].message


def test_image_providers_default_to_zero_retry_delay():
    sync_provider = OpenAIRelayProvider()
    async_provider = OpenAIAsyncProvider()

    assert sync_provider.client.retry_base_delay == settings.generation_retry_base_delay == 0.0
    assert sync_provider.client.retry_max_delay == settings.generation_retry_max_delay == 0.0
    assert async_provider.client.retry_base_delay == settings.generation_retry_base_delay == 0.0
    assert async_provider.client.retry_max_delay == settings.generation_retry_max_delay == 0.0
