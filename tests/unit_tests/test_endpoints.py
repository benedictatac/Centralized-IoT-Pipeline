import os
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# 1. Set env vars BEFORE importing app so BaseSettings doesn't fail
os.environ.setdefault("DB_USER", "mock")
os.environ.setdefault("DB_PASSWORD", "mock")
os.environ.setdefault("DB_NAME", "mock")
os.environ.setdefault("RDS_USER", "mock")
os.environ.setdefault("RDS_PASSWORD", "mock")
os.environ.setdefault("RDS_NAME", "mock")

from src.api.endpoints import app
from src.pipeline.storage import get_db, ReadingDB
from conftest import mock_client



# 6. Pass the `client` fixture into the test function signature!
@pytest.mark.asyncio
async def test_get_readings_endpoint(mock_client: AsyncClient):
    test_device_id = "2cc77e1a-9915-4c7b-8170-f01e0c1f1bd1"

    # Send GET request using the configured client fixture
    response = await mock_client.get(
        "/events", 
        params={"device_id": test_device_id, "limit": 2}
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "metric" in data[0]
    assert "value" in data[0]
    assert data[0]["device_id"] == test_device_id