# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run device-producer
#
# Connection management: the device logic is started by the on_connect callback, only when the connection has been
# accepted by the broker. In particular:
# - the retained Device Info is published directly inside on_connect: it is a single and quick operation,
#   so it does not block the Paho network loop, and it is automatically re-published at each reconnection;
# - the telemetry publishing is a long-running loop, so it is executed in a dedicated thread. The callback must return
#   quickly since it is executed by the Paho network loop, that is also responsible for sending the queued messages
#   and the keepalive pings.
# See simple_producer.py and the "Asynchronous Model of Paho" section of the README for a detailed explanation.

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
from mqtt_playground.dto.message_descriptor import MessageDescriptor
from mqtt_playground.dto.device_descriptor import DeviceDescriptor
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any
import threading
import time
import uuid

# Configuration variables
client_id = "clientId0001-Producer"
sensor_topic = "sensor/temperature"
device_base_topic = "device"
message_limit = 1000

# Create a Device Descriptor with a random UUID (Universally Unique Identifier - Standardized 128-bit format)
device_descriptor = DeviceDescriptor(str(uuid.uuid1()), "PYTHON-ACME_CORPORATION", "0.1-beta")

# Thread running the telemetry publishing logic (None until the first successful connection)
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

    # Publish the retained Device Info with the dedicated method. It is a single publish, so it can be safely
    # executed inside the callback: the message is sent by the network loop as soon as the callback returns
    publish_device_info(client)

    # Start the telemetry publishing. The callback returns immediately, leaving the network loop free to work
    start_publishing(client)


def publish_device_info(mqtt_client: mqtt.Client) -> None:
    # MQTT Paho Publish method with all the available parameters
    # mqtt_client.publish(topic, payload=None, qos=0, retain=False)

    # Build the target topic and the payload string
    target_topic = "{0}/{1}/info".format(device_base_topic, device_descriptor.device_id)

    # Serialize the Device Descriptor to a JSON string
    device_payload_string = device_descriptor.to_json()

    # Publish the Device Descriptor to the target topic
    mqtt_client.publish(target_topic, device_payload_string, 0, True)

    # Print the Device Info Published
    print(f"Device Info Published: Topic: {target_topic} Payload: {device_payload_string}")


def start_publishing(mqtt_client: mqtt.Client) -> None:
    global publisher_thread

    # on_connect is called again at each automatic reconnection: avoid starting a second publishing thread
    if publisher_thread is not None and publisher_thread.is_alive():
        print("Publishing thread already running ...")
        return

    # Start the telemetry publishing in a dedicated thread (daemon to not block the process exit, e.g., with CTRL+C)
    publisher_thread = threading.Thread(target=publish_telemetry, args=(mqtt_client,), daemon=True)
    publisher_thread.start()


def publish_telemetry(mqtt_client: mqtt.Client) -> None:

    # Create Demo Temperature Sensor
    temperature_sensor = TemperatureSensor()

    # Build the target topic
    data_topic = "{0}/{1}/{2}".format(device_base_topic, device_descriptor.device_id, sensor_topic)

    # Publish messages with the temperature value
    for message_id in range(message_limit):

        # Measure the temperature
        temperature_sensor.measure_temperature()

        # Create the payload String in JSON format with the temperature value
        payload_string = MessageDescriptor(int(time.time()),
                                           "TEMPERATURE_SENSOR",
                                           temperature_sensor.temperature_value).to_json()

        # Publish the message to the target topic
        mqtt_client.publish(data_topic, payload_string)

        # Print the message sent
        print(f"Message Sent: {message_id} Topic: {data_topic} Payload: {payload_string}")
        time.sleep(1)

    # Disconnect from the broker when all the messages have been sent: this also stops the loop_forever in main()
    mqtt_client.disconnect()


def main() -> None:

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Attach Paho OnConnect Callback Method
    mqtt_client.on_connect = on_connect

    # Connect to the target MQTT Broker
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Run the MQTT Client network loop in the main thread with the blocking loop_forever method.
    # The device logic is started by the on_connect callback, while loop_forever returns
    # when disconnect() is called (at the end of the publishing or if the connection is refused)
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
