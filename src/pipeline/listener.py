from paho.mqtt import client as mqttclient
from config import Settings
import asyncio

#requires callback functions so we get a resulting output of whether we do connect to the broker and/or we get a message from it
class Client:

    def __init__(self, host:str, port:int, clientId:str, message_handler, process_payload_handler, loop:asyncio.AbstractEventLoop, settings:Settings):
        self.host = host
        self.port = port
        self.clientId = clientId
        self.client = None
        self.message_handler = message_handler
        self.process_payload_handler = process_payload_handler
        self.loop = loop
        self.settings = settings

        #add subscription to topics inside on_connect right away 
    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code ==0:

            print("Successfully connected to broker")
            #subscribe to topic right away so on reconnect, it automatically subscribes
            self.subscribe_to_topic(client) 
        else:
            print(f"Failed to connect, reason code: {reason_code}")

    def on_message(self, client, userdata, msg):
        device = self.message_handler(msg)

        if device is not None:
            asyncio.run_coroutine_threadsafe(
                self.process_payload_handler(device), 
                self.loop
            )

    def async_payload_func(self):
        self.process_payload_handler()
    def create_and_connect_client(self) -> mqttclient.Client:

        self.client = mqttclient.Client(callback_api_version=mqttclient.CallbackAPIVersion.VERSION2, client_id=self.clientId)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(self.host, self.port)
        print(f"Connecting to host: '{self.host}' on port: {self.port}")

        self.client.loop_start()
        return self.client

    
    def subscribe_to_topic(self, mqtt_client:mqttclient.Client):
        
        try:
            result, mid = mqtt_client.subscribe(self.settings.topic_default) 
            if result == 0:
                print(f"Successfully subscribed to {self.settings.topic_default}")
            else:
                print(f"Could not subscribe to topic {self.settings.topic_default}")
        except Exception as e:
            print(f"Did not successfully subscribe to Topic due to: {e}")
            mqtt_client.loop_stop()
            
        
         


# if __name__ == '__main__':

#     print("Script started!")

#     try:
#         clientMqtt = Client(MQTT_HOST,MQTT_PORT,PLACEHOLDER_CLIENT_ID)   
#         clientMqtt.create_and_connect_client()


#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\nDisconnecting client...")
#         if clientMqtt.client:
#             clientMqtt.client.loop_stop()
#             clientMqtt.client.disconnect()
#         print("Script exited cleanly.")
#     except Exception as e:
#         print(f"Problem occured at {e}")


                
            


