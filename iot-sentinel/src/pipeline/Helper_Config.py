
### MAIN TEST HELPER THAT INCLDES FUNCTIONS, ARBRITRARY VALUES AND CONST MEMBERS ### 

from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Unit, Reading
from uuid import uuid4
import enum
import pydantic


def CreateValidDevice(deviceType,deviceUUID, deviceName, date, readings: list[Reading]) -> Device:
    
    try: 
        device = Device(deviceType, deviceUUID, deviceName, date, readings)
        if device == Device:
            print("Device successfully created!")
            return device
    except Exception as e: 
        print(f"Device was not successfully created due to {e}")

     