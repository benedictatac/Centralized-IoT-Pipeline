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
    STATE = "STATE"
    TEMPERATURE = "TEMPERATURE"
    VOLUME = "VOLUME"

class Unit(Enum):
    KMPERHOUR = "KMPERHOUR"
    BOOLEAN = "BOOLEAN"
    CELSIUS = "CELSIUS"
    DECIBEL = "DECIBEL"

# class DeviceStatus(Enum):
#     ACTIVE = True
#     INACTIVE = False

class Reading(BaseModel):
    
    metric: Metric
    unit : Unit
    value : float

class Device(BaseModel):

    device_type : DeviceType
    device_id : UUID4
    device_name : str
    timestamp : datetime
    readings : list[Reading] = Field(default_factory=list)

    @classmethod
    def validate_dict(cls, data:dict) -> "Device":
        return cls.model_validate(data)