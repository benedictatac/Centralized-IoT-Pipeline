import json
import pytest
from unittest.mock import AsyncMock
import src.pipeline.cache as cache


# swaps the real redis connection for a mock so no redis server is needed
@pytest.mark.asyncio
async def test_upsert_data_writes_readings_as_json(create_device_obj, monkeypatch):
    fake_conn = AsyncMock()
    monkeypatch.setattr(cache, "conn", fake_conn)

    await cache.upsert_data(create_device_obj)

    key, value = fake_conn.set.await_args.args
    assert key == f"device:{create_device_obj.device_id}:latest"
    # enums arrive as plain strings, so any consumer can json.loads the cached value
    assert json.loads(value) == [{"metric": "Movement", "unit": "Celsius", "value": 2.0}]
    fake_conn.expire.assert_awaited_once_with(key, 86400)
