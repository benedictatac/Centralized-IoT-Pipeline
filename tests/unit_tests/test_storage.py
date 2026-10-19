
#will integrate integration tests later 
import pytest
from sqlalchemy import select
from src.pipeline.storage import upsert_device, store_event
from src.models.database import DeviceDB, ReadingDB




# Device -> DeviceDB
# fixtures are requested as arguments, pytest builds them (they can't be called directly)
@pytest.mark.asyncio
async def test_upsert_device(create_device_obj, mock_db_session):

    #serialized to DeviceDB (SQLAlchemy language)
    device_serialized = await upsert_device(create_device_obj, mock_db_session)

    assert device_serialized is not None
    assert isinstance(device_serialized, DeviceDB)
    assert device_serialized.device_type == "Camera" # enum value, not DeviceType.CAMERA


# goes through the real SQL driver, which rejects Enum objects in String columns
@pytest.mark.asyncio
async def test_store_event_saves_enums_as_text(create_device_obj, mock_db_session):

    await store_event(create_device_obj, mock_db_session)

    reading = (await mock_db_session.scalars(select(ReadingDB))).one()
    assert reading.device_id == create_device_obj.device_id
    assert reading.metric == "Movement"
    assert reading.unit == "Celsius"
    assert reading.value == 2.0


@pytest.mark.asyncio
async def test_store_event_twice_updates_existing_device(create_device_obj, mock_db_session):

    await store_event(create_device_obj, mock_db_session)
    await store_event(create_device_obj, mock_db_session)

    devices = (await mock_db_session.scalars(select(DeviceDB))).all()
    readings = (await mock_db_session.scalars(select(ReadingDB))).all()
    assert len(devices) == 1 # second event updated the device instead of inserting a duplicate
    assert len(readings) == 2






