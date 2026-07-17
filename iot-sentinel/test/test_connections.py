from ast import main
from paho.mqtt import client as mqtt_client
import os 
import redis
import sqlalchemy


#variables for MQTT broker
BROKER = os.getenv("MQTT_NAME", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
CLIENT_ID = "client-Id"

#variables for Redis
BROKER2 = os.getenv("RDS_NAME", "localhost")
PORT2 = int (os.getenv("RDS_PORT", 6739))
CLIENT_ID2 = "client-ID2"


#variables for POSTGRESQL


def connect_mqtt():
   client = mqtt_client.Client(
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2, #when creating a client must indicate the callback api version which in this case is v2

        client_id=CLIENT_ID
    )
   try: 
       result = client.connect(BROKER, PORT, keepalive=60)
       if result == 0:
            print("Client successfully connected")
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


        
if __name__ == '__main__':
    connect_mqtt()
    connect_redis()
    


