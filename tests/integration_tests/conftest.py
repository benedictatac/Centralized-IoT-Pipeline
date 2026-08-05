

import os
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import patch

# Set environment variables prior to imports
os.environ.setdefault("DB_USER", "mock")
os.environ.setdefault("DB_PASSWORD", "mock")
os.environ.setdefault("DB_NAME", "mock")
os.environ.setdefault("RDS_USER", "mock")
os.environ.setdefault("RDS_PASSWORD", "mock")
os.environ.setdefault("RDS_NAME", "mock")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.models.baseModel import Device, DeviceType, Metric, Unit, Reading
from src.models.database import Base, DeviceDB, ReadingDB
from src.pipeline.storage import upsert_device, insert_readings, store_event




TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(session = "session")
async def mock_engine():

    """Session-scoped async engine for SQLite in-memory testing."""
    engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    """
    Function-scoped AsyncSession wrapped in a rollback transaction.
    Guarantees complete test isolation without leaving state behind.
    """
    async_session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_engine.connect() as conn:
        # Begin nested transaction
        trans = await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
        # Roll back transaction after test finishes
        await trans.rollback()
#endregion fixtures