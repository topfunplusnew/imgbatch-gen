from types import SimpleNamespace

import pytest

from src.api.routes import assistant


class FakeChatCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes[self.calls - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.chat = SimpleNamespace(completions=FakeChatCompletions(outcomes))
        self.base_url = "http://example.com/v1"
        self.api_key = "test-key"


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


@pytest.mark.asyncio
async def test_run_chat_completion_retries_invalid_token_then_succeeds():
    error = Exception("Error code: 401 - {'error': {'message': '无效的令牌', 'type': 'new_api_error'}}")
    client = FakeClient([error, error, FakeResponse("ok")])

    raw, used_model = await assistant._run_chat_completion(
        client,
        [{"role": "user", "content": "hello"}],
        "gpt-4o-mini",
    )

    assert used_model == "gpt-4o-mini"
    assert raw.choices[0].message.content == "ok"
    assert client.chat.completions.calls == 3


@pytest.mark.asyncio
async def test_run_chat_completion_returns_failure_after_all_invalid_token_retries():
    error = Exception("Error code: 401 - {'error': {'message': '无效的令牌', 'type': 'new_api_error'}}")
    client = FakeClient([error, error, error])

    with pytest.raises(Exception, match="401"):
        await assistant._run_chat_completion(
            client,
            [{"role": "user", "content": "hello"}],
            "gpt-4o-mini",
        )

    assert client.chat.completions.calls == 3


@pytest.mark.asyncio
async def test_refund_frozen_billing_helper_settles_points_back(monkeypatch):
    captured = {}

    class FakeAccountService:
        async def settle_frozen_points(self, **kwargs):
            captured.update(kwargs)
            return {
                "status": "refunded",
                "freeze_id": kwargs["freeze_id"],
                "balance_after": {"points": 100, "gift_points": 0, "balance": 0},
            }

    monkeypatch.setattr(assistant, "get_account_service", lambda: FakeAccountService())

    result = await assistant._refund_frozen_billing_if_needed(
        user_id="user-1",
        billing_info={"status": "frozen", "freeze_id": "freeze-1"},
        model_name="gemini-3.1-flash-image-preview",
        request_id="req-1",
        error_reason="task creation failed",
        provider="google",
    )

    assert result["status"] == "refunded"
    assert captured["user_id"] == "user-1"
    assert captured["freeze_id"] == "freeze-1"
    assert captured["success"] is False
