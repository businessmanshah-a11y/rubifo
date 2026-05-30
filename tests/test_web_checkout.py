"""Tests for website login, checkout, and payment callback."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import app


class FakeCheckoutDb:
    def __init__(self):
        self.users = {
            "09123456789": {
                "id": 1,
                "user_id": "rubika-guid-1",
                "username": "testuser",
                "phone_number": "09123456789",
                "password_hash": "$2b$12$hBZ0oLaLcoSUqOfM8LoDcOd9AgREo8I62rBKKtPyKc9lvComqc8m6",
                "trial_start_at": datetime.now(),
                "trial_end_at": datetime.now() + timedelta(hours=72),
                "is_trial_active": True,
                "onboarding_completed_at": datetime.now(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        }
        self.transactions = {}
        self.subscriptions_created = 0
        self.completed_updates = 0

    async def fetchrow(self, query: str, *args):
        if "FROM users WHERE phone_number" in query:
            return self.users.get(args[0])
        if "FROM users WHERE user_id" in query:
            for user in self.users.values():
                if user["user_id"] == args[0]:
                    return user
            return None
        if "INSERT INTO transactions" in query:
            authority = args[4]
            row = {
                "id": 10,
                "user_id": args[0],
                "amount": args[1],
                "tier": args[2],
                "status": args[3],
                "authority": authority,
                "reference_id": None,
                "created_at": datetime.now(),
            }
            self.transactions[authority] = row
            return {"id": 10}
        if "FROM transactions WHERE authority" in query:
            return self.transactions.get(args[0])
        if "INSERT INTO subscriptions" in query:
            self.subscriptions_created += 1
            return {
                "id": self.subscriptions_created,
                "user_id": args[0],
                "tier": args[1],
                "start_date": args[2],
                "end_date": args[3],
                "is_active": True,
                "created_at": datetime.now(),
            }
        return None

    async def fetch(self, query: str, *args):
        return []

    async def fetchval(self, query: str, *args):
        return 0

    async def execute(self, query: str, *args):
        if "UPDATE transactions SET status" in query and "reference_id" in query:
            for row in self.transactions.values():
                if row["id"] == args[2]:
                    row["status"] = args[0]
                    row["reference_id"] = args[1]
                    self.completed_updates += 1
        elif "UPDATE transactions SET status" in query:
            for row in self.transactions.values():
                if row["id"] == args[1]:
                    row["status"] = args[0]
        return None


def test_user_login_returns_user_token():
    db = FakeCheckoutDb()
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        response = client.post(
            "/api/auth/login",
            json={"phone_number": "09123456789", "password": "secret123"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["user_id"] == "rubika-guid-1"


def test_checkout_start_creates_pending_transaction_and_returns_gateway_url():
    db = FakeCheckoutDb()
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        login = client.post(
            "/api/auth/login",
            json={"phone_number": "09123456789", "password": "secret123"},
        )
        token = login.json()["access_token"]

    with patch("app.db_module.pool", db):
        with patch("app.create_zarinpal_gateway") as gateway_factory:
            gateway = AsyncMock()
            gateway.request_payment.return_value = (
                True,
                "https://sandbox.zarinpal.com/pg/StartPay/AUTH123",
            )
            gateway_factory.return_value = gateway
            response = client.post(
                "/api/checkout/start",
                json={"tier": "basic"},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    assert response.json()["payment_url"].endswith("/AUTH123")
    assert db.transactions["AUTH123"]["status"] == "pending"
    assert db.transactions["AUTH123"]["user_id"] == "rubika-guid-1"


def test_payment_callback_completes_transaction_idempotently():
    db = FakeCheckoutDb()
    db.transactions["AUTH123"] = {
        "id": 10,
        "user_id": "rubika-guid-1",
        "amount": 1998000,
        "tier": "basic",
        "status": "pending",
        "authority": "AUTH123",
        "reference_id": None,
        "created_at": datetime.now(),
    }
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        with patch("app.create_zarinpal_gateway") as gateway_factory:
            gateway = AsyncMock()
            gateway.verify_payment.return_value = (True, "REF123")
            gateway_factory.return_value = gateway
            response = client.get("/payment/callback?Authority=AUTH123&Status=OK")
            second = client.get("/payment/callback?Authority=AUTH123&Status=OK")

    assert response.status_code == 200
    assert "REF123" in response.text
    assert second.status_code == 200
    assert db.transactions["AUTH123"]["status"] == "completed"
    assert db.subscriptions_created == 1
    assert db.completed_updates == 1
