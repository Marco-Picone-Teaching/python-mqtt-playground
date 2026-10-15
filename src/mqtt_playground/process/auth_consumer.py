# For this example we rely on the Paho MQTT Library for Python (2.x)
# Dependencies are managed with uv. From the project root run: uv run auth-consumer
# The target MQTT Broker (host and port) is configured in the config.yaml file

from mqtt_playground.config.config_manager import ConfigManager
import paho.mqtt.client as mqtt

# Configuration variables
client_id = "clientId0001-Consumer"
username = "<your_username>"
password = "<your_password>"
account_topic_prefix = "/iot/user/<your_username>/"


# The callback for when the client receives a CONNACK response from the server.
# With the Callback API VERSION2 the callback receives the reason_code and the (MQTT v5) properties
def on_connect(client, userdata, flags, reason_code, properties):
    # Print the connection result contained in the variable reason_code
    print("Connected with result code " + str(reason_code))

    # After the connection is established, we subscribe to the target topic composed by the account
    # topic prefix and the wildcard character #
    target_topic = account_topic_prefix + "#"

    # Subscribe to the target topic
    client.subscribe(target_topic)

    # Print the topic we are subscribed to
    print("Subscribed to: " + target_topic)


# Define a callback method to receive asynchronous messages
def on_message(client, userdata, message):
    # Print the message received from the broker
    # Available attributes: payload, topic, qos, retain
    print("\n##########################################################")
    print("message received: ", str(message.payload.decode("utf-8")))
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)
    print("##########################################################")


def main():

    # Load the shared configuration (e.g., MQTT Broker host and port) from the config.yaml file
    config_manager = ConfigManager()

    # Create a new MQTT Client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Attack Paho OnMessage Callback Method
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect

    # Set Account Username & Password
    mqtt_client.username_pw_set(username, password)

    # Connect to the target MQTT Broker
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
