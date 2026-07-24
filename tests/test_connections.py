from ast import main
import asyncio
from re import DEBUG
import asyncpg.connection
from paho.mqtt import client as mqtt_client
import os 
import redis
import asyncpg
import time
import json 



data = {
    
    "deviceName":"Anglo",
    "deviceType" : "camera", 
    "captureType" : ["pictures", "videos"]
    }
#variables for MQTT broker
BROKER = os.getenv("MQTT_NAME", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
CLIENT_ID = "client-Id"

#variables for Redis
BROKER2 = os.getenv("RDS_NAME", "localhost")
PORT2 = int (os.getenv("RDS_PORT", 6739))
CLIENT_ID2 = "client-ID2"


#variables for POSTGRESQL



#handles incoming messages
def on_message(client,userdata, msg):
        print(f" Received message on topic: {msg.topic}")
        print(f"   Payload: {msg.payload.decode()}")

def connect_mqtt():
   client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2, #when creating a client must indicate the callback api version which in this case is v2

        client_id=CLIENT_ID
    )
   client.on_message= on_message
   

   try: 
       result = client.connect(BROKER, PORT, keepalive=60)
       if result == 0:
            print("Client successfully connected to mosquitto server")
            return client
   except Exception as e:
            print(f"Error: Could not connect to broker. Details: {e}")
            return None    



def connect_redis():
    client = redis.Redis(BROKER2, PORT2, socket_keepalive=60)

    try:
        response = client.ping()
        if response: 
            print("Client connected to Redis server")
    except Exception as e: 
            print(f"Client Redis did not successfully connect due to {e}")

async def connect_db():

    
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "mysecretlocalpassword")
    db_port = os.getenv("DB_PORT", 5432)
    db_name = os.getenv("DB_NAME", "iot_sentinel")
        
    try:
        client = await asyncpg.connect(f"postgresql://{db_user}:{db_password}@localhost:{db_port}/{db_name}")  
        if client: 
            print("Connection to SQL database server successful")
    
    except Exception as e:
            print(f"Client not connected due to {e}")
            
if __name__ == '__main__':
    connect_redis()
    asyncio.run(connect_db())

    client = connect_mqtt()

    if client: 
        #start network loop
        client.loop_start()

        #subscribe to the topic
        client.subscribe("house/livingRoom/windgust")
        time.sleep(0.5) 

        msg_info = client.publish(
        topic="house/livingRoom/windgust", 
        payload=json.dumps(data), 
        qos=1
    )
        msg_info.wait_for_publish(timeout=2.0)

        time.sleep(1.0)
        # Clean up
        client.loop_stop()
        client.disconnect()