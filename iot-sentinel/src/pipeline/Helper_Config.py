
### MAIN TEST HELPER THAT INCLDES FUNCTIONS, ARBRITRARY VALUES AND CONST MEMBERS ### 

from multiprocessing import Value
from src.models.baseModel import BaseModel, Device, DeviceStatus, DeviceType, Metric, Unit, Reading
from uuid import UUID, uuid4
import enum
import pydantic
import json
from pathlib import Path
#trying out 3 different types of testing in this case, for personal and learning reasons


#specific method with hardcoded values from dev user's 
def CreateValidDevice(deviceType,deviceUUID, deviceName, date, readings: list[Reading]) -> Device:
    
    try: 
        device = Device(deviceType, deviceUUID, deviceName, date, readings)
        if device == Device:
            print("Device successfully created!")
            return device
    except Exception as e: 
        print(f"Device was not successfully created due to {e}")


#creating device from json values 
def create_device_from_json(json_str:str) -> Device: 
    data = json.loads(json_str)


    readings = [
        Reading(
            metric = Metric(item["metric"]), 
            unit = Unit(item["unit"]), 
            value = item["value"])
            
        for item in data.get("readings", [])
        ]

    return Device(
            device_type=DeviceType(data["device_type"]), 
            device_id = UUID(data["device_id"]), 
            device_name=data["device_name"], 
            timestamp=data["timestamp"], 
            status = DeviceStatus(data["status"]), 
            readings=readings
        )


#using Pydantic already built in function in parsing json 
# already handles type conversion, validation, and error  reporting automatically when given the types models 
def create_device_from_json2(file_path: Path) -> Device:


    with open(file_path, 'r') as f:
        data = json.load(f)
    return Device(**data)

