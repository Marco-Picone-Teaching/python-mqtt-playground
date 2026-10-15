# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run device-producer

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
from mqtt_playground.dto.message_descriptor import MessageDescriptor
from mqtt_playground.dto.device_descriptor import DeviceDescriptor
import paho.mqtt.client as mqtt
import time
import uuid

# Configuration variables
client_id = "clientId0001-Producer"
sensor_topic = "sensor/temperature"
device_base_topic = "device"
message_limit = 1000


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client, userdata, flags, reason_code, properties):
    # Print the connection result contained in the variable reason_code
    print("Connected with result code " + str(reason_code))


def publish_device_info(mqtt_client, device_descriptor):
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


def main():

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Attach Paho OnMessage Callback Method
    mqtt_client.on_connect = on_connect

    # Connect to the target MQTT Broker
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Start the MQTT Client with the loop_start method to process the callbacks in a separate thread
    mqtt_client.loop_start()

    # Create Demo Temperature Sensor & Device Descriptor
    temperature_sensor = TemperatureSensor()

    # Create a Device Descriptor with a random UUID (Universally Unique Identifier - Standardized 128-bit format)
    device_descriptor = DeviceDescriptor(str(uuid.uuid1()), "PYTHON-ACME_CORPORATION", "0.1-beta")

    # Publish the Device Info with the dedicated method
    publish_device_info(mqtt_client, device_descriptor)

    # Publish messages with the temperature value
    for message_id in range(message_limit):

        # Measure the temperature
        temperature_sensor.measure_temperature()

        # Create the payload String in JSON format with the temperature value
        payload_string = MessageDescriptor(int(time.time()),
                                           "TEMPERATURE_SENSOR",
                                           temperature_sensor.temperature_value).to_json()

        # Build the target topic
        data_topic = "{0}/{1}/{2}".format(device_base_topic, device_descriptor.device_id, sensor_topic)

        # Publish the message to the target topic
        mqtt_client.publish(data_topic, payload_string)

        # Print the message sent
        print(f"Message Sent: {message_id} Topic: {data_topic} Payload: {payload_string}")
        time.sleep(1)

    # Stop the MQTT Client with the loop_stop method in order to stop the processing of the callbacks
    mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
