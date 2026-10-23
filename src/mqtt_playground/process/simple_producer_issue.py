# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run simple-producer-issue
#
# ATTENTION: this is an intentionally WRONG version of the simple_producer.py example!
# It is kept to show a common issue: the producer starts publishing WITHOUT waiting for the result of the
# connection (the on_connect callback). See the "ISSUE" comments below and compare it with the two correct versions:
# - simple_producer_event.py: the main thread waits for the on_connect callback (threading.Event) before publishing;
# - simple_producer.py: the on_connect callback starts the publishing logic in a dedicated thread.
# The "Asynchronous Model of Paho" section of the README explains the problem and the different options.

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any
import time

# Configuration variables
client_id = "clientId0001-Producer"
default_topic = "sensor/temperature"
message_limit = 1000


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
# ISSUE: the callback only prints the reason_code. It does not check if the connection has been refused by the
# broker (e.g., wrong credentials, not authorized client id) and it does not notify the main thread in any way.
# For this reason the main thread has no idea if and when the client is actually connected.
def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
               reason_code: ReasonCode, properties: Properties | None) -> None:
    print("Connected with result code " + str(reason_code))

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

    # Attach Paho OnMessage Callback Method
    mqtt_client.on_connect = on_connect

    # Attach Paho OnPublish Callback Method
    #mqtt_client.on_publish = on_publish

    # Connect to the target MQTT Broker
    # ISSUE: connect() only opens the TCP socket and sends the MQTT CONNECT packet. It returns immediately,
    # WITHOUT waiting for the broker response (CONNACK). The CONNACK is received later by the network thread,
    # that will then call the on_connect callback.
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Start the MQTT Client with the loop_start method to process the callbacks in a separate thread
    # ISSUE: loop_start() is also non-blocking. It starts the network thread and returns immediately,
    # so the code below runs in parallel with the connection handshake.
    mqtt_client.loop_start()

    # Create Demo Temperature Sensor
    temperature_sensor = TemperatureSensor()

    # MQTT Paho Publish method with all the available parameters
    # mqtt_client.publish(topic, payload=None, qos=0, retain=False)

    # ISSUE: the publishing logic starts right away, without being sure that the client is connected:
    # - the first messages can be sent before the CONNACK has been received;
    # - if the broker refuses the connection (e.g., bad credentials) the broker closes the connection and all the
    #   messages are silently lost, while the loop keeps "publishing" and printing "Message Sent";
    # - with QoS 0 Paho does not keep the messages to re-send them after a (re)connection, so they are simply dropped;
    # - the value returned by publish() (MQTTMessageInfo with the rc field) is ignored, so errors such as
    #   MQTT_ERR_NO_CONN are never detected.
    # The behaviour is therefore non-deterministic: it may look like it works with a local broker,
    # but it can easily lose messages with a remote/slow broker or with a refused connection.

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
        # ISSUE: "Message Sent" is printed even if the client is not (yet) connected and the message is lost
        print(f"Message Sent: {message_id} Topic: {default_topic} Payload: {payload_string}")

        # Wait for 1 second before sending the next message
        time.sleep(1)

    # Stop the MQTT Client with the loop_stop method in order to stop the separate thread
    mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
