


# create an async database session using SQLAlchemy async engine
# check if the device already exists in the devices table - if not, create. If yes, update its update_at timestamp
# insert each reading from the payload into the readings table 



import asyncpg
import asyncio
from config import Settings

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import(
    AsyncEngine,
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine,
    )
from src.models.database import DeviceDB
from sqlalchemy import exists, select
import uuid

#single connection

settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

new_id = uuid.uuid4()

# 1. Create Engine & Session Factory ONCE at module scope
engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 2. Corrected dependency/context manager function
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Call async_session() to construct an actual session
    async with async_session() as session:
        yield session


# 3. Functions accept an AsyncSession directly (cleaner separation)
async def create_device(device_id: uuid.uuid4, session: AsyncSession) -> DeviceDB:
    new_device = DeviceDB(device_id=device_id)
    session.add(new_device)
    await session.commit()
    await session.refresh(new_device)
    return new_device


async def check_device_exists(device_id: str, session: AsyncSession) -> bool:
    stmt = select(exists().where(DeviceDB.device_id == device_id))
    result = await session.scalar(stmt)
    return bool(result)


