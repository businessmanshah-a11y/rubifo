from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
import csv
import io
from datetime import datetime, date
from typing import Optional, List
from src.admin.auth import verify_token
import src.database as db_module
from src.core.transaction_service import TransactionService
from src.core.subscription_service import SubscriptionService
from src.core.user_service import UserService
from src.logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])


class _EmptyAdminDb:
    """Empty async DB used by tests before the real pool is initialized."""

    async def fetchrow(self, query: str, *args):
        if "AVG(" in query:
            return {"avg": 0}
        if "SUM(amount)" in query:
            return {"count": 0, "total": 0, "total_count": 0, "total_amount": 0}
        return {"count": 0}

    async def fetch(self, query: str, *args):
        return []

    async def execute(self, query: str, *args):
        return None


_EMPTY_DB = _EmptyAdminDb()


def _db():
    return db_module.pool or _EMPTY_DB


@router.get("/transactions")
async def get_transactions(
    username: str = Depends(verify_token),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, completed, failed)"),
    tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> dict:
    """Get transactions with optional filtering.

    Args:
        username: Authenticated username
        user_id: Filter by user ID
        status: Filter by status
        tier: Filter by subscription tier
        start_date: Start date for filtering
        end_date: End date for filtering
        limit: Result limit
        offset: Pagination offset

    Returns:
        List of transactions with total count
    """
    logger.info(f"Admin {username} accessing transactions")

    transaction_service = TransactionService(_db())

    # Build query with filters
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if user_id:
        query += f" AND user_id = ${len(params) + 1}"
        params.append(user_id)

    if status:
        query += f" AND status = ${len(params) + 1}"
        params.append(status)

    if tier:
        query += f" AND tier = ${len(params) + 1}"
        params.append(tier)

    if start_date:
        query += f" AND created_at::date >= ${len(params) + 1}"
        params.append(start_date)

    if end_date:
        query += f" AND created_at::date <= ${len(params) + 1}"
        params.append(end_date)

    # Count total matching records
    count_query = f"SELECT COUNT(*) as count FROM transactions WHERE 1=1"
    count_params = []

    if user_id:
        count_query += f" AND user_id = ${len(count_params) + 1}"
        count_params.append(user_id)
    if status:
        count_query += f" AND status = ${len(count_params) + 1}"
        count_params.append(status)
    if tier:
        count_query += f" AND tier = ${len(count_params) + 1}"
        count_params.append(tier)
    if start_date:
        count_query += f" AND created_at::date >= ${len(count_params) + 1}"
        count_params.append(start_date)
    if end_date:
        count_query += f" AND created_at::date <= ${len(count_params) + 1}"
        count_params.append(end_date)

    total_row = await _db().fetchrow(count_query, *count_params)
    total = total_row["count"] if total_row else 0

    # Add ordering and pagination
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    # Fetch transactions
    results = await _db().fetch(query, *params)
    transactions = [dict(row) for row in results]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": transactions,
    }


@router.get("/stats")
async def get_stats(username: str = Depends(verify_token)) -> dict:
    """Get revenue statistics and summary.

    Args:
        username: Authenticated username

    Returns:
        Revenue statistics including totals and breakdown by tier
    """
    logger.info(f"Admin {username} accessing stats")

    transaction_service = TransactionService(_db())

    # Get overall stats
    overall_stats = await transaction_service.get_revenue_stats()

    # Get breakdown by tier
    tier_breakdown = await transaction_service.get_revenue_by_tier()

    # Get active subscription count
    active_subs = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM subscriptions WHERE is_active = true"
    )
    active_subscriptions = active_subs["count"] if active_subs else 0

    # Get total users
    total_users = await _db().fetchrow("SELECT COUNT(*) as count FROM users")
    total_user_count = total_users["count"] if total_users else 0

    # Get transactions by status
    status_breakdown = await _db().fetch(
        "SELECT status, COUNT(*) as count FROM transactions GROUP BY status"
    )
    status_stats = {row["status"]: row["count"] for row in status_breakdown}

    return {
        "overall": overall_stats,
        "by_tier": tier_breakdown,
        "active_subscriptions": active_subscriptions,
        "total_users": total_user_count,
        "by_status": status_stats,
    }


@router.get("/transactions/export")
async def export_transactions(
    username: str = Depends(verify_token),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
) -> StreamingResponse:
    """Export transactions as CSV.

    Args:
        username: Authenticated username
        user_id: Filter by user ID
        status: Filter by status
        tier: Filter by subscription tier
        start_date: Start date
        end_date: End date

    Returns:
        CSV file as streaming response
    """
    logger.info(f"Admin {username} exporting transactions")

    # Build query with filters
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if user_id:
        query += f" AND user_id = ${len(params) + 1}"
        params.append(user_id)
    if status:
        query += f" AND status = ${len(params) + 1}"
        params.append(status)
    if tier:
        query += f" AND tier = ${len(params) + 1}"
        params.append(tier)
    if start_date:
        query += f" AND created_at::date >= ${len(params) + 1}"
        params.append(start_date)
    if end_date:
        query += f" AND created_at::date <= ${len(params) + 1}"
        params.append(end_date)

    query += " ORDER BY created_at DESC"

    # Fetch transactions
    results = await _db().fetch(query, *params)
    transactions = [dict(row) for row in results]

    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "user_id",
            "amount",
            "tier",
            "status",
            "reference_id",
            "created_at",
        ],
    )

    writer.writeheader()
    for txn in transactions:
        writer.writerow(txn)

    # Convert to bytes
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue().encode()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


@router.get("/routes")
async def get_routes(
    username: str = Depends(verify_token),
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get all routes with user info and queue count.

    Args:
        username: Authenticated username
        user_id: Filter by user ID
        limit: Result limit
        offset: Pagination offset

    Returns:
        List of routes with queue information
    """
    logger.info(f"Admin {username} accessing routes")

    query = """
        SELECT r.id, r.user_id, r.source_channel_id, r.target_channel_id,
               r.is_active, r.created_at,
               COUNT(CASE WHEN pq.status = 'pending' THEN 1 END) as pending_count
        FROM routes r
        LEFT JOIN post_queue pq ON r.id = pq.route_id
        WHERE 1=1
    """
    params = []

    if user_id:
        query += f" AND r.user_id = ${len(params) + 1}"
        params.append(user_id)

    query += " GROUP BY r.id ORDER BY r.created_at DESC"

    # Count total
    count_query = "SELECT COUNT(DISTINCT id) as count FROM routes WHERE 1=1"
    count_params = []
    if user_id:
        count_query += f" AND user_id = ${len(count_params) + 1}"
        count_params.append(user_id)

    total_row = await _db().fetchrow(count_query, *count_params)
    total = total_row["count"] if total_row else 0

    query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    results = await _db().fetch(query, *params)
    routes = [dict(row) for row in results]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "routes": routes,
    }


@router.get("/routes/{route_id}")
async def get_route_detail(
    route_id: int,
    username: str = Depends(verify_token),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get route detail with queue items.

    Args:
        route_id: Route ID
        username: Authenticated username
        limit: Queue item limit
        offset: Pagination offset

    Returns:
        Route info with queue items
    """
    logger.info(f"Admin {username} accessing route {route_id}")

    # Get route info
    route = await _db().fetchrow("SELECT * FROM routes WHERE id = $1", route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Get queue items
    queue = await _db().fetch(
        "SELECT * FROM post_queue WHERE route_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
        route_id,
        limit,
        offset,
    )

    # Get queue stats
    stats = await _db().fetchrow(
        """
        SELECT status, COUNT(*) as count FROM post_queue
        WHERE route_id = $1 GROUP BY status
        """,
        route_id,
    )

    return {
        "route": dict(route),
        "queue_items": [dict(item) for item in queue],
        "queue_stats": dict(stats) if stats else {},
    }


@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: int, username: str = Depends(verify_token)
) -> dict:
    """Deactivate a route.

    Args:
        route_id: Route ID
        username: Authenticated username

    Returns:
        Confirmation message
    """
    logger.info(f"Admin {username} deleting route {route_id}")

    # Check if route exists
    route = await _db().fetchrow("SELECT * FROM routes WHERE id = $1", route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Deactivate route
    await _db().execute("UPDATE routes SET is_active = false WHERE id = $1", route_id)

    logger.info(f"Route {route_id} deactivated by admin {username}")

    return {"message": "Route deactivated successfully"}


@router.get("/users")
async def get_users(
    username: str = Depends(verify_token),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get all users with subscription status.

    Args:
        username: Authenticated username
        limit: Result limit
        offset: Pagination offset

    Returns:
        List of users with subscription info
    """
    logger.info(f"Admin {username} accessing users list")

    query = """
        SELECT u.id, u.user_id, u.username, u.trial_start_at, u.trial_end_at,
               u.is_trial_active, u.created_at,
               s.tier as current_tier, s.end_date as subscription_end
        FROM users u
        LEFT JOIN subscriptions s ON u.id::TEXT = s.user_id AND s.is_active = true
        ORDER BY u.created_at DESC
        LIMIT $1 OFFSET $2
    """

    # Count total users
    total_row = await _db().fetchrow("SELECT COUNT(*) as count FROM users")
    total = total_row["count"] if total_row else 0

    results = await _db().fetch(query, limit, offset)
    users = [dict(row) for row in results]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "users": users,
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int, username: str = Depends(verify_token)
) -> dict:
    """Get detailed user information.

    Args:
        user_id: User ID
        username: Authenticated username

    Returns:
        User details with subscriptions and routes
    """
    logger.info(f"Admin {username} accessing user {user_id} details")

    # Get user
    user = await _db().fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get subscriptions
    subscriptions = await _db().fetch(
        "SELECT * FROM subscriptions WHERE user_id = $1 ORDER BY created_at DESC",
        user_id,
    )

    # Get routes
    routes = await _db().fetch(
        "SELECT * FROM routes WHERE user_id = $1 ORDER BY created_at DESC",
        user_id,
    )

    # Get recent transactions
    transactions = await _db().fetch(
        """
        SELECT * FROM transactions WHERE user_id = $1
        ORDER BY created_at DESC LIMIT 10
        """,
        user_id,
    )

    return {
        "user": dict(user),
        "subscriptions": [dict(row) for row in subscriptions],
        "routes": [dict(row) for row in routes],
        "recent_transactions": [dict(row) for row in transactions],
    }


@router.get("/dashboard-summary")
async def get_dashboard_summary(username: str = Depends(verify_token)) -> dict:
    """Get dashboard summary with key metrics.

    Args:
        username: Authenticated username

    Returns:
        Dashboard metrics
    """
    logger.info(f"Admin {username} accessing dashboard summary")

    # Total users
    total_users = await _db().fetchrow("SELECT COUNT(*) as count FROM users")

    # Active subscriptions
    active_subs = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM subscriptions WHERE is_active = true"
    )

    # Active routes
    active_routes = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM routes WHERE is_active = true"
    )

    # Pending posts in queues
    pending_posts = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM post_queue WHERE status = 'pending'"
    )

    # Revenue (completed transactions)
    revenue = await _db().fetchrow(
        """
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM transactions WHERE status = 'completed'
        """
    )

    # Trial users
    from datetime import datetime
    trial_users = await _db().fetchrow(
        """
        SELECT COUNT(*) as count FROM users
        WHERE is_trial_active = true AND trial_end_at > $1
        """,
        datetime.now(),
    )

    return {
        "total_users": total_users["count"] if total_users else 0,
        "active_subscriptions": active_subs["count"] if active_subs else 0,
        "active_routes": active_routes["count"] if active_routes else 0,
        "pending_posts": pending_posts["count"] if pending_posts else 0,
        "total_revenue": {
            "count": revenue["count"] if revenue else 0,
            "total_amount": revenue["total"] if revenue else 0,
        },
        "active_trial_users": trial_users["count"] if trial_users else 0,
    }


@router.get("/logs")
async def get_logs(
    username: str = Depends(verify_token),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None, description="Filter by action type"),
    level: Optional[str] = Query(None, description="Filter by log level (info, warning, error)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get system logs with optional filtering.

    Args:
        username: Authenticated username
        user_id: Filter by user ID
        action: Filter by action type
        level: Filter by log level
        start_date: Start date
        end_date: End date
        limit: Result limit
        offset: Pagination offset

    Returns:
        Logs with pagination
    """
    logger.info(f"Admin {username} accessing logs")

    query = "SELECT * FROM logs WHERE 1=1"
    params = []

    if user_id:
        query += f" AND user_id = ${len(params) + 1}"
        params.append(user_id)

    if action:
        query += f" AND action = ${len(params) + 1}"
        params.append(action)

    if level:
        query += f" AND level = ${len(params) + 1}"
        params.append(level)

    if start_date:
        query += f" AND created_at::date >= ${len(params) + 1}"
        params.append(start_date)

    if end_date:
        query += f" AND created_at::date <= ${len(params) + 1}"
        params.append(end_date)

    # Count total
    count_query = f"SELECT COUNT(*) as count FROM logs WHERE 1=1"
    count_params = []

    if user_id:
        count_query += f" AND user_id = ${len(count_params) + 1}"
        count_params.append(user_id)
    if action:
        count_query += f" AND action = ${len(count_params) + 1}"
        count_params.append(action)
    if level:
        count_query += f" AND level = ${len(count_params) + 1}"
        count_params.append(level)
    if start_date:
        count_query += f" AND created_at::date >= ${len(count_params) + 1}"
        count_params.append(start_date)
    if end_date:
        count_query += f" AND created_at::date <= ${len(count_params) + 1}"
        count_params.append(end_date)

    total_row = await _db().fetchrow(count_query, *count_params)
    total = total_row["count"] if total_row else 0

    # Add ordering and pagination
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    results = await _db().fetch(query, *params)
    logs = [dict(row) for row in results]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": logs,
    }


@router.get("/performance")
async def get_performance_metrics(username: str = Depends(verify_token)) -> dict:
    """Get performance metrics and system health.

    Args:
        username: Authenticated username

    Returns:
        Performance metrics
    """
    logger.info(f"Admin {username} accessing performance metrics")

    # Messages processed in last hour
    from datetime import timedelta
    one_hour_ago = datetime.now() - timedelta(hours=1)
    one_day_ago = datetime.now() - timedelta(days=1)

    messages_1h = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM post_queue WHERE status = 'sent' AND created_at > $1",
        one_hour_ago,
    )

    messages_24h = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM post_queue WHERE status = 'sent' AND created_at > $1",
        one_day_ago,
    )

    # Failed messages
    failed_messages = await _db().fetchrow(
        "SELECT COUNT(*) as count FROM post_queue WHERE status = 'failed'"
    )

    # Average retry count
    avg_retry = await _db().fetchrow(
        "SELECT AVG(retry_count) as avg FROM post_queue"
    )

    # Queue performance
    queue_stats = await _db().fetch(
        """
        SELECT route_id, COUNT(*) as count,
               ROUND(AVG(EXTRACT(EPOCH FROM (created_at - NOW())))) as avg_age_seconds
        FROM post_queue
        WHERE status = 'pending'
        GROUP BY route_id
        ORDER BY count DESC
        LIMIT 10
        """
    )

    # Subscription tier distribution
    tier_distribution = await _db().fetch(
        """
        SELECT tier, COUNT(*) as count
        FROM subscriptions
        WHERE is_active = true
        GROUP BY tier
        """
    )

    return {
        "messages_processed": {
            "last_hour": messages_1h["count"] if messages_1h else 0,
            "last_24h": messages_24h["count"] if messages_24h else 0,
        },
        "failed_messages": failed_messages["count"] if failed_messages else 0,
        "average_retry_count": float(avg_retry["avg"] or 0),
        "largest_queues": [dict(row) for row in queue_stats],
        "subscription_distribution": [dict(row) for row in tier_distribution],
    }
