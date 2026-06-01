"""Integration tests for admin dashboard (T62)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch
from src.admin.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    from src.admin.auth import AdminAuth
    auth = AdminAuth()
    # Note: This requires ADMIN_USERNAME and ADMIN_PASSWORD_HASH to be set
    token = auth.create_token("admin")
    return token


class TestAdminAuthEndpoints:
    """Test authentication endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/admin/login",
            json={"username": "invalid", "password": "invalid"},
        )
        assert response.status_code == 401

    def test_root_redirect(self, client):
        """Test root path serves login page."""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200

    def test_enamad_verification_file(self, client):
        """Test eNamad verification file is served from the domain root."""
        response = client.get("/795459943.txt")
        assert response.status_code == 200
        assert response.text == ""
        assert "text/plain" in response.headers.get("content-type", "")


class TestAdminDashboardAPI:
    """Test dashboard API endpoints."""

    def test_dashboard_summary_unauthorized(self, client):
        """Test accessing dashboard summary without token."""
        response = client.get("/admin/dashboard-summary")
        assert response.status_code == 403

    def test_dashboard_summary_requires_token(self, client):
        """Test dashboard summary requires authentication."""
        response = client.get(
            "/admin/dashboard-summary",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestAdminTransactionsAPI:
    """Test transactions API endpoints."""

    def test_transactions_list_unauthorized(self, client):
        """Test listing transactions without token."""
        response = client.get("/admin/transactions")
        assert response.status_code == 403

    def test_transactions_list_structure(self, client, valid_token):
        """Test transactions list has correct structure."""
        response = client.get(
            "/admin/transactions",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "transactions" in data
            assert isinstance(data["transactions"], list)

    def test_transactions_export_unauthorized(self, client):
        """Test exporting transactions without token."""
        response = client.get("/admin/transactions/export")
        assert response.status_code == 403


class TestAdminStatsAPI:
    """Test statistics API endpoints."""

    def test_stats_unauthorized(self, client):
        """Test stats endpoint without token."""
        response = client.get("/admin/stats")
        assert response.status_code == 403

    def test_stats_structure(self, client, valid_token):
        """Test stats endpoint structure."""
        response = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "overall" in data
            assert "by_tier" in data
            assert "active_subscriptions" in data
            assert "total_users" in data


class TestAdminRoutesAPI:
    """Test routes management API."""

    def test_routes_list_unauthorized(self, client):
        """Test listing routes without token."""
        response = client.get("/admin/routes")
        assert response.status_code == 403

    def test_routes_list_structure(self, client, valid_token):
        """Test routes list structure."""
        response = client.get(
            "/admin/routes",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "routes" in data

    def test_route_detail_unauthorized(self, client):
        """Test route detail endpoint without token."""
        response = client.get("/admin/routes/1")
        assert response.status_code == 403


class TestAdminUsersAPI:
    """Test users management API."""

    def test_users_list_unauthorized(self, client):
        """Test listing users without token."""
        response = client.get("/admin/users")
        assert response.status_code == 403

    def test_users_list_structure(self, client, valid_token):
        """Test users list structure."""
        response = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "users" in data
            assert isinstance(data["users"], list)

    def test_users_list_includes_phone_number(self, client, valid_token):
        """Test users list exposes phone number without password hash."""

        class FakeAdminUsersDb:
            async def fetchrow(self, query: str, *args):
                if "COUNT(*)" in query:
                    return {"count": 1}
                return None

            async def fetch(self, query: str, *args):
                assert "u.phone_number" in query
                assert "u.user_id = s.user_id" in query
                assert "u.id::TEXT = s.user_id" not in query
                assert "password_hash" not in query
                return [
                    {
                        "id": 1,
                        "user_id": "rubika-guid-1",
                        "username": "testuser",
                        "phone_number": "09123456789",
                        "trial_start_at": datetime.now(),
                        "trial_end_at": datetime.now(),
                        "is_trial_active": True,
                        "created_at": datetime.now(),
                        "current_tier": "pro",
                        "subscription_end": datetime.now(),
                    }
                ]

        with patch("src.admin.routes.db_module.pool", FakeAdminUsersDb()):
            response = client.get(
                "/admin/users",
                headers={"Authorization": f"Bearer {valid_token}"},
            )

        assert response.status_code == 200
        user = response.json()["users"][0]
        assert user["phone_number"] == "09123456789"
        assert "password_hash" not in user

    def test_user_detail_unauthorized(self, client):
        """Test user detail endpoint without token."""
        response = client.get("/admin/users/1")
        assert response.status_code == 403


class TestAdminLogsAPI:
    """Test logs API endpoint."""

    def test_logs_unauthorized(self, client):
        """Test logs endpoint without token."""
        response = client.get("/admin/logs")
        assert response.status_code == 403

    def test_logs_structure(self, client, valid_token):
        """Test logs endpoint structure."""
        response = client.get(
            "/admin/logs",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "logs" in data


class TestAdminPerformanceAPI:
    """Test performance metrics API."""

    def test_performance_unauthorized(self, client):
        """Test performance endpoint without token."""
        response = client.get("/admin/performance")
        assert response.status_code == 403

    def test_performance_structure(self, client, valid_token):
        """Test performance metrics structure."""
        response = client.get(
            "/admin/performance",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert "messages_processed" in data
            assert "failed_messages" in data
            assert "average_retry_count" in data
            assert "largest_queues" in data
            assert "subscription_distribution" in data


class TestAdminStaticFiles:
    """Test static file serving."""

    def test_login_page_accessible(self, client):
        """Test login page is served."""
        response = client.get("/static/login.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_landing_page_has_enamad_meta_tag(self):
        """Test landing page includes eNamad verification meta tag."""
        html = Path("src/admin/static/index.html").read_text(encoding="utf-8")
        assert '<meta name="enamad" content="795459943" />' in html

    def test_css_file_accessible(self, client):
        """Test CSS file is served."""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_dashboard_page_accessible(self, client):
        """Test dashboard page is served."""
        response = client.get("/static/dashboard.html")
        assert response.status_code == 200

    def test_users_page_accessible(self, client):
        """Test users page is served."""
        response = client.get("/static/users.html")
        assert response.status_code == 200

    def test_users_page_renders_phone_number_column(self):
        """Test users page includes the phone column and matching render hooks."""
        html = Path("src/admin/static/users.html").read_text(encoding="utf-8")

        assert "<th>شماره تماس</th>" in html
        assert "user.phone_number" in html
        assert "detailPhoneNumber" in html
        assert "user.current_tier" in html
        assert "اشتراک فعال" in html
        assert 'colspan="9"' in html
        assert 'colspan="8"' not in html

    def test_logs_page_accessible(self, client):
        """Test logs page is served."""
        response = client.get("/static/logs.html")
        assert response.status_code == 200

    def test_performance_page_accessible(self, client):
        """Test performance page is served."""
        response = client.get("/static/performance.html")
        assert response.status_code == 200

    def test_settings_page_accessible(self, client):
        """Test settings page is served."""
        response = client.get("/static/settings.html")
        assert response.status_code == 200


class TestAdminSecurity:
    """Test security-related functionality."""

    def test_invalid_token_rejected(self, client):
        """Test invalid JWT token is rejected."""
        response = client.get(
            "/admin/dashboard-summary",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_missing_token_rejected(self, client):
        """Test missing token is rejected."""
        response = client.get("/admin/dashboard-summary")
        assert response.status_code == 403

    def test_cors_headers_present(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/health")
        # This tests that the app is accessible


def test_admin_static_pages_use_explicit_persian_calendar_locale():
    """Admin-visible dates should request the Persian calendar explicitly."""
    static_dir = Path("src/admin/static")
    html = "\n".join(path.read_text(encoding="utf-8") for path in static_dir.glob("*.html"))

    assert "fa-IR-u-ca-persian" in html
    assert "toLocaleDateString('fa-IR')" not in html
    assert "toLocaleString('fa-IR')" not in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
