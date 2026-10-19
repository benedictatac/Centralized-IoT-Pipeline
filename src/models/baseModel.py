
#file organises the pydantic model thats going to be the main structure of the data 

from dataclasses import dataclass
from multiprocessing import Value
from uuid import uuid4
from xmlrpc.client import boolean
from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator
import string
from datetime import datetime, timezone
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

    #every timestamp leaves this model as timezone-aware UTC so it matches the TIMESTAMPTZ columns
    #naive timestamps (no offset in the payload) are assumed to already be UTC
    @field_validator("timestamp")
    @classmethod
    def normalize_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

class AlertReading(BaseModel):
    id : UUID4
    device_id: UUID4 # from which device it comes form
    reading : Reading # what readings it gave (showcases the specific anomaly value )


class ReadingResponse(BaseModel):
    id: UUID4
    device_id: UUID4
    metric:str
    unit:str
    value:float
    timestamp:datetime
    alerts: list[AlertReading] = Field(default_factory = list, nullable = True) # if no alerts, can be value
    model_config = ConfigDict(from_attributes=True)



    