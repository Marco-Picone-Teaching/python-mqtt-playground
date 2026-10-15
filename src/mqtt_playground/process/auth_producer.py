# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run auth-producer
# The target MQTT Broker (host and port) is configured in the config.yaml file

from mqtt_playground.config.config_manager import ConfigManager
from mqtt_playground.model.temperature_sensor import TemperatureSensor
import paho.mqtt.client as mqtt
import time

# Configuration variables
client_id = "clientId0001-Producer"
default_topic = "sensor/temperature"
message_limit = 1000
username = "<your_username>"
password = "<your_password>"
account_topic_prefix = "/iot/user/<your_username>/"


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code " + str(reason_code))

#def on_publish(client, userdata, mid, reason_code, properties):
    #print("mid: " + str(mid))
    #pass


def main():

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
    mqtt_client.on_connect = on_connect

    # Set Account Username & Password
    mqtt_client.username_pw_set(username, password)

    # Connect to the target MQTT Broker
    print("Connecting to " + config_manager.broker_host + " port: " + str(config_manager.broker_port))
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Start the MQTT Client with the loop_start method to process the callbacks in a separate thread
    mqtt_client.loop_start()

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

        # Publish the message to the target topic composed by the account topic prefix and the default topic
        target_topic = account_topic_prefix + default_topic

        # Publish the message to the topic
        mqtt_client.publish(target_topic, payload_string)

        # Print the message sent and sleep for 1 second
        print(f"Message Sent: {message_id} Topic: {target_topic} Payload: {payload_string}")
        time.sleep(1)

    mqtt_client.loop_stop()


if __name__ == "__main__":
    main()
