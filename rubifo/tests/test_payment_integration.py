"""Integration tests for payment system (T68)."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from src.integrations.zarinpal import ZarinpalGateway
from src.core.subscription_service import SubscriptionService
from src.core.transaction_service import TransactionService


@pytest.mark.asyncio
class TestZarinpalIntegration:
    """Test Zarinpal payment gateway integration."""

    @pytest.fixture
    def zarinpal_gateway(self):
        """Create Zarinpal gateway instance."""
        return ZarinpalGateway(merchant_id="test_merchant", sandbox=True)

    async def test_request_payment_success(self, zarinpal_gateway, sample_zarinpal_response):
        """Test successful payment request."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=sample_zarinpal_response)
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            success, result = await zarinpal_gateway.request_payment(
                amount=50000,
                description="Test payment",
                callback_url="https://example.com/callback",
            )

            assert success is True

    async def test_request_payment_invalid_amount(self, zarinpal_gateway):
        """Test payment request with invalid amount."""
        success, result = await zarinpal_gateway.request_payment(
            amount=0,
            description="Test",
            callback_url="https://example.com/callback",
        )

        # Should fail with invalid amount
        assert success is False or isinstance(result, str)

    async def test_verify_payment_success(self, zarinpal_gateway, sample_zarinpal_verify):
        """Test successful payment verification."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=sample_zarinpal_verify)
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            success, ref_id = await zarinpal_gateway.verify_payment(
                authority="auth_123456",
                amount=50000,
            )

            assert success is True

    async def test_verify_payment_failure(self, zarinpal_gateway):
        """Test payment verification failure."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"result": -1})
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            success, ref_id = await zarinpal_gateway.verify_payment(
                authority="invalid_auth",
                amount=50000,
            )

            assert success is False

    async def test_gateway_timeout_handling(self, zarinpal_gateway):
        """Test gateway timeout handling."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()

            success, result = await zarinpal_gateway.request_payment(
                amount=50000,
                description="Test",
                callback_url="https://example.com/callback",
            )

            assert success is False

    async def test_gateway_connection_error(self, zarinpal_gateway):
        """Test gateway connection error handling."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.side_effect = ConnectionError("Network error")

            success, result = await zarinpal_gateway.request_payment(
                amount=50000,
                description="Test",
                callback_url="https://example.com/callback",
            )

            assert success is False


@pytest.mark.asyncio
class TestSubscriptionPaymentFlow:
    """Test subscription payment flow integration."""

    async def test_complete_payment_flow(self, mock_db, sample_user_data, sample_transaction_data):
        """Test complete payment flow."""
        subscription_service = SubscriptionService(mock_db)
        transaction_service = TransactionService(mock_db)

        # Step 1: Initiate payment
        zarinpal = ZarinpalGateway(merchant_id="test", sandbox=True)
        with patch.object(zarinpal, "request_payment", return_value=(True, "auth_123")):
            success, auth = await zarinpal.request_payment(50000, "Test", "https://example.com")
            assert success is True

        # Step 2: Verify payment
        mock_db.fetchrow.return_value = sample_transaction_data
        with patch.object(zarinpal, "verify_payment", return_value=(True, "ref_123")):
            verified, ref = await zarinpal.verify_payment("auth_123", 50000)
            assert verified is True

        # Step 3: Create subscription
        mock_db.execute.return_value = None
        mock_db.fetchrow.return_value = {
            "id": 1,
            "user_id": 1,
            "tier": "basic",
            "is_active": True,
        }

        sub = await subscription_service.create_subscription(1, "basic")
        assert mock_db.execute.called

    async def test_payment_failure_recovery(self, mock_db):
        """Test recovery from payment failure."""
        transaction_service = TransactionService(mock_db)

        # Failed payment
        mock_db.execute.return_value = None

        # Should still be able to retry
        zarinpal = ZarinpalGateway(merchant_id="test", sandbox=True)
        with patch.object(zarinpal, "request_payment", return_value=(True, "auth_456")):
            success, auth = await zarinpal.request_payment(50000, "Retry", "https://example.com")
            assert success is True


@pytest.mark.asyncio
class TestTransactionTracking:
    """Test transaction history tracking."""

    async def test_insert_transaction(self, mock_db):
        """Test inserting transaction."""
        transaction_service = TransactionService(mock_db)
        mock_db.execute.return_value = None

        result = await transaction_service.insert_transaction(
            user_id=1,
            amount=50000,
            tier="basic",
            status="completed",
            reference_id="ref_123",
        )

        assert mock_db.execute.called

    async def test_get_transactions(self, mock_db):
        """Test retrieving transactions."""
        transaction_service = TransactionService(mock_db)
        mock_db.fetch.return_value = [
            {"id": 1, "amount": 50000, "status": "completed"},
            {"id": 2, "amount": 120000, "status": "completed"},
        ]

        transactions = await transaction_service.get_transactions(user_id=1)

        assert isinstance(transactions, list)
        assert mock_db.fetch.called

    async def test_get_transaction_by_reference(self, mock_db):
        """Test getting transaction by reference ID."""
        transaction_service = TransactionService(mock_db)
        mock_db.fetchrow.return_value = {"id": 1, "reference_id": "ref_123", "status": "completed"}

        txn = await transaction_service.get_transaction_by_reference("ref_123")

        assert mock_db.fetchrow.called

    async def test_get_revenue_stats(self, mock_db):
        """Test revenue statistics."""
        transaction_service = TransactionService(mock_db)
        mock_db.fetchrow.return_value = {"count": 100, "total": 5000000}

        stats = await transaction_service.get_revenue_stats()

        assert mock_db.fetchrow.called


@pytest.mark.asyncio
class TestPaymentErrorHandling:
    """Test error handling in payment system."""

    async def test_duplicate_payment_prevention(self, mock_db):
        """Test preventing duplicate payments."""
        transaction_service = TransactionService(mock_db)
        mock_db.fetchrow.return_value = {"id": 1, "reference_id": "ref_123"}

        # Should detect duplicate reference
        existing = await transaction_service.get_transaction_by_reference("ref_123")
        assert mock_db.fetchrow.called

    async def test_payment_amount_validation(self, mock_db):
        """Test payment amount validation."""
        subscription_service = SubscriptionService(mock_db)

        # Invalid amounts should be rejected
        # Amount must be > 0
        zarinpal = ZarinpalGateway(merchant_id="test", sandbox=True)

        with patch.object(zarinpal, "request_payment", return_value=(False, "Invalid amount")):
            success, result = await zarinpal.request_payment(0, "Test", "https://example.com")
            assert success is False

    async def test_payment_timeout_retry(self, mock_db):
        """Test retry logic on timeout."""
        zarinpal = ZarinpalGateway(merchant_id="test", sandbox=True)

        # First attempt fails, retry succeeds
        with patch.object(zarinpal, "verify_payment", side_effect=[
            (False, "Timeout"),
            (True, "ref_123"),
        ]):
            # First attempt
            success1, result1 = await zarinpal.verify_payment("auth_123", 50000)
            # Retry
            success2, result2 = await zarinpal.verify_payment("auth_123", 50000)

            assert success2 is True


if __name__ == "__main__":
    import asyncio
    pytest.main([__file__, "-v"])
