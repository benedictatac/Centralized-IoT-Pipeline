import redis.asyncio as redis
from config import Settings
from src.models.baseModel import Device
import json
# A Redis client connection (created once at module scope, same pattern as your SQLAlchemy engine)
# A function that takes a device and writes its latest readings to Redis
# The redis library supports async with redis.asyncio — use that since your pipeline is async



settings = Settings()


#password authenticates as the "default" redis user (set by --requirepass in docker-compose.yml)
conn = redis.Redis(host = settings.rds_host, port = settings.rds_port, password = settings.rds_password, decode_responses=True)


async def upsert_data(device:Device):

    key = f"device:{device.device_id}:latest"

    #since we require serialization from python obj to string var (json stirng). 
    #then convert pydantic model into standard python dict
    #basically Pydantic -> python obj -> string var
    #mode="json" turns the Metric/Unit enums into their string values, json.dumps can't serialize Enum objects
    value = json.dumps([reading.model_dump(mode="json") for reading in device.readings])
     
    await conn.set(key,value)
    await conn.expire(key, 86400)