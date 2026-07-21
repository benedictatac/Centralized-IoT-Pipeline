from src.models.baseModel import BaseModel, Device, DeviceType, Metric, Unit
import pydantic
import pytest
from uuid import uuid4 
from datetime import datetime

# members


    





if __name__ == '__main__': 


    device = Device(device_type= DeviceType.CAMERA, device_id=uuid4(), device_name="John",date = datetime(), readings = [Reading(metric = Metric.MOVEMENT,unit = Unit.BOOLEAN, value = 2.0)])

