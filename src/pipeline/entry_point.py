import asyncio
from src.pipeline.listener import Client 
from src.models.baseModel import Device
from src.pipeline.storage import create_async_engine, get_db, upsert_device, insert_readings, store_event
import uuid
from processor import process_message
from paho.mqtt import client as mqtt_client
from src.pipeline.Helper_Config import PLACEHOLDER_CLIENT_ID
from config import Settings


async def process_payload_insertion(device: Device):
    if device is None:
        return 

    try:
        db = get_db()

        # Wrap in await if storage layer is async
        # If storage functions are standard synchronous functions, wrap with:
        # await asyncio.to_thread(upsert_device, device, db)
        await upsert_device(device, db)
        await insert_readings(device, db)

    except Exception as e:
        print(f"Error inserting device payload into DB: {e}")







async def main():
    
    #get currently running loop
    loop = asyncio.get_running_loop()
    settings = Settings()
    
    client = Client(settings.mqtt_host, settings.mqtt_port, PLACEHOLDER_CLIENT_ID,process_message,process_payload_insertion, loop, settings)

    created_client= client.create_and_connect_client()
    print("MQTT listener started. Waiting for messages...")
    await asyncio.Event().wait()




if __name__ == '__main__':

  try:
      asyncio.run(main())
  except KeyboardInterrupt: 
      print("\nShutdown complete.")