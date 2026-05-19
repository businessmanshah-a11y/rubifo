"""Tests for queue selection needed by professional plans."""

import pytest

from src.core.queue_service import QueueService


@pytest.mark.asyncio
async def test_get_next_pending_for_message_type_filters_source_post_type(mock_db):
    mock_db.fetchrow.return_value = {
        "id": 11,
        "route_id": 5,
        "source_post_id": 42,
        "status": "pending",
        "order_index": 3,
        "message_type": "video",
    }

    item = await QueueService(mock_db).get_next_pending(route_id=5, message_type="video")

    assert item["source_post_id"] == 42
    sql = mock_db.fetchrow.call_args.args[0]
    assert "sp.message_type = $2" in sql


@pytest.mark.asyncio
async def test_rebuild_pending_from_source_uses_route_source_id(mock_db):
    mock_db.fetchrow.return_value = {"source_id": 3}
    mock_db.fetch.return_value = [{"id": 101}, {"id": 102}]

    inserted = await QueueService(mock_db).rebuild_pending_from_source(route_id=7)

    assert inserted == 2
    assert mock_db.fetchrow.await_count == 1
    assert mock_db.execute.await_count == 2
