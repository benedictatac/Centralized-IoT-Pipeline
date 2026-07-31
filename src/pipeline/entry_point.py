import asyncio
from src.pipeline.listener import Client 
from src.models.baseModel import Device
from src.pipeline.storage import create_async_engine, get_db, upsert_device, insert_readings, store_event
import uuid




async def process_payload_insertion(device:Device):
    db = get_db()
    upsert_device()
    insert_readings()




async def main():
    
    #get currently running loop
    loop = asyncio.get_running_loop()

    client_mqtt = Client()




if __name__ == '__main__':

    soemthi