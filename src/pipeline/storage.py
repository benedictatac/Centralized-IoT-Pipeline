# create an async database session using SQLAlchemy async engine
# check if the device already exists in the devices table - if not, create. If yes, update its update_at timestamp
# insert each reading from the payload into the readings table 

from config import Settings
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import(
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine,
    )
from src.models.baseModel import Reading, Device
from src.models.database import DeviceDB, ReadingDB
from sqlalchemy import  select
import uuid
from typing import List

#single connection

settings = Settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


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


async def upsert_device(device:Device, session:AsyncSession) -> DeviceDB:

    #1. Check if device is avaialable
        stmt = select(DeviceDB).where(DeviceDB.device_id == device.device_id)
        result = await session.execute(stmt)

        device_found = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        #if device does not exist, we create a new one
        if not device_found: 
            new_device = DeviceDB(device_id = device.device_id, device_type = device.device_type, device_name = device.device_name)
            session.add(new_device)
            return new_device
        
            #else we update_at of the device accordingly
        else:
            device_found.updated_at = now
            return device_found




async def insert_readings(device:Device, session:AsyncSession) -> None:
        if not device.readings:
            return
        for reading in device.readings:
            new_reading = ReadingDB(
            device_id=device.device_id,
            metric=reading.metric,
            unit=reading.unit,
            value=reading.value,
            timestamp=device.timestamp
        )
            session.add(new_reading)

 

async def store_event(device: Device, session:AsyncSession):
    
    
    try: 
        device_row = await upsert_device(device=device, session =session)
        await insert_readings(device, session =session)
        await session.commit()

    except Exception:
        await session.rollback()
        raise