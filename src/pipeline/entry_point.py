import asyncio

from sqlalchemy.orm import session
from src.pipeline.listener import Client 
from src.models.baseModel import Device
from src.pipeline.storage import create_async_engine, get_db, upsert_device, insert_readings, store_event, async_session
from src.pipeline.processor import process_message
from src.pipeline.Helper_Config import PLACEHOLDER_CLIENT_ID
from src.pipeline.cache import upsert_data


from config import Settings


async def store_device(device: Device):
    if device is None:
        return 

    try:
        async with async_session() as session:
            await store_event(device=device, session=session)
        # Wrap in await if storage layer is async
        # If storage functions are standard synchronous functions, wrap with:
        # await asyncio.to_thread(upsert_device, device, db)
        
    except Exception as e:
        print(f"Error inserting device payload into DB: {e}")
    try:
         await upsert_data(device=device)
    except Exception as e:
        print(f"Redis Caching failed due to: {e}")







async def main():
    
    #get currently running loop
    loop = asyncio.get_running_loop()
    settings = Settings()
    
    def handle_message(msg):
        device = process_message(msg)
        if device: 
            asyncio.run_coroutine_threadsafe(store_device(device), loop)


    client = Client(settings.mqtt_host, settings.mqtt_port, PLACEHOLDER_CLIENT_ID,process_message, settings)
    created_client= client.create_and_connect_client()
    print("MQTT listener started. Waiting for messages...")
    await asyncio.Event().wait()




if __name__ == '__main__':

  try:
      asyncio.run(main())
  except KeyboardInterrupt: 
      print("\nShutdown complete.")