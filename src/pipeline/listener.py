from queue import Empty
from unicodedata import category
from paho import mqtt
from paho.mqtt import client as mqttclient
import os
import time
import json
from dotenv import load_dotenv



load_dotenv()
CLIENT_TOPIC = os.getenv("TOPIC")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
PLACEHOLDER_CLIENT_ID = "Client-ID"
#requires callback functions so we get a resulting output of whether we do connect to the broker and/or we get a message from it

class Client:


    def __init__(self, port, clientId):
        self.port = port
        self.clientId= clientId

    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code ==0:
            print("Successfully connected to broker")
            #subscribe to topic right away so on reconnect, it automatically subscribes
            self.SubscribeToTopic(client) 
        else:
            print(f"Failed to connect, reason code: {reason_code}")


    def on_message(client, userdata, msg):
        print(f"Received message on topic:{msg.topic}")
        print(f"Payload: {msg.payload.decode()}")

    def CreateAndConnectClient(self, host:str, port:int, clientId:str) -> mqttclient.Client:

        client = mqttclient.Client(callback_api_version=mqttclient.CallbackAPIVersion.VERSION2, client_id=clientId)
        
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.loop_start()
        client.connect(host, port)
        client.loop_forever()

        return client


    def SubscribeToTopic(self, mqtt_client:mqttclient.Client):
        
        try:

            result, mid = mqtt_client.subscribe(CLIENT_TOPIC)
            status = print(f"Successfully subscribed to {CLIENT_TOPIC}") if result ==0 else print("Could not subscribe to Topics")
        except Exception as e:
            print(f"Did not sucessfully subscribe to Topic due to {e}")
            mqtt_client.loop_stop()
            


if __name__ == '__main__':


    try:
        clientMqtt = Client(MQTT_PORT,PLACEHOLDER_CLIENT_ID)   
        clientMqtt.CreateAndConnectClient(MQTT_HOST,MQTT_PORT, PLACEHOLDER_CLIENT_ID)
    except Exception as e:
        print(f"Problem occured at {e}")


                
            


