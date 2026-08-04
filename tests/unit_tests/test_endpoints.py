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


@pytest_asyncio.fixture
async def client():
    # 2. Setup mock database session
    mock_db = AsyncMock()

    # Create dummy SQLAlchemy ORM objects to simulate DB query output
    mock_reading = ReadingDB(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        device_id=uuid.UUID("2cc77e1a-9915-4c7b-8170-f01e0c1f1bd1"),
        metric="temperature",
        unit="celsius",
        value=23.5,
        timestamp=datetime.now(),
        created_at=datetime.now(),
    )

    # Mock `await db.scalars(...)` behavior
    # db.scalars() returns a result object that has an .all() method
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_reading]
    mock_db.scalars.return_value = mock_result

    # 3. Override dependency
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    # 4. Yield client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 5. Clean up after test finishes
    app.dependency_overrides.clear()


# 6. Pass the `client` fixture into the test function signature!
@pytest.mark.asyncio
async def test_get_readings_endpoint(client: AsyncClient):
    test_device_id = "2cc77e1a-9915-4c7b-8170-f01e0c1f1bd1"

    # Send GET request using the configured client fixture
    response = await client.get(
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