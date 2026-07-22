from asyncio.windows_events import NULL
from dataclasses import dataclass
from multiprocessing import Value
from uuid import uuid4
from xmlrpc.client import boolean
from pydantic import UUID4, BaseModel, Field 
import string
from datetime import datetime
from enum import Enum



class DeviceType(Enum):
    CAMERA = "CAMERA"
    LIGHTBULB = "LIGHTBULB"
    THERMOSTAT = "THERMOSTAT"
    SPEAKER = "SPEAKER"


class Metric(Enum):
    MOVEMENT = "MOVEMENT"
    TEMPERATURE = "TEMPERATURE"
    VOLUME = "VOLUME"

class Unit(Enum):
    KMPERHOUR = "KMPERHOUR"
    CELSIUS = "CELSIUS"
    DECIBEL = "DECIBEL"

class DeviceStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class Reading(BaseModel):
    
    metric: Metric
    unit : Unit
    value : float

class Device(BaseModel):

    device_type : DeviceType
    device_id : UUID4
    device_name : str
    timestamp : datetime
    status: DeviceStatus
    readings : list[Reading] = Field(default_factory=list)


if __name__ ==  '__main__':
    
    device = Device(device_type = DeviceType.CAMERA, device_id=uuid4(), device_name="something",  timestamp=datetime.now(), status = DeviceStatus.ACTIVE, readings = [Reading(metric = Metric.MOVEMENT, unit = Unit.CELSIUS, value= 2.0)])


    if device != NULL:
        print("We good chief")