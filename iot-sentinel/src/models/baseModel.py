from xmlrpc.client import boolean
from pydantic import UUID4, BaseModel, Field 
import string
from datetime import datetime
from enum import Enum, StrEnum

from pydantic_core.core_schema import uuid_schema



class DeviceType(StrEnum):
    CAMERA = "camera"
    LIGHTBULB = "lightbulb"
    THERMOSTAT = "thermostat"
    SPEAKER = "speaker"

class Metric(StrEnum):
    MOVEMENT = "movement"
    STATE = "state"
    TEMPERATURE = "temperature"
    VOLUME = "volume"

class Unit(StrEnum):
    SPEED = "speed"
    BOOLEAN = "boolean"
    CELSIUS = "celsius"
    DECIBEL = "decibel"


class Reading(BaseModel):
    
    metric: Metric
    unit : Unit
    value : float

class Device(BaseModel):

    device_type : DeviceType
    device_id : UUID4
    device_name : str
    timestamp : datetime
    readings : list[Reading]



