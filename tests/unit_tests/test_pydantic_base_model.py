from src.models.baseModel import Device
from datetime import datetime, timedelta, timezone
import src.pipeline.Helper_Config
import pytest
import pydantic
# the expected values live next to the fixture that uses them, so both always agree
# (fixtures themselves are found by pytest automatically and must not be imported)
from tests.unit_tests.conftest import FILE_PATH, DEVICETYPE, DEVICEID, DEVICENAME, DAYTIME, MOVEMENT, UNIT, VALUE
#region members

INVALID_VALUE = "BANANA"

#endregion

#region testCases
#keep this since its an integration test for later 
def test_device_creation_with_jsonFile_valid():

        device = src.pipeline.Helper_Config.Create_Device_From_Json2(FILE_PATH)
        assert device is not None
        assert isinstance(device, Device)

def test_create_valid_device(create_device_obj):

    device = create_device_obj

    assert device is not None
    assert isinstance(device, Device)
    assert device.device_type == DEVICETYPE
    assert device.device_id == DEVICEID
    assert device.device_name == DEVICENAME
    assert device.timestamp == DAYTIME
    assert device.readings[0].metric == MOVEMENT
    assert device.readings[0].unit == UNIT
    assert device.readings[0].value == VALUE


def test_invalid_devicetype(create_device_obj):
   
     bad_device = create_device_obj.model_dump()

     bad_device["device_type"] = INVALID_VALUE
     with pytest.raises(pydantic.ValidationError):
         Device.model_validate(bad_device)

def test_invalid_deviceID(create_device_obj):
    bad_device = create_device_obj.model_dump()
    bad_device["device_id"] = INVALID_VALUE

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_deviceName(create_device_obj):
    bad_device = create_device_obj.model_dump()
    bad_device["device_name"] = 123

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_timeStamp(create_device_obj):
    bad_device = create_device_obj.model_dump()
    bad_device["timestamp"] = "somethingdifferent here"

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_readingmetric(create_device_obj):

    bad_device = create_device_obj.model_dump()
    bad_device["readings"][0]["metric"] = INVALID_VALUE

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_readingunit(create_device_obj):

    bad_device = create_device_obj.model_dump()
    bad_device["readings"][0]["unit"] = INVALID_VALUE
    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_readingvalue(create_device_obj):

    bad_device = create_device_obj.model_dump()
    bad_device["readings"][0]["value"] = INVALID_VALUE

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_naive_timestamp_is_treated_as_utc(create_device_obj):
    device_data = create_device_obj.model_dump()
    device_data["timestamp"] = datetime(2026, 10, 18, 12, 0) # no tzinfo

    device = Device.model_validate(device_data)

    assert device.timestamp == DAYTIME
    assert device.timestamp.tzinfo == timezone.utc

def test_offset_timestamp_is_converted_to_utc(create_device_obj):
    device_data = create_device_obj.model_dump()
    device_data["timestamp"] = "2026-10-18T14:00:00+02:00" # same instant as DAYTIME

    device = Device.model_validate(device_data)

    assert device.timestamp == DAYTIME
    assert device.timestamp.utcoffset() == timedelta(0)
#endregion testCases