from types import SimpleNamespace

import pytest

from src.services.account_service import AccountService


class FakeDBManager:
    def __init__(self):
        self.account = SimpleNamespace(
            user_id="user-1",
            points=100,
            gift_points=0,
            balance=0,
            total_generated=0,
            total_spent=0,
        )
        self.transactions = []
        self.transaction_counter = 0

    async def get_account_by_user(self, user_id):
        if user_id != self.account.user_id:
            return None
        return self.account

    async def create_user_account(self, user_id):
        self.account.user_id = user_id
        return self.account

    async def update_account(self, account):
        self.account = account
        return account

    async def add_transaction(self, **kwargs):
        self.transaction_counter += 1
        tx = SimpleNamespace(
            id=f"tx-{self.transaction_counter}",
            user_id=kwargs["user_id"],
            transaction_type=kwargs["transaction_type"],
            amount=kwargs.get("amount", 0),
            points_change=kwargs.get("points_change", 0),
            description=kwargs.get("description", ""),
            related_request_id=kwargs.get("related_request_id"),
            apply_account_change=kwargs.get("apply_account_change", True),
        )
        self.transactions.append(tx)

        if kwargs.get("apply_account_change", True):
            self.account.balance += kwargs.get("amount", 0)
            self.account.points += kwargs.get("points_change", 0)

        return tx

    async def get_transaction_by_id(self, transaction_id):
        for tx in self.transactions:
            if tx.id == transaction_id:
                return tx
        return None

    async def create_consumption_record(self, **kwargs):
        return SimpleNamespace(**kwargs)


@pytest.mark.asyncio
async def test_freeze_and_settle_points_only_deduct_once(monkeypatch):
    service = AccountService()
    fake_db = FakeDBManager()
    service.db_manager = fake_db

    async def fake_get_model_price(model_name: str):
        return {"points": 33, "amount": 50}

    monkeypatch.setattr(service, "get_model_price", fake_get_model_price)

    freeze_result = await service.freeze_points(
        user_id="user-1",
        model_name="gemini-3.1-flash-image-preview",
        count=1,
        request_id="req-1",
    )

    assert freeze_result["status"] == "frozen"
    assert fake_db.account.points == 67
    assert fake_db.transactions[0].apply_account_change is False

    settle_result = await service.settle_frozen_points(
        user_id="user-1",
        freeze_id=freeze_result["freeze_id"],
        success=True,
        model_name="gemini-3.1-flash-image-preview",
        provider="google",
        request_id="task-1",
        prompt="生成一张海报",
        image_count=1,
        image_urls=["https://example.com/image.png"],
    )

    assert settle_result["status"] == "deducted"
    assert fake_db.account.points == 67
    assert settle_result["balance_after"]["points"] == 67
    assert fake_db.transactions[1].apply_account_change is False
