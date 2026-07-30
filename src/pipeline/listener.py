from paho.mqtt import client as mqttclient
import os
import time
import json

from pydantic import ValidationError
from config import Settings
import logging
from src.models.baseModel import Device 

#connection and message receiving -> sends to processor 
settings = Settings()
device_obj = Device()
CLIENT_TOPIC = settings.TOPIC_DEFAULT
MQTT_PORT = settings.MQTT_PORT
MQTT_HOST = settings.MQTT_HOST
PLACEHOLDER_CLIENT_ID = "Client-ID"

#requires callback functions so we get a resulting output of whether we do connect to the broker and/or we get a message from it
class Client:



    def __init__(self, host:str, port:int, clientId:str):
        self.host = host
        self.port = port
        self.clientId = clientId
        self.client = None

        #add subscription to topics inside on_connect right away 
    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code ==0:

            print("Successfully connected to broker")
            #subscribe to topic right away so on reconnect, it automatically subscribes
            self.SubscribeToTopic(client) 
        else:
            print(f"Failed to connect, reason code: {reason_code}")


    def on_message_topic(self, client, userdata, msg):

        #case of msg being NONE | empty 
        if msg is None or getattr(msg, 'payload', None) is None:
            return

        data = None # initialize to None so it won't have some garbage value 
        try:
            if msg.topic:
                print(f"Received message on topic: {msg.topic}", flush = True)
                data = self.parse_json_payload(msg = msg)
            if data is not None:
                print(f"Parsed data is {data}")
            dataValidated = device_obj.validate_dict(data) 

        except ValidationError as e: 
            print(f"Validation failed. Schema does not correspond")
            print(e.errors())
        except Exception as e: 
            print(f"Error processing message on topic '{getattr(msg, 'topic', 'unknown')}': {e}", flush=True)   

            #parsing to return dict structure 
    def parse_json_payload(self, msg) -> dict | None:
         try: 
            parsed_json = msg.payload.decode("utf-8")
            return json.loads(parsed_json)
         except (UnicodeError, AttributeError) as e: 
            logging.error(f"Failed to decode message on {msg.topic}: payload is not valid UTF-8 text.")
            return None
         except json.JSONDecodeError as err:
            logging.error(f"JSON parsing error on topic '{msg.topic}': {err}")
            logging.debug(f"Raw raw text was: {msg.payload}")
            return None



    def CreateAndConnectClient(self) -> mqttclient.Client:

        self.client = mqttclient.Client(callback_api_version=mqttclient.CallbackAPIVersion.VERSION2, client_id=self.clientId)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message_topic

        self.client.connect(self.host, self.port)
        self.client.loop_start()
        return self.client

    
    def SubscribeToTopic(self, mqtt_client:mqttclient.Client):
        
        try:
            result, mid = mqtt_client.subscribe(CLIENT_TOPIC) 
            print(f"Successfully subscribed to {CLIENT_TOPIC}") if result ==0 else print("Could not subscribe to Topics")
        except Exception as e:
            print(f"Did not sucessfully subscribe to Topic due to {e}")
            mqtt_client.loop_stop()
            
        
         


if __name__ == '__main__':

    print("Script started!")

    try:
        clientMqtt = Client(MQTT_HOST,MQTT_PORT,PLACEHOLDER_CLIENT_ID)   
        clientMqtt.CreateAndConnectClient()


        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting client...")
        if clientMqtt.client:
            clientMqtt.client.loop_stop()
            clientMqtt.client.disconnect()
        print("Script exited cleanly.")
    except Exception as e:
        print(f"Problem occured at {e}")


                
            


