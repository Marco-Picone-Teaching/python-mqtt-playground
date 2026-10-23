# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run simple-producer-event
#
# Connection management - Option 1: "the main thread waits for the connection" (threading.Event)
#
# connect() and loop_start() are NON-BLOCKING: connect() opens the TCP socket and sends the MQTT CONNECT packet,
# while the broker response (CONNACK) is received later by the Paho network thread started with loop_start(),
# that then calls the on_connect callback. For this reason the main thread can not start publishing right after
# connect() (see simple_producer_issue.py), but it has to wait for the result of the on_connect callback.
#
# In this version the synchronization between the two threads is done with a threading.Event:
# - the on_connect callback (executed in the Paho network thread) sets the event when the connection is accepted;
# - the main thread blocks on connected_event.wait(timeout) and starts the publishing logic only when the event is set.
# Note: Event.wait() is NOT an active (busy) wait. The main thread is suspended by the OS without consuming CPU
# until the event is set or the timeout expires.
#
# Pros: the logic stays sequential and easy to read in the main() function.
# Cons: the connection is managed only once at startup. If the connection is lost and Paho reconnects
# automatically, the main thread is not aware of it and keeps publishing (QoS 0 messages are lost meanwhile).
#
# See simple_producer.py for Option 2: the publishing logic is started by the on_connect callback in a dedicated thread.

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any
import threading
import time

# Configuration variables
client_id = "clientId0001-Producer"
default_topic = "sensor/temperature"
message_limit = 1000
connection_timeout_s = 10

# Event used to notify the main thread that the connection has been accepted by the broker.
# The on_connect callback is executed by the Paho network thread (started with loop_start), so we need
# a thread-safe synchronization mechanism to wait for it before starting the publishing logic
connected_event = threading.Event()


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
               reason_code: ReasonCode, properties: Properties | None) -> None:
    # Check if the broker has refused the connection (e.g., wrong credentials or not authorized client id)
    if reason_code.is_failure:
        print("Connection refused with result code " + str(reason_code))
    else:
        print("Connected with result code " + str(reason_code))
        # Notify the main thread that the client is connected and can start publishing
        connected_event.set()

#def on_publish(client: mqtt.Client, userdata: Any, mid: int, reason_code: ReasonCode, properties: Properties) -> None:
    #print("mid: " + str(mid))
    #pass


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

    # Attach Paho OnPublish Callback Method
    #mqtt_client.on_publish = on_publish

    # Connect to the target MQTT Broker
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Start the MQTT Client with the loop_start method to process the callbacks in a separate thread
    mqtt_client.loop_start()

    # Wait for the on_connect callback before starting the publishing logic.
    # connect() and loop_start() are non-blocking: without this wait the messages could be published
    # before the CONNACK has been received or even if the connection has been refused by the broker
    if not connected_event.wait(connection_timeout_s):
        print(f"Unable to connect to the MQTT Broker within {connection_timeout_s} seconds. Exiting ...")
        mqtt_client.loop_stop()
        return

    # Create Demo Temperature Sensor
    temperature_sensor = TemperatureSensor()

    # MQTT Paho Publish method with all the available parameters
    # mqtt_client.publish(topic, payload=None, qos=0, retain=False)

    # Publish messages with the temperature value
    for message_id in range(message_limit):

        # Measure the temperature
        temperature_sensor.measure_temperature()

        # Create the payload string with the temperature value
        payload_string = temperature_sensor.temperature_value

        # Publish the message to the default topic
        mqtt_client.publish(default_topic, payload_string)

        # Publish the message to the default topic and get the result in the infot variable
        #infot = mqtt_client.publish(default_topic, payload_string)
        #infot.wait_for_publish()

        # Print the message sent
        print(f"Message Sent: {message_id} Topic: {default_topic} Payload: {payload_string}")

        # Wait for 1 second before sending the next message
        time.sleep(1)

    # Disconnect from the broker and stop the MQTT Client network thread started with loop_start
    mqtt_client.disconnect()
    mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
