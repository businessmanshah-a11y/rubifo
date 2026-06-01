"""Tests for website login, checkout, and Zibal-compatible mock payment."""

from datetime import datetime, timedelta
from unittest.mock import patch

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


def test_landing_paid_plans_link_to_website_checkout():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/login?next=/checkout&tier=basic"' in response.text
    assert 'href="/login?next=/checkout&tier=pro"' in response.text
    assert 'href="/login?next=/checkout&tier=enterprise"' in response.text
    assert 'href="https://rubika.ir/rubifo_bot"' in response.text


def test_user_login_failure_explains_robot_registration():
    db = FakeCheckoutDb()
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        response = client.post(
            "/api/auth/login",
            json={"phone_number": "09120000000", "password": "secret123"},
        )

    assert response.status_code == 401
    assert "اول داخل ربات ثبت‌نام" in response.json()["detail"]


def test_checkout_page_routes_missing_token_to_login():
    client = TestClient(app)

    response = client.get("/checkout?tier=pro")

    assert response.status_code == 200
    assert "localStorage.getItem('rubifo_user_token')" in response.text
    assert "/login?next=/checkout&tier=" in response.text


def test_checkout_login_uses_landing_theme_tokens():
    client = TestClient(app)

    response = client.get("/login?next=/checkout&tier=pro")

    assert response.status_code == 200
    assert "rubifo-theme" in response.text
    assert "data-theme" in response.text
    assert "--black:" in response.text
    assert "--purple:" in response.text
    assert "--violet:" in response.text
    assert 'html[data-theme="light"]' in response.text
    assert "--accent: oklch(70% 0.185 55)" not in response.text


def test_checkout_page_rejects_invalid_tier_with_clear_message():
    client = TestClient(app)

    response = client.get("/checkout?tier=unknown")

    assert response.status_code == 200
    assert "پلن نامعتبر" in response.text
    assert "پلن‌های اشتراک" in response.text


def test_checkout_start_creates_pending_transaction_and_returns_zibal_mock_url():
    db = FakeCheckoutDb()
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        login = client.post(
            "/api/auth/login",
            json={"phone_number": "09123456789", "password": "secret123"},
        )
        token = login.json()["access_token"]

    with patch("app.db_module.pool", db):
        response = client.post(
            "/api/checkout/start",
            json={"tier": "basic"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "zibal_mock"
    assert payload["track_id"].startswith("RUBIFO-")
    assert payload["payment_url"].endswith(f"/mock/zibal/start/{payload['track_id']}")
    assert db.transactions[payload["track_id"]]["status"] == "pending"
    assert db.transactions[payload["track_id"]]["user_id"] == "rubika-guid-1"


def test_mock_zibal_page_exposes_success_failure_and_cancel_paths():
    client = TestClient(app)

    response = client.get("/mock/zibal/start/RUBIFO-123")

    assert response.status_code == 200
    assert "/payment/callback?trackId=RUBIFO-123&success=1" in response.text
    assert "/payment/callback?trackId=RUBIFO-123&success=0" in response.text
    assert "/payment/callback?trackId=RUBIFO-123&success=-1" in response.text


def test_payment_callback_completes_transaction_idempotently():
    db = FakeCheckoutDb()
    db.transactions["RUBIFO-123"] = {
        "id": 10,
        "user_id": "rubika-guid-1",
        "amount": 1998000,
        "tier": "basic",
        "status": "pending",
        "authority": "RUBIFO-123",
        "reference_id": None,
        "created_at": datetime.now(),
    }
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        response = client.get("/payment/callback?trackId=RUBIFO-123&success=1")
        second = client.get("/payment/callback?trackId=RUBIFO-123&success=1")

    assert response.status_code == 200
    assert "RUBIFO-123" in response.text
    assert "شروع در ربات" in response.text
    assert second.status_code == 200
    assert db.transactions["RUBIFO-123"]["status"] == "completed"
    assert db.subscriptions_created == 1
    assert db.completed_updates == 1


def test_payment_callback_failure_marks_transaction_failed_without_subscription():
    db = FakeCheckoutDb()
    db.transactions["RUBIFO-FAIL"] = {
        "id": 11,
        "user_id": "rubika-guid-1",
        "amount": 3998000,
        "tier": "pro",
        "status": "pending",
        "authority": "RUBIFO-FAIL",
        "reference_id": None,
        "created_at": datetime.now(),
    }
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        response = client.get("/payment/callback?trackId=RUBIFO-FAIL&success=0")

    assert response.status_code == 200
    assert "پرداخت ناموفق" in response.text
    assert db.transactions["RUBIFO-FAIL"]["status"] == "failed"
    assert db.subscriptions_created == 0


def test_payment_callback_cancel_marks_transaction_canceled_without_subscription():
    db = FakeCheckoutDb()
    db.transactions["RUBIFO-CANCEL"] = {
        "id": 12,
        "user_id": "rubika-guid-1",
        "amount": 9998000,
        "tier": "enterprise",
        "status": "pending",
        "authority": "RUBIFO-CANCEL",
        "reference_id": None,
        "created_at": datetime.now(),
    }
    client = TestClient(app)

    with patch("app.db_module.pool", db):
        response = client.get("/payment/callback?trackId=RUBIFO-CANCEL&success=-1")

    assert response.status_code == 200
    assert "پرداخت لغو شد" in response.text
    assert db.transactions["RUBIFO-CANCEL"]["status"] == "canceled"
    assert db.subscriptions_created == 0
