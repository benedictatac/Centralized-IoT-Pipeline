
#file organises the pydantic model thats going to be the main structure of the data 

from dataclasses import dataclass
from multiprocessing import Value
from uuid import uuid4
from xmlrpc.client import boolean
from pydantic import UUID4, BaseModel, ConfigDict, Field 
import string
from datetime import datetime
from enum import Enum



class DeviceType(Enum):
    CAMERA = "Camera"
    LIGHTBULB = "LightBulb"
    THERMOSTAT = "Thermostat"
    SPEAKER = "Speaker"


class Metric(Enum):
    MOVEMENT = "Movement"
    STATE = "State"
    TEMPERATURE = "Temperature"
    VOLUME = "Volume"

class Unit(Enum):
    KMPERHOUR = "kmPerHour"
    BOOLEAN = "Boolean"
    CELSIUS = "Celsius"
    DECIBEL = "Decibel"


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