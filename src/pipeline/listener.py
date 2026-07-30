from paho.mqtt import client as mqttclient
import src.pipeline.Helper_Config as settings


#requires callback functions so we get a resulting output of whether we do connect to the broker and/or we get a message from it
class Client:

    def __init__(self, host:str, port:int, clientId:str, message_handler):
        self.host = host
        self.port = port
        self.clientId = clientId
        self.client = None
        self.message_handler = message_handler

        #add subscription to topics inside on_connect right away 
    def on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code ==0:

            print("Successfully connected to broker")
            #subscribe to topic right away so on reconnect, it automatically subscribes
            self.subscribe_to_topic(client) 
        else:
            print(f"Failed to connect, reason code: {reason_code}")

    def on_message(self, client, userdata, msg):
        self.message_handler(msg)


    def create_and_connect_client(self) -> mqttclient.Client:

        self.client = mqttclient.Client(callback_api_version=mqttclient.CallbackAPIVersion.VERSION2, client_id=self.clientId)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(self.host, self.port)
        self.client.loop_start()
        return self.client

    
    def subscribe_to_topic(self, mqtt_client:mqttclient.Client):
        
        try:
            result, mid = mqtt_client.subscribe(settings.CLIENT_TOPIC) 
            print(f"Successfully subscribed to {settings.CLIENT_TOPIC}") if result ==0 else print("Could not subscribe to Topics")
        except Exception as e:
            print(f"Did not sucessfully subscribe to Topic due to {e}")
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


                
            


