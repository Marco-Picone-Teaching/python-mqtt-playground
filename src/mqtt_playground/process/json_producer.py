# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run json-producer
#
# Connection management: the publishing logic is started by the on_connect callback in a dedicated thread,
# only when the connection has been accepted by the broker. The callback must return quickly since it is executed
# by the Paho network loop, that is also responsible for sending the queued messages and the keepalive pings.
# See simple_producer.py and the "Asynchronous Model of Paho" section of the README for a detailed explanation.

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
from mqtt_playground.dto.message_descriptor import MessageDescriptor
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any
import threading
import time

# Configuration variables
client_id = "clientId0001-Producer"
default_topic = "device/temperature"
message_limit = 1000

# Thread running the publishing logic (None until the first successful connection)
publisher_thread: threading.Thread | None = None


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
               reason_code: ReasonCode, properties: Properties | None) -> None:
    # Check if the broker has refused the connection (e.g., wrong credentials or not authorized client id)
    if reason_code.is_failure:
        print("Connection refused with result code " + str(reason_code))
        # Stop the client (and the loop_forever in the main thread) since retrying would fail again
        client.disconnect()
        return

    print("Connected with result code " + str(reason_code))

    # Start the publishing logic. The callback returns immediately, leaving the network loop free to work
    start_publishing(client)


def start_publishing(mqtt_client: mqtt.Client) -> None:
    global publisher_thread

    # on_connect is called again at each automatic reconnection: avoid starting a second publishing thread
    if publisher_thread is not None and publisher_thread.is_alive():
        print("Publishing thread already running ...")
        return

    # Start the publishing logic in a dedicated thread (daemon to not block the process exit, e.g., with CTRL+C)
    publisher_thread = threading.Thread(target=publish_messages, args=(mqtt_client,), daemon=True)
    publisher_thread.start()


def publish_messages(mqtt_client: mqtt.Client) -> None:

    # Create Demo Temperature Sensor
    temperature_sensor = TemperatureSensor()

    # MQTT Paho Publish method with all the available parameters
    # mqtt_client.publish(topic, payload=None, qos=0, retain=False)

    # Publish messages with the temperature value
    for message_id in range(message_limit):

        # Measure the temperature
        temperature_sensor.measure_temperature()

        # Create the payload String in JSON format with the temperature value
        payload_string = MessageDescriptor(int(time.time()),
                                           "TEMPERATURE_SENSOR",
                                           temperature_sensor.temperature_value).to_json()

        # Publish the message to the default topic
        mqtt_client.publish(default_topic, payload_string)

        # Print the message sent
        print(f"Message Sent: {message_id} Topic: {default_topic} Payload: {payload_string}")

        # Wait for 1 second before sending the next message
        time.sleep(1)

    # Disconnect from the broker when all the messages have been sent: this also stops the loop_forever in main()
    mqtt_client.disconnect()


def main() -> None:

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Full MQTT client creation with all the parameters. Since Paho 2.x the Callback API version is mandatory,
    # while the ClientId should be unique
    # mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=None,
    #                           userdata=None, protocol=mqtt.MQTTv311, transport="tcp")

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Attach Paho OnConnect Callback Method
    mqtt_client.on_connect = on_connect

    # Connect to the target MQTT Broker
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Run the MQTT Client network loop in the main thread with the blocking loop_forever method.
    # The publishing logic is started by the on_connect callback, while loop_forever returns
    # when disconnect() is called (at the end of the publishing or if the connection is refused)
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
