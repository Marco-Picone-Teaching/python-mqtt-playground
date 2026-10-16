# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run mqtt-smart-object-controller

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.dto.action_descriptor import ActionDescriptor
from mqtt_playground.dto.device_descriptor import DeviceDescriptor
from mqtt_playground.dto.event_descriptor import EventDescriptor
from mqtt_playground.dto.message_descriptor import MessageDescriptor
import json
import threading

# Configuration variables
client_id = "clientId0001-Consumer"
target_monitored_device = "device001"
device_info_topic = f'device/{target_monitored_device}/info'
device_telemetry_topic = f'device/{target_monitored_device}/telemetry/#'
device_event_topic = f'device/{target_monitored_device}/event/#'
device_action_topic = f'device/{target_monitored_device}/action/switch'
TEMPERATURE_LIMIT = 37

# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
               reason_code: ReasonCode, properties: Properties | None) -> None:

    # Print the connection result contained in the variable reason_code
    print("Connected with result code " + str(reason_code))

    # After the connection is established, subscribe to the device info and data topics
    client.subscribe(device_info_topic)
    client.subscribe(device_telemetry_topic)
    client.subscribe(device_event_topic)

    # Print the topics we are subscribed to
    print("Subscribed to: " + device_info_topic)
    print("Subscribed to: " + device_telemetry_topic)
    print("Subscribed to: " + device_event_topic)


# Define a callback method to receive asynchronous messages
def on_message(client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:

    # If the message received is in the device info topic
    # We use the MQTT Paho topic_matches_sub method to match the topic with the device info topic
    if mqtt.topic_matches_sub(device_info_topic, message.topic):
        handle_device_info_message(message)
    # If the message received is in the data topic
    # We use the MQTT Paho topic_matches_sub method to match the topic with the device info topic
    elif mqtt.topic_matches_sub(device_telemetry_topic, message.topic):
        handle_device_telemetry_message(client, message)
    elif mqtt.topic_matches_sub(device_event_topic, message.topic):
        handle_event_message(message)
    # If the message received is in an unmanaged topic
    else:
        print("Unmanaged Topic !")

def handle_event_message(message: mqtt.MQTTMessage) -> None:
    """
    Handle the device event message received from the broker
    :param message: Message received from the broker
    """

    try:
        # Decode the message payload from an array of bytes to a string
        message_payload = str(message.payload.decode("utf-8"))

        # Create a DeviceDescriptor object from the JSON payload
        event_descriptor = EventDescriptor(**json.loads(message_payload))

        # Print the message received from the broker
        print(f"Received Event: Topic: {message.topic} Type: {event_descriptor.event_type} Value: {event_descriptor.event_value}")
    except Exception as e:
        # Print the error message
        print(f"Error processing message: {e}")

def handle_device_info_message(message: mqtt.MQTTMessage) -> None:
    """
    Handle the device info message received from the broker
    :param message: Message received from the broker
    """

    try:
        # Decode the message payload from an array of bytes to a string
        message_payload = str(message.payload.decode("utf-8"))

        # Create a DeviceDescriptor object from the JSON payload
        device_descriptor = DeviceDescriptor(**json.loads(message_payload))

        # Print the message received from the broker
        print(f"Received IoT Message (Retained:{message.retain}): Topic: {message.topic} DeviceId: {device_descriptor.device_id} Manufacturer: {device_descriptor.producer} SoftwareVersion: {device_descriptor.software_version}")
    except Exception as e:
        # Print the error message
        print(f"Error processing message: {e}")


def handle_device_telemetry_message(mqtt_client: mqtt.Client, message: mqtt.MQTTMessage) -> None:
    """
    Handle the device telemetry message received from the broker
    :param mqtt_client: MQTT Client used to publish the switch actions
    :param message: Message received from the broker
    """
    try:
        # Decode the message payload from an array of bytes to a string
        message_payload = str(message.payload.decode("utf-8"))

        # Create a MessageDescriptor object from the JSON payload
        message_descriptor = MessageDescriptor(**json.loads(message_payload))

        # Print the message received from the broker
        print(f"Received IoT Message: Topic: {message.topic} Timestamp: {message_descriptor.timestamp} Type: {message_descriptor.value_type} Value: {message_descriptor.value}")

        # Check if the telemetry value is above the temperature limit
        # The value can be a float (temperature) or a string (switch status), so we check its type before the comparison
        if (message_descriptor.value_type == "TEMPERATURE_SENSOR"
                and isinstance(message_descriptor.value, (int, float))
                and message_descriptor.value > TEMPERATURE_LIMIT):

            # Trigger a switch action to turn off the device
            trigger_switch_action(mqtt_client, "SWITCH", "OFF")

            # Schedule a switch action to turn on the device after 10 seconds
            schedule_device_action(mqtt_client, 10, "SWITCH", "ON")

    except Exception as e:
        # Print the error message
        print(f"Error processing message: {e}")


def trigger_switch_action(mqtt_client: mqtt.Client, switch_action: str, switch_value: str) -> None:
    """
    Publish a switch action to the broker for a target device
    :param mqtt_client: MQTT Client used to publish the action
    :param switch_action: Action to trigger
    :param switch_value: Value of the action
    :return:
    """
    try:
        # Create an ActionDescriptor object
        action_descriptor = ActionDescriptor(action_type=switch_action, action_value=switch_value)

        # Convert the ActionDescriptor object to a JSON string
        action_descriptor_json = json.dumps(action_descriptor.__dict__)

        # Publish the action to the broker
        mqtt_client.publish(device_action_topic, action_descriptor_json, qos=1, retain=False)

        print(f"Action Published: {action_descriptor_json}")
    except Exception as e:
        # Print the error message
        print(f"Error processing message: {e}")


def schedule_device_action(mqtt_client: mqtt.Client, delay_sec: float, switch_action: str, switch_value: str) -> None:
    """
    Schedule a device action to be triggered
    :param mqtt_client: MQTT Client used to publish the action
    :param delay_sec: Seconds to wait before triggering the action
    :param switch_action: Action to trigger
    :param switch_value: Value of the action
    :return:
    """
    print(f"Scheduling Action: {switch_action} Value: {switch_value} in {delay_sec} seconds")
    timer = threading.Timer(delay_sec, trigger_switch_action, args=[mqtt_client, switch_action, switch_value])
    timer.start()


def main() -> None:

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

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
