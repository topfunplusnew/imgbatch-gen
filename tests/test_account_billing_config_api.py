import pytest

from src.api.routes import account as account_routes


@pytest.mark.asyncio
async def test_public_billing_config_exposes_plans_and_recharge_options(monkeypatch):
    fake_config = {
        "billing": {"mode": "hybrid"},
        "initial_quota": {"free_generations": 10},
        "recharge_options": {
            "options": [
                {"id": "recharge_1", "amount_yuan": 1, "points": 100},
            ]
        },
        "subscription_plans": {
            "plans": [
                {"id": "plus", "name": "Plus", "monthly_price": 9900},
            ]
        },
        "limits": {"order_expire_minutes": 30},
    }
    monkeypatch.setattr(account_routes, "get_billing_config", lambda: fake_config)

    result = await account_routes.get_billing_config_info(user={})

    assert result["billing"] == fake_config["billing"]
    assert result["initial_quota"] == fake_config["initial_quota"]
    assert result["recharge_options"] == fake_config["recharge_options"]
    assert result["subscription_plans"] == fake_config["subscription_plans"]
    assert result["limits"] == fake_config["limits"]


@pytest.mark.asyncio
async def test_public_subscription_plans_endpoint_exposes_configured_plans(monkeypatch):
    fake_config = {
        "subscription_plans": {
            "plans": [
                {
                    "id": "plus",
                    "name": "Plus",
                    "icon": "bolt",
                    "badge": "最受欢迎",
                    "monthly_price": 9900,
                    "yearly_price": 99900,
                    "points_per_month": 150,
                    "features": ["优先支持"],
                    "color": "amber",
                },
            ]
        }
    }
    monkeypatch.setattr(account_routes, "get_billing_config", lambda: fake_config)

    result = await account_routes.get_subscription_plans(user={})

    assert len(result) == 1
    assert result[0].id == "plus"
    assert result[0].monthly_price == 9900
    assert result[0].features == ["优先支持"]
