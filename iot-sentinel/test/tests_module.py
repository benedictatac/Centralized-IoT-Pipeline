from importlib import metadata
from os import read
import pathlib

from click import File
from sklearn import metrics
from src.models.baseModel import BaseModel, Device, DeviceStatus, DeviceType, Metric, Reading, Unit
import pydantic
import pytest
import uuid
from datetime import datetime
import src.pipeline.Helper_Config
import json
import docker.mosquitto.data
from pathlib import Path

#region members

BASE_DIR = Path(__file__).parent.parent
FILE_PATH = BASE_DIR / "docker" / "mosquitto" / "data" / "randomData.json"
DEVICETYPE = DeviceType.CAMERA
DEVICEID = uuid.uuid4()
DEVICENAME = "Charles' device"
DAYTIME = datetime.now()
STATUS = DeviceStatus.ACTIVE
MOVEMENT = Metric.MOVEMENT
UNIT = Unit.CELSIUS
VALUE = 2.0
INVALID_VALUE = "BANANA"
#endregion

#region testCases

@pytest.fixture
def test_createDevice():
       return  Device(device_type=DEVICETYPE, device_id=DEVICEID, device_name=DEVICENAME,
                    timestamp=DAYTIME, status=STATUS, readings = [Reading(metric=MOVEMENT, unit=UNIT, value=VALUE)])
      
#keep this since its an integration test for later 
def test_device_creation_with_jsonFile_Valid():

        device = src.pipeline.Helper_Config.Create_Device_From_Json2(FILE_PATH)
        assert device is not None
        assert isinstance(device, Device)

def test_device_creation_with_values_Valid():

    device = Device(device_type=DEVICETYPE, device_id=DEVICEID, device_name=DEVICENAME,
                    timestamp=DAYTIME, status=STATUS, readings = [Reading(metric=MOVEMENT, unit=UNIT, value=VALUE)])

    assert device is not None
    assert isinstance(device, Device)
    assert device.device_type == DEVICETYPE
    assert device.device_id == DEVICEID
    assert device.device_name == DEVICENAME
    assert device.timestamp == DAYTIME
    assert device.status == STATUS
    assert device.readings[0].metric == MOVEMENT
    assert device.readings[0].unit == UNIT
    assert device.readings[0].value == VALUE


def test_device_creation_with_values_Invalid(test_createDevice):
   
     test_createDevice.device_Type = INVALID_VALUE
     with pytest.raises(pydantic.ValidationError):
         test_createDevice
        

#endregion testCases