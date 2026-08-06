from importlib import metadata
from os import read
import pathlib
from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Reading, Unit
import uuid
from datetime import datetime
import src.pipeline.Helper_Config
import json
import docker.mosquitto.data
from pathlib import Path
import pytest
import pydantic
from conftest import FILE_PATH, create_device_obj
#region members

DEVICETYPE = DeviceType.CAMERA
DEVICEID = uuid.uuid4()
DEVICENAME = "Charles' device"
DAYTIME = datetime.now()
# STATUS = DeviceStatus.ACTIVE
MOVEMENT = Metric.MOVEMENT
UNIT = Unit.CELSIUS
VALUE = 2.0
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
    bad_device["readings"][0]["value"] = INVALID_VALUE
    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)

def test_invalid_readingvalue(create_device_obj):

    bad_device = create_device_obj.model_dump()
    bad_device["readings"][0]["value"] = INVALID_VALUE

    with pytest.raises(pydantic.ValidationError):
        Device.model_validate(bad_device)
#endregion testCases