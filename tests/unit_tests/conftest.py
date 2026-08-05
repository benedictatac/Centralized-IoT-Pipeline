import pytest
import uuid
import os
from unittest.mock import AsyncMock
from datetime import datetime
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base  # SQLAlchemy DeclarativeBase

#region members

BASE_DIR = Path(__file__).parent.parent
FILE_PATH = BASE_DIR / "docker" / "mosquitto" / "data" / "randomData.json"
TEST_DATABASE_URL = "sqlite:///:memory:"
#endregion members


#region fixtures 


@pytest.fixture
def valid_payload():
    return {
        "device_id": str(uuid.uuid4()),
        "device_name": "Test Thermostat",
        "device_type": "Thermostat",
        "timestamp": datetime.now().isoformat(),
        "readings": [
            {"metric": "Temperature", "unit": "Celsius", "value": 22.5}
        ]
    }

@pytest.fixture
def test_created_device():
       
    
        device = Device(device_type=DeviceType.CAMERA, device_id=uuid.uuid4(), device_name="Charles' device",
                    timestamp=datetime.now(), readings = [Reading(metric=Metric.MOVEMENT, unit=Unit.Celsius, value=2.0)])
        
        yield device 

        
        device.delete()


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



@pytest.fixture(session = "session")
async def mock_engine():

    engine = create_engine(url = TEST_DATABASE_URL)
    Base.metadata.create_all(bind = engine)
    yield engine
    Base.metadata.drop_all(bind = engine)


@pytest.fixture(scope = "function")
async def mock_db_session(mock_engine):

    connection = mock_engine.connect()
    transaction = connection.begin()
    
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
#endregion fixtures