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


async def upsert_device(device_type:str, device_name:str, session:AsyncSession,device_id: uuid.UUID) -> DeviceDB:

    #1. Check if device is avaialable

   
        stmt = select(DeviceDB).where(DeviceDB.device_id == device_id)
        result = await session.execute(stmt)

        device = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        #if device does not exist, we create a new one
        if not device: 
            new_device = DeviceDB(device_id = device_id, device_type = device_type, device_name = device_name)
            session.add(new_device)
            return new_device
        
            #else we update_at of the device accordingly
        else:
            device.updated_at = now
            return device




async def insert_readings(device_id: uuid.UUID, 
                                             session : AsyncSession, 
                                             readings_data : List[Reading], timestamp:datetime ) -> None:
        if not readings_data:
            return
        for reading in readings_data:
            new_reading = ReadingDB(
            device_id=device_id,
            metric=reading.metric,
            unit=reading.unit,
            value=reading.value,
            timestamp=timestamp
        )
            session.add(new_reading)

 

async def store_event(device: Device, session:AsyncSession):
    
    
    try: 
        device_row = await upsert_device(
        device_id=device.device_id,
        device_type=device.device_type,
        device_name=device.device_name,
        session=session
    )

        await insert_readings(device_id=device.device_id,
                            readings_data=device.readings,    
                           timestamp=device.timestamp, session = session,)
        await session.commit()

    except Exception:
        await session.rollback()