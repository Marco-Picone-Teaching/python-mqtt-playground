# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run json-consumer

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.dto.message_descriptor import MessageDescriptor
import paho.mqtt.client as mqtt
import json
import traceback

# Configuration variables
client_id = "clientId0001-Consumer"
default_topic = "device/temperature"


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client, userdata, flags, reason_code, properties):

    # Print the connection result contained in the variable reason_code
    print("Connected with result code " + str(reason_code))

    # After the connection is established, we subscribe to the default topic
    client.subscribe(default_topic)

    # Print the topic we are subscribed to
    print("Subscribed to: " + default_topic)


# Define a callback method to receive asynchronous messages
def on_message(client, userdata, message):

    # If the message received is in the default topic, we print the message
    if message.topic == default_topic:
        try:
            # Decode the message payload from an array of bytes to a string
            message_payload = str(message.payload.decode("utf-8"))

            # Create a MessageDescriptor object from the JSON payload
            message_descriptor = MessageDescriptor(**json.loads(message_payload))

            # Print the message received from the broker
            print(
                f"Received IoT Message: Topic: {message.topic} Timestamp: {message_descriptor.timestamp} Type: {message_descriptor.value_type} Value: {message_descriptor.value}")
        except Exception as e:
            # Print the exception traceback
            traceback.print_exc()

            # Print the error message
            print(f"Error processing message: {e}")


def main():

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Full MQTT client creation with all the parameters. Since Paho 2.x the Callback API version is mandatory,
    # while the ClientId should be unique
    # mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=None,
    #                           userdata=None, protocol=mqtt.MQTTv311, transport="tcp")

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Attack Paho OnMessage Callback Method
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect

    # Connect to the target MQTT Broker
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
