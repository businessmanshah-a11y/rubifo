from typing import List, Optional, Dict, Any
from src.logger import logger


class TransactionService:
    """Service for payment transaction management."""

    def __init__(self, db):
        self.db = db

    async def insert_transaction(
        self, user_id: int, amount: int, tier: str, status: str, reference_id: str
    ) -> int:
        """Insert transaction record.

        Args:
            user_id: Rubika user ID
            amount: Amount in Rials
            tier: Subscription tier
            status: Transaction status (pending, completed, failed)
            reference_id: Zarinpal reference ID

        Returns:
            Transaction ID
        """
        result = await self.db.fetchrow(
            "INSERT INTO transactions "
            "(user_id, amount, tier, status, reference_id) "
            "VALUES ($1, $2, $3, $4, $5) RETURNING id",
            user_id,
            amount,
            tier,
            status,
            reference_id,
        )

        transaction_id = result["id"] if result and "id" in result else 0
        logger.info(f"Transaction created: {transaction_id} for user {user_id}")
        return transaction_id

    async def get_transactions(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering.

        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Result limit
            offset: Pagination offset

        Returns:
            List of transaction dictionaries
        """
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if user_id:
            query += f" AND user_id = ${len(params) + 1}"
            params.append(user_id)

        if status:
            query += f" AND status = ${len(params) + 1}"
            params.append(status)

        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])

        results = await self.db.fetch(query, *params)
        return [dict(row) for row in results]

    async def get_transaction_by_reference(self, reference_id: str):
        """Get transaction by Zarinpal reference ID.

        Args:
            reference_id: Zarinpal reference ID

        Returns:
            Transaction dictionary or None
        """
        result = await self.db.fetchrow(
            "SELECT * FROM transactions WHERE reference_id = $1", reference_id
        )

        return dict(result) if result else None

    async def update_transaction_status(self, transaction_id: int, status: str) -> None:
        """Update transaction status.

        Args:
            transaction_id: Transaction ID
            status: New status
        """
        await self.db.execute(
            "UPDATE transactions SET status = $1 WHERE id = $2", status, transaction_id
        )

        logger.info(f"Transaction {transaction_id} status updated to {status}")

    async def get_revenue_stats(self) -> Dict[str, Any]:
        """Get revenue statistics for completed transactions.

        Returns:
            Dictionary with total_count and total_amount
        """
        result = await self.db.fetchrow(
            "SELECT COUNT(*) as total_count, COALESCE(SUM(amount), 0) as total_amount "
            "FROM transactions WHERE status = 'completed'"
        )

        return {
            "total_count": result.get("total_count", result.get("count", 0)) if result else 0,
            "total_amount": result.get("total_amount", result.get("total", 0)) if result else 0,
        }

    async def get_revenue_by_tier(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by subscription tier.

        Returns:
            List of revenue statistics per tier
        """
        results = await self.db.fetch(
            "SELECT tier, COUNT(*) as count, SUM(amount) as total "
            "FROM transactions WHERE status = 'completed' "
            "GROUP BY tier ORDER BY total DESC"
        )

        return [dict(row) for row in results]
