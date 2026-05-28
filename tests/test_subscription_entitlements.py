"""Tests for subscription entitlement decisions."""

from datetime import timedelta

import pytest

from src.config import SUBSCRIPTION_TIERS
from src.core.subscription_service import SubscriptionService
from src.utils import now_tehran


@pytest.mark.asyncio
async def test_access_state_trial_when_trial_is_active(mock_db):
    service = SubscriptionService(mock_db)
    mock_db.fetchrow.side_effect = [
        None,
        {"is_trial_active": True, "trial_end_at": now_tehran() + timedelta(hours=6)},
        None,
        {"is_trial_active": True, "trial_end_at": now_tehran() + timedelta(hours=6)},
    ]

    assert await service.get_access_state("u1") == "trial"
    assert await service.can_use_professional_plans("u1") is False


@pytest.mark.asyncio
async def test_access_state_expired_when_trial_has_ended(mock_db):
    service = SubscriptionService(mock_db)
    mock_db.fetchrow.side_effect = [
        None,
        {"is_trial_active": True, "trial_end_at": now_tehran() - timedelta(minutes=1)},
        None,
        {"is_trial_active": True, "trial_end_at": now_tehran() - timedelta(minutes=1)},
    ]

    assert await service.get_access_state("u1") == "expired"
    assert await service.get_destination_limit("u1") == 0


@pytest.mark.asyncio
async def test_access_state_paid_when_subscription_is_active(mock_db, sample_subscription_data):
    service = SubscriptionService(mock_db)
    mock_db.fetchrow.return_value = sample_subscription_data | {"tier": "pro"}

    assert await service.get_access_state("u1") == "paid"
    assert await service.is_paid("u1") is True
    assert await service.can_use_professional_plans("u1") is True
    assert await service.get_destination_limit("u1") == 3


def test_subscription_tier_prices_and_limits():
    assert SUBSCRIPTION_TIERS["basic"]["display_name_fa"] == "شروع حرفه‌ای"
    assert SUBSCRIPTION_TIERS["basic"]["price_monthly"] == 1998000
    assert SUBSCRIPTION_TIERS["basic"]["max_destinations"] == 1
    assert SUBSCRIPTION_TIERS["pro"]["display_name_fa"] == "رشد"
    assert SUBSCRIPTION_TIERS["pro"]["price_monthly"] == 3998000
    assert SUBSCRIPTION_TIERS["pro"]["max_destinations"] == 3
    assert SUBSCRIPTION_TIERS["enterprise"]["display_name_fa"] == "مقیاس"
    assert SUBSCRIPTION_TIERS["enterprise"]["price_monthly"] == 9998000
    assert SUBSCRIPTION_TIERS["enterprise"]["max_destinations"] == 10
