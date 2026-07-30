
### MAIN TEST HELPER THAT INCLDES FUNCTIONS, ARBRITRARY VALUES AND CONST MEMBERS ### 

from multiprocessing import Value
from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Unit, Reading
from uuid import UUID, uuid4
import enum
import pydantic
import json
from pathlib import Path
from config import Settings as settings
#trying out 3 different types of testing in this case, for personal and learning reasons



#region env variables from settings

CLIENT_TOPIC = settings.TOPIC_DEFAULT
MQTT_PORT = settings.MQTT_PORT
MQTT_HOST = settings.MQTT_HOST
PLACEHOLDER_CLIENT_ID = "Client-ID"
#endregion


#specific method with hardcoded values from dev user's 
def CreateValidDevice(deviceType,deviceUUID, deviceName, date, readings: list[Reading]) -> Device:
    
        device = Device(device_type = deviceType, device_uuid = deviceUUID, device_name = deviceName, timestamp=date, readings =readings)
        return device


#using Pydantic already built in function in parsing json 
# already handles type conversion, validation, and error  reporting automatically when given the types models 
def Create_Device_From_Json2(file_path: Path) -> Device:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return Device(**data)

