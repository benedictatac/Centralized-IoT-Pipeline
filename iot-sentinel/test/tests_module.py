from importlib import metadata
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
MOVEMENT = Reading.metric =Metric.MOVEMENT
UNIT = Reading.unit = Unit.CELSIUS
VALUE = 2.0
READING = [MOVEMENT, UNIT, VALUE]

#endregion

#region testCases
def test_device_creation_with_jsonFile_Valid():

        device = src.pipeline.Helper_Config.create_device_from_json2(FILE_PATH)
        assert device is not None
        assert isinstance(device, Device)

def test_device_creation_with_values_Valid():

    device = Device(device_type=DEVICETYPE, device_id=DEVICEID, device_name=DEVICENAME,
                    timestamp=DAYTIME, status=STATUS, readings = [Reading(metric=MOVEMENT, unit=UNIT, value=VALUE)])
#endregion testCases