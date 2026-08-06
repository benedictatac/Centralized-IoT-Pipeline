
#will integrate integration tests later 
import pytest
from src.pipeline.storage import *
from tests.unit_tests.conftest import create_device_obj, mock_engine, mock_db_session
from src.models.database import DeviceDB




# Device -> DeviceDB
@pytest.mark.asyncio
def test_upsert_device(create_device_obj):

    engine = mock_engine()
    session = mock_db_session(engine)

    #serialized to DeviceDB (SQLAlchemy language)
    device_serialized = upsert_device(create_device_obj, session)

    assert device_serialized is not None
    assert isinstance(device_serialized, DeviceDB)






