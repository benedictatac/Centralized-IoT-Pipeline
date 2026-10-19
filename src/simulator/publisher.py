# MQTT connection the simulator publishes through

from paho.mqtt import client as mqttclient
from config import Settings


#must differ from the listener's PLACEHOLDER_CLIENT_ID ("Client-ID"): when a second client connects with an ID
#that is already in use, the broker disconnects the first one, so reusing it would knock the listener offline
PUBLISHER_CLIENT_ID = "iot-simulator"

#QoS 1: the broker confirms (PUBACK) every message it receives, so the shutdown can wait for the last one
PUBLISH_QOS = 1


def on_connect(client, userdata, flags, reason_code, properties):
    #same check as the listener: a VERSION2 ReasonCode compares equal to 0 on success
    if reason_code == 0:
        print(f"Simulator connected to broker as '{PUBLISHER_CLIENT_ID}'")
    else:
        print(f"Simulator failed to connect, reason code: {reason_code}")


#Settings reads .env from the current working directory, so start the simulator from the repo root
def create_publisher() -> mqttclient.Client:
    settings = Settings()

    client = mqttclient.Client(callback_api_version=mqttclient.CallbackAPIVersion.VERSION2, client_id=PUBLISHER_CLIENT_ID)
    client.on_connect = on_connect

    #raises ConnectionRefusedError right away if the broker isn't running
    client.connect(settings.mqtt_host, settings.mqtt_port)
    print(f"Connecting to host: '{settings.mqtt_host}' on port: {settings.mqtt_port}")

    #background network thread: sends the queued messages and receives the broker's acknowledgements
    client.loop_start()
    return client


#returns the MQTTMessageInfo, the main loop keeps the latest one so the shutdown can wait_for_publish() on it
def publish(client: mqttclient.Client, topic: str, payload: str) -> mqttclient.MQTTMessageInfo:
    return client.publish(topic, payload, qos=PUBLISH_QOS)
