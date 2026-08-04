from dataclasses import dataclass
from multiprocessing import Value
from uuid import uuid4
from xmlrpc.client import boolean
from pydantic import UUID4, BaseModel, ConfigDict, Field 
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

class ReadingResponse(BaseModel):
    id: UUID4
    device_id: UUID4
    metric:str
    unit:str
    value:float
    timestamp:datetime
    model_config = ConfigDict(from_attributes=True)