import pytest
import uuid
import os
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


# 1. Set env vars BEFORE importing app so BaseSettings doesn't fail
os.environ.setdefault("DB_USER", "mock")
os.environ.setdefault("DB_PASSWORD", "mock")
os.environ.setdefault("DB_NAME", "mock")
os.environ.setdefault("RDS_USER", "mock")
os.environ.setdefault("RDS_PASSWORD", "mock")
os.environ.setdefault("RDS_NAME", "mock")

from src.models.baseModel import Device, DeviceType, Metric, Unit, Reading
from src.api.endpoints import app
from src.pipeline.storage import get_db, ReadingDB
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.models.database import Base  # SQLAlchemy DeclarativeBase

#region members

# conftest.py -> unit_tests -> tests -> repo root
BASE_DIR = Path(__file__).parent.parent.parent
FILE_PATH = BASE_DIR / "docker" / "mosquitto" / "data" / "randomData.json"
# storage.py is async, so the test database needs an async driver too
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# fixed values (not uuid4()/now()) so tests can assert against exactly what the fixture built
DEVICETYPE = DeviceType.CAMERA
DEVICEID = uuid.UUID("2cc77e1a-9915-4c7b-8170-f01e0c1f1bd1")
DEVICENAME = "Charles' device"
DAYTIME = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
MOVEMENT = Metric.MOVEMENT
UNIT = Unit.CELSIUS
VALUE = 2.0
#endregion members


#region fixtures 


@pytest.fixture
def valid_payload():
    return {
        "device_id": str(uuid.uuid4()),
        "device_name": "Test Thermostat",
        "device_type": "Thermostat",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "readings": [
            {"metric": "Temperature", "unit": "Celsius", "value": 22.5}
        ]
    }

@pytest.fixture
def create_device_obj():

        # a Pydantic model is not a DB row, there is nothing to delete afterwards -> plain return
        device = Device(device_type=DEVICETYPE, device_id=DEVICEID, device_name=DEVICENAME,
                    timestamp=DAYTIME, readings = [Reading(metric=MOVEMENT, unit=UNIT, value=VALUE)])
        return device


@pytest_asyncio.fixture
async def mock_client():

    #mock database session
    mock_db = AsyncMock()

    #create a dummy SQLAlchemy ORM objects to simulate DB query output

    mock_reading  = ReadingDB(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        device_id=uuid.UUID("2cc77e1a-9915-4c7b-8170-f01e0c1f1bd1"),
        metric="temperature",
        unit="celsius",
        value=23.5,
        timestamp=DAYTIME,
        created_at=DAYTIME,
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



#function scoped: every test gets its own brand new in-memory database, so nothing leaks between tests
#(a session scoped async engine would live on a different event loop than the function scoped tests)
@pytest_asyncio.fixture
async def mock_engine():

    engine = create_async_engine(url = TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


#AsyncSession because upsert_device/insert_readings/store_event all await the session
@pytest_asyncio.fixture
async def mock_db_session(mock_engine):

    async with AsyncSession(bind=mock_engine, expire_on_commit=False) as session:
        yield session
#endregion fixtures