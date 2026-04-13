from types import SimpleNamespace

import pytest

from src.api.routes import payment as payment_routes


class FakePaymentService:
    def __init__(self):
        self.created_orders = []
        self.updated_orders = []

    async def create_order(self, **kwargs):
        self.created_orders.append(kwargs)
        return SimpleNamespace(
            order_id="PAY123",
            user_id=kwargs["user_id"],
            order_type=kwargs["order_type"],
            amount=kwargs["amount"],
            payment_method=kwargs["payment_method"],
            status="pending",
            subject=kwargs["subject"],
            created_at=None,
            expire_time=None,
        )

    async def update_order_payment_info(self, **kwargs):
        self.updated_orders.append(kwargs)
        return None

    async def cancel_order(self, order_id):
        return None


@pytest.mark.asyncio
async def test_create_subscription_order_uses_configured_yearly_pricing(monkeypatch):
    fake_service = FakePaymentService()
    monkeypatch.setattr(payment_routes, "get_payment_service", lambda: fake_service)
    monkeypatch.setattr(
        payment_routes,
        "_get_subscription_plan_config",
        lambda plan_id: {
            "id": plan_id,
            "name": "Plus",
            "monthly_price": 9900,
            "yearly_price": 99900,
            "points_per_month": 150,
        },
    )

    async def fake_create_native_payment(order):
        return "weixin://pay/mock", None, "prepay_mock"

    monkeypatch.setattr(payment_routes, "_create_native_payment", fake_create_native_payment)

    body = payment_routes.CreateSubscriptionOrderRequest(
        plan_id="plus",
        billing_cycle="yearly",
        payment_method="wechat",
    )
    result = await payment_routes.create_subscription_order(
        request=None,
        body=body,
        user={"id": "user-1"},
    )

    assert result.order_type == "subscription"
    assert result.amount == 99900
    assert result.amount_yuan == 999
    assert result.qr_code_url == "weixin://pay/mock"

    created_order = fake_service.created_orders[0]
    assert created_order["plan_id"] == "plus"
    assert created_order["amount"] == 99900
    assert created_order["attach"]["billing_cycle"] == "yearly"
    assert created_order["attach"]["duration_days"] == 365
    assert created_order["attach"]["points_included"] == 1800

    updated_order = fake_service.updated_orders[0]
    assert updated_order["order_id"] == "PAY123"
    assert updated_order["prepay_id"] == "prepay_mock"
