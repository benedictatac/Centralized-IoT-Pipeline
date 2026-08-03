import redis.asyncio as redis
from config import Settings
from src.models.baseModel import Device
import json
# A Redis client connection (created once at module scope, same pattern as your SQLAlchemy engine)
# A function that takes a device and writes its latest readings to Redis
# The redis library supports async with redis.asyncio — use that since your pipeline is async



settings = Settings()


conn = redis.Redis(host = settings.rds_host, port = settings.rds_port,decode_responses=True)


async def upsert_data(device:Device):

    key = f"device:{device.device_id}:latest"

    #since we require serialization from python obj to string var (json stirng). 
    #then convert pydantic model into standard python dict
    #basically Pydantic -> python obj -> string var 
    value = json.dumps([reading.model_dump() for reading in device.readings])

    await conn.set(key,value)
    await conn.expire(key, 86400)