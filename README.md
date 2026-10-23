# Python MQTT Playground

This Project contains a group of Python MQTT Paho examples focusing on the following aspects:

- Simple MQTT Producer and Consumer
- MQTT Producer and Consumer with Authentication
- Json MQTT Producer and Consumer
- IoT Device Demo Producer and Consumer

Reference MQTT Python Library Paho (2.x) - https://github.com/eclipse/paho.mqtt.python

## Table of Contents

- [Setup](#setup)
  - [Using pip (alternative)](#using-pip-alternative)
  - [MQTT Broker](#mqtt-broker)
- [Configuration](#configuration)
- [Paho MQTT 2.x](#paho-mqtt-2x)
- [Asynchronous Model of Paho](#asynchronous-model-of-paho)
  - [Network Loop Options](#network-loop-options)
  - [The Connection is Asynchronous](#the-connection-is-asynchronous)
  - [Connection Management Options](#connection-management-options)
  - [Why a Thread for the Logic Started by a Callback?](#why-a-thread-for-the-logic-started-by-a-callback)
- [Project Structure](#project-structure)
  - [Type Hints](#type-hints)
- [Running the Examples](#running-the-examples)
- [Playground Outline](#playground-outline)
  - [1. Simple Producer & Consumer](#1-simple-producer--consumer)
  - [2. JSON Producer & Consumer](#2-json-producer--consumer)
  - [3. Device Producer & Consumer](#3-device-producer--consumer)
  - [4. Authorized Producer & Consumer](#4-authorized-producer--consumer)
  - [5. MQTT IoT Smart Object](#5-mqtt-iot-smart-object)
    - [Threads & Timer Information](#threads--timer-information)
- [Code Example](#code-example)
- [MQTT Client Tools](#mqtt-client-tools)
  - [Connection Management](#connection-management)
  - [Receiving Messages on Topics](#receiving-messages-on-topics)
  - [Using an MQTT Client with the Playground](#using-an-mqtt-client-with-the-playground)

## Setup

The project is managed with [uv](https://docs.astral.sh/uv/). Dependencies are declared in `pyproject.toml`,
locked in `uv.lock`, and the Python version (3.12) is pinned in `.python-version`.

- Dependencies: `paho-mqtt` (2.x) and `pyyaml` (to read the configuration file)

Install uv (if needed) following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/), e.g.:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the project root, create the virtual environment (`.venv`) and install all the dependencies with:

```bash
uv sync
```

uv automatically downloads the required Python version if it is not available on your machine.
The command also installs the `mqtt_playground` package (in `src/`) in editable mode, together with a dedicated
command for each MQTT process (see [Running the Examples](#running-the-examples)).

In PyCharm, you can select the existing `.venv` interpreter or add a new "uv" interpreter from the interpreter settings.

### Using pip (alternative)

The `requirements.txt` file is **generated** from `uv.lock` and is kept only for pip-based workflows:

```bash
pip install -r requirements.txt
```

Do not edit it manually. After changing the dependencies, regenerate it with:

```bash
uv export --no-hashes --no-dev -o requirements.txt
```

### MQTT Broker

All the examples require a running MQTT Broker. The address of the broker is configured in `config.yaml`
(see [Configuration](#configuration)). There are two options:

**Option 1 - Local broker (recommended)**

Install [Eclipse Mosquitto](https://mosquitto.org/), an open source and lightweight MQTT Broker, on your machine.
It can be installed in different ways (installer for Windows, Homebrew on macOS, package managers on Linux, Docker, ...)
as described on the official [download page](https://mosquitto.org/download/).
Once started, the broker is reachable at `127.0.0.1` on port `1883`, which is the default configuration of the playground.

**Option 2 - Public test broker**

If you can not install a local broker, you can use one of the free public brokers available on the Internet
(plain MQTT on port `1883`, no authentication required):

| Broker                                              | Host                 | Port   |
|-----------------------------------------------------|----------------------|--------|
| [Eclipse Mosquitto](https://test.mosquitto.org/)    | `test.mosquitto.org` | `1883` |
| [HiveMQ](https://www.hivemq.com/mqtt/public-mqtt-broker/) | `broker.hivemq.com`  | `1883` |
| [EMQX](https://www.emqx.com/en/mqtt/public-mqtt5-broker)  | `broker.emqx.io`     | `1883` |

To use one of them, set its host in `config.yaml`, e.g.:

```yaml
broker:
  host: test.mosquitto.org
  port: 1883
```

Public brokers are shared with everybody on the Internet, so keep in mind that:

- **all the messages are public**: anyone can read the data you publish, so never send personal or sensitive information;
- **topics are shared**: other users may publish on the same topics (e.g., `sensor/temperature`), so you can receive
  unexpected messages. Use a unique prefix in the topics of the examples (e.g., `<your_name>/sensor/temperature`);
- **the client id must be unique**: if two clients connect with the same client id, the broker disconnects one of them.
  Change the `client_id` variable of the examples (e.g., `<your_name>-Producer`);
- **avoid subscribing to `#`**: on a public broker it means receiving the traffic of all the users;
- they are intended for testing only, with no guarantee of availability, and they do not support the
  [Authorized Producer & Consumer](#4-authorized-producer--consumer) example, that requires a broker configured with user accounts.

## Configuration

The parameters shared by all the scripts (the target MQTT Broker) are defined in the `config.yaml` file in the project root:

```yaml
broker:
  host: 127.0.0.1
  port: 1883
  keepalive: 60
```

The file is loaded by the `ConfigManager` class (`src/mqtt_playground/config/config_manager.py`), that each process
creates in its `main()` function and uses to connect to the broker:

```python
from mqtt_playground.config.config_manager import ConfigManager

def main():
    config_manager = ConfigManager()
    ...
    mqtt_client.connect(config_manager.broker_host, config_manager.broker_port, config_manager.broker_keepalive)
```

By default `ConfigManager` searches `config.yaml` in the current working directory and then in the project root.
A different file can be used by passing its path: `ConfigManager("path/to/other_config.yaml")`.
Generic values can be read with dotted keys, e.g., `config_manager.get("broker.host")`.

The parameters specific to a single example (e.g., client id, topics, credentials, number of messages)
are still defined as variables at the beginning of each process module.

## Paho MQTT 2.x

The playground uses the 2.x version of the Paho library. The main differences with respect to the previous 1.x version are:

- The Callback API version is a mandatory parameter when creating the client. We use `VERSION2`:

  ```python
  mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
  ```

- With `VERSION2`, the `on_connect` callback receives the `reason_code` (a `ReasonCode` object instead of the integer `rc`)
  and the MQTT v5 `properties`. The same signature is used for both MQTT v3.1.1 and v5:

  ```python
  def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
                 reason_code: ReasonCode, properties: Properties | None) -> None:
      if reason_code.is_failure:
          print(f"Connection failed: {reason_code}")
  ```

- Other callbacks change in the same way, e.g., `on_publish(client, userdata, mid, reason_code, properties)`.
  The `on_message(client, userdata, message)` callback is unchanged.
- The library is fully type annotated, so the types of the callback parameters can be imported and used in the code
  (see [Type Hints](#type-hints)).

More details are available in the official [migration guide](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html).

## Asynchronous Model of Paho

Paho is an **asynchronous** library: most of the methods of the client (`connect()`, `publish()`, `subscribe()`, ...)
do not wait for the response of the broker, but only prepare the MQTT packets and return immediately.
The real communication with the broker is performed by the **network loop**, that:

- writes on the socket the outgoing packets queued by `publish()`, `subscribe()`, ...;
- reads from the socket the incoming packets (CONNACK, PUBACK, incoming messages, ...);
- sends the keepalive `PINGREQ` packets to keep the connection alive;
- manages the automatic reconnection when the connection is lost;
- **executes the callbacks** (`on_connect`, `on_message`, `on_publish`, ...) when the related packet is received.

### Network Loop Options

The network loop has to be executed by the application in one of the following ways:

| Method                       | Blocking | Thread                          | Typical usage                                                         |
|------------------------------|----------|---------------------------------|-----------------------------------------------------------------------|
| `loop_forever()`             | Yes      | The calling thread (e.g., main) | The whole application is driven by the callbacks (e.g., consumers)    |
| `loop_start()` / `loop_stop()` | No     | A new background thread         | The main thread has its own logic and the loop runs "behind the scenes" |
| `loop(timeout)`              | Yes (up to `timeout`) | The calling thread     | The application integrates the loop in its own event loop             |

`loop_forever()` returns only when `disconnect()` is called, while with `loop_start()` the loop runs until `loop_stop()` is called.

### The Connection is Asynchronous

`connect()` opens the TCP socket and sends the MQTT `CONNECT` packet, but it does **not** wait for the `CONNACK` of the broker.
These operations are executed by the thread that calls `connect()` (e.g., the main thread), since the network loop
has not been started yet. On the contrary, `connect_async()` only stores the connection parameters:
the socket and the `CONNECT` packet are then managed by the network loop when it starts.
The result of the connection is known only when the network loop receives the `CONNACK` and calls `on_connect`.
The following diagram shows what happens in `simple_producer_issue.py`, where the main thread starts publishing
right after `connect()` / `loop_start()`:

```mermaid
sequenceDiagram
    participant M as Main Thread
    participant L as Network Loop Thread<br/>(started by loop_start)
    participant B as Broker

    M->>B: connect() opens the socket and sends CONNECT
    Note over M: executed by the Main Thread (the network thread<br/>does not exist yet). It returns immediately<br/>without waiting for the CONNACK
    M->>L: loop_start() creates the Network Loop Thread
    Note over M: loop_start() returns immediately
    M->>L: publish() only queues the message
    Note over M,L: ISSUE: the main thread publishes without knowing<br/>if and when the client is connected
    L->>B: PUBLISH
    B-->>L: CONNACK (reason_code)
    L->>L: on_connect(reason_code)
    alt connection refused (e.g., wrong credentials)
        B--xL: the broker closes the connection
        Note over M,B: the QoS 0 messages are silently lost<br/>while the main thread keeps printing "Message Sent"
    else connection accepted
        Note over M,B: it works, but only by chance (timing dependent)
    end
```

A producer that starts publishing right after `connect()` / `loop_start()` is therefore not sure to be connected:
the first messages can be sent before the `CONNACK`, and if the broker refuses
the connection (e.g., wrong credentials) the QoS 0 messages are silently lost, while the console still prints "Message Sent".
The same is true for a retained message, such as the device info of the Device Producer.
Note that `reason_code` must always be checked in `on_connect`: the callback is called also when the connection is refused.

### Connection Management Options

The playground shows two correct ways to start the application logic only after a successful connection:

**Option 1 - The main thread waits for the connection** (`simple_producer_event.py`).
The `on_connect` callback sets a `threading.Event`, while the main thread blocks on `event.wait(timeout)` before publishing:

```python
connected_event = threading.Event()

def on_connect(client, userdata, flags, reason_code, properties):
    if not reason_code.is_failure:
        connected_event.set()

mqtt_client.connect(host, port, keepalive)
mqtt_client.loop_start()
if not connected_event.wait(connection_timeout_s):
    print("Unable to connect ...")
    return
# ... publishing logic in the main thread
```

Two threads are involved: the **main thread**, that runs the publishing logic, and the **network loop thread**
started by `loop_start()`, that executes `on_connect`. The `Event` is the communication channel between them:

```mermaid
sequenceDiagram
    participant M as Main Thread
    participant L as Network Loop Thread<br/>(started by loop_start)
    participant B as Broker

    M->>B: connect() sends CONNECT
    M->>L: loop_start()
    M->>M: connected_event.wait(timeout)
    Note over M: suspended by the OS<br/>(no CPU usage)
    B-->>L: CONNACK (reason_code)
    L->>L: on_connect(reason_code)
    alt connection accepted
        L-->>M: connected_event.set() wakes up the main thread
        loop message_limit times
            M->>L: publish() queues the message
            L->>B: PUBLISH
            M->>M: time.sleep(1)
        end
        M->>L: disconnect() and loop_stop()
    else connection refused or timeout expired
        Note over M: wait() returns False after the timeout
        M->>L: loop_stop() and exit
    end
```

`Event.wait()` is **not** an active (busy) wait: the main thread is suspended by the OS without consuming CPU
until the event is set or the timeout expires. On the contrary, a loop like `while not client.is_connected(): time.sleep(0.1)`
is a polling solution that should be avoided.

**Option 2 - The connection starts the logic** (`simple_producer.py` and all the other producers).
The `on_connect` callback starts the publishing logic in a **dedicated thread**, while the main thread only runs `loop_forever()`:

```python
publisher_thread: threading.Thread | None = None

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        client.disconnect()   # stop loop_forever
        return
    start_publishing(client)

def start_publishing(client):
    global publisher_thread
    if publisher_thread is None or not publisher_thread.is_alive():
        publisher_thread = threading.Thread(target=publish_messages, args=(client,), daemon=True)
        publisher_thread.start()

def publish_messages(client):
    # ... publishing loop
    client.disconnect()       # stop loop_forever when done

mqtt_client.connect(host, port, keepalive)
mqtt_client.loop_forever()
```

In this case the network loop runs in the **main thread** (`loop_forever()`), so `on_connect` is executed by the main thread,
while the publishing logic runs in the **publisher thread** started by the callback.
The publisher thread communicates with the network loop through the client methods: `publish()` puts the message
in the outgoing queue and `disconnect()` stops `loop_forever()`:

```mermaid
sequenceDiagram
    participant M as Main Thread<br/>(Network Loop with loop_forever)
    participant P as Publisher Thread
    participant B as Broker

    M->>B: connect() sends CONNECT
    M->>M: loop_forever()
    B-->>M: CONNACK (reason_code)
    M->>M: on_connect(reason_code)
    alt connection refused
        M->>M: disconnect() stops loop_forever and the process exits
    else connection accepted
        M->>P: start_publishing() starts the Publisher Thread
        Note over M: on_connect returns immediately:<br/>the network loop is free to work
        loop message_limit times
            P->>M: publish() queues the message
            M->>B: PUBLISH (written by the network loop)
            P->>P: time.sleep(1)
        end
        Note over M,B: meanwhile the network loop also sends the<br/>PINGREQ packets and processes the incoming packets
        P->>M: disconnect() stops loop_forever and the process exits
    end
```

Since Paho reconnects automatically, `on_connect` can be called more than once. For this reason `start_publishing()`
checks if the publisher thread is still running before starting a new one:

```mermaid
sequenceDiagram
    participant M as Main Thread<br/>(Network Loop with loop_forever)
    participant P as Publisher Thread
    participant B as Broker

    Note over P: publishing messages ...
    B--xM: connection lost
    M->>B: automatic reconnection: CONNECT
    B-->>M: CONNACK (reason_code)
    M->>M: on_connect(reason_code)
    M->>M: start_publishing(): publisher_thread.is_alive() is True
    Note over M,P: no new thread is started:<br/>the existing Publisher Thread keeps publishing
```

| Option                         | Pros                                                         | Cons                                                                                    |
|--------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| 1. `Event` + `loop_start()`    | Sequential code, easy to read in `main()`                    | The connection is checked only at startup: reconnections are not visible to the main thread |
| 2. `on_connect` + thread       | Event-driven, consistent with consumers and Smart Object     | `on_connect` is called again at each reconnection: a second thread must not be started  |

### Why a Thread for the Logic Started by a Callback?

It could seem simpler to call the publishing loop directly inside `on_connect`. However, **the callbacks are executed by
the network loop itself** (the main thread with `loop_forever()`, or the background thread with `loop_start()`),
and while a callback is running the network loop is blocked. Moreover, `publish()` only puts the message in an
outgoing queue: the message is actually written on the socket by the network loop. Running a long loop
(e.g., 1000 messages with a `sleep(1)`) inside `on_connect` has the following effects:

- the queued messages are **not sent** until the callback returns;
- the keepalive `PINGREQ` packets are not sent, so the broker **closes the connection** after 1.5 x keepalive seconds;
- incoming messages, QoS 1/2 acknowledgments and the other callbacks are not processed.

```mermaid
sequenceDiagram
    participant M as Main Thread<br/>(Network Loop with loop_forever)
    participant B as Broker

    B-->>M: CONNACK (reason_code)
    M->>M: on_connect() runs the publishing loop (WRONG)
    Note over M: the network loop is BLOCKED<br/>until on_connect returns
    loop message_limit times
        M->>M: publish() only queues the message
        M->>M: time.sleep(1)
    end
    Note over M,B: no PUBLISH and no PINGREQ are written on the socket
    B--xM: after 1.5 x keepalive seconds the broker closes the connection
```

For this reason a callback must always **return quickly**:

- short operations (a single `publish()`, a `subscribe()`, updating a variable) can be executed directly in the callback.
  For example, the Device Producer publishes the retained device info inside `on_connect`, and the consumers
  subscribe inside `on_connect` so that the subscriptions are restored at each reconnection;
- long-running or blocking logic (periodic telemetry, `time.sleep()`, waiting for user input, ...) has to be executed
  in a **dedicated thread** started by the callback, as done by the producers and by the MQTT Smart Object (`device_behaviour` thread).

For the same reason, blocking methods such as `MQTTMessageInfo.wait_for_publish()` must never be called inside a callback:
they wait for the network loop, that is blocked by the callback itself.

## Project Structure

The project follows the `src` layout: all the code is in the `mqtt_playground` package in `src/`.

```
python-mqtt-playground/
├── pyproject.toml          # Project metadata, dependencies and entry points
├── uv.lock                 # Locked dependency versions (managed by uv)
├── requirements.txt        # Generated from uv.lock for pip users
├── config.yaml             # Shared configuration (MQTT Broker)
├── src/mqtt_playground/    # Application package
│   ├── config/             # ConfigManager (reads config.yaml)
│   ├── dto/                # Data Transfer Objects (JSON payloads)
│   ├── model/              # Emulated sensors and actuators
│   └── process/            # MQTT processes (producers, consumers, smart object), each with a main() function
└── images/
```

Each module in `process/` follows the same structure:

- the **configuration variables** of the example (client id, topics, ...) at the beginning of the module;
- the **Paho callbacks** (`on_connect`, `on_message`) and the helper functions, that receive the MQTT client
  as parameter (e.g., the `client` argument of the callbacks) instead of using a global variable;
- the **`main()`** function that loads the configuration, creates the MQTT client, connects to the broker and starts the loop.

Importing a module has no side effects: the process starts only when `main()` is called.

### Type Hints

The code uses Python **type hints** (Python >= 3.10 syntax, e.g., `float | str`, `Properties | None`) on DTOs, Models,
the `ConfigManager` and the functions of the processes. They make explicit the data exchanged by each function
(e.g., the fields of a `MessageDescriptor` or the MQTT client received by the helper functions) and allow
IDEs and static type checkers to detect errors before running the code.

The Paho callbacks use the types provided by the library:

| Parameter     | Type                 | Description                                                                 |
|---------------|----------------------|-----------------------------------------------------------------------------|
| `client`      | `mqtt.Client`        | The MQTT client that received the event                                     |
| `userdata`    | `Any`                | The user data set on the client (not used in the examples)                  |
| `flags`       | `mqtt.ConnectFlags`  | The CONNACK flags (e.g., `session_present`)                                 |
| `reason_code` | `ReasonCode`         | The result of the operation (`paho.mqtt.reasoncodes`)                       |
| `properties`  | `Properties \| None` | The MQTT v5 properties (`paho.mqtt.properties`), `None` with MQTT v3.1.1    |
| `message`     | `mqtt.MQTTMessage`   | The received message (`topic`, `payload`, `qos`, `retain`)                  |

```python
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from typing import Any

def on_connect(client: mqtt.Client, userdata: Any, flags: mqtt.ConnectFlags,
               reason_code: ReasonCode, properties: Properties | None) -> None:
    ...

def on_message(client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
    ...
```

Type hints are not checked at runtime by Python. To check the code with [mypy](https://mypy.readthedocs.io/) run:

```bash
uv run --with mypy mypy src/mqtt_playground --ignore-missing-imports
```

For example, the `value` of a `MessageDescriptor` is declared as `float | str` (a temperature or a switch status),
so mypy reports an error if it is compared with a number without checking its type first. For this reason the
Smart Object Controller checks the type with `isinstance(message_descriptor.value, (int, float))` before the comparison
with the temperature limit.

## Running the Examples

Each process is exposed as a command declared in the `[project.scripts]` section of `pyproject.toml`:

| Command                        | Module                                                 |
|--------------------------------|--------------------------------------------------------|
| `simple-producer`              | `mqtt_playground.process.simple_producer`              |
| `simple-producer-event`        | `mqtt_playground.process.simple_producer_event`        |
| `simple-producer-issue`        | `mqtt_playground.process.simple_producer_issue`        |
| `simple-consumer`              | `mqtt_playground.process.simple_consumer`              |
| `json-producer`                | `mqtt_playground.process.json_producer`                |
| `json-consumer`                | `mqtt_playground.process.json_consumer`                |
| `device-producer`              | `mqtt_playground.process.device_producer`              |
| `device-consumer`              | `mqtt_playground.process.device_consumer`              |
| `auth-producer`                | `mqtt_playground.process.auth_producer`                |
| `auth-consumer`                | `mqtt_playground.process.auth_consumer`                |
| `auth-admin-consumer`          | `mqtt_playground.process.auth_admin_consumer`          |
| `mqtt-smart-object`            | `mqtt_playground.process.mqtt_smart_object`            |
| `mqtt-smart-object-controller` | `mqtt_playground.process.mqtt_smart_object_controller` |

With the MQTT Broker running, from the project root, start each process with `uv run`
(usually the consumer first and then the producer in another terminal), e.g.:

```bash
uv run simple-consumer
uv run simple-producer
```

Alternatively, you can run a process as a module or execute the file directly:

```bash
uv run python -m mqtt_playground.process.simple_consumer
uv run src/mqtt_playground/process/simple_consumer.py
```

---

## Playground Outline

- [Simple Producer & Consumer](#1-simple-producer--consumer)
- [JSON Producer & Consumer](#2-json-producer--consumer)
- [Device Producer & Consumer](#3-device-producer--consumer)
- [Authorized Producer & Consumer](#4-authorized-producer--consumer)
- [MQTT IoT Smart Object](#5-mqtt-iot-smart-object)

### 1. Simple Producer & Consumer

![](images/simple_producer_consumer.png)
 
In this exercise, we configure an MQTT Producer to simulate data generated by a temperature sensor and 
a Consumer to receive and process that data in real time.

The Producer will establish a connection to an MQTT Broker, which serves as the central hub for message exchange.
Once connected, the Producer publishes a series of n messages (e.g., 1000) containing only numeric temperature values. 
These messages are sent to the sensor/temperature topic.
For this setup, messages will be published with Quality of Service (QoS) level set to 0, 
meaning no delivery guarantee beyond a best-effort attempt. Additionally, the Retained flag is set to false, indicating that the Broker should not store these messages once sent.

The Consumer, acting as a receiver, also connects to the MQTT Broker.
It subscribes to the # topic, a wildcard subscription that enables it to receive all published messages across topics.
As messages are received, the Consumer reads the numeric temperature values and displays them, allowing to observe the real-time data flow.

- **Python Files**:
  - `src/mqtt_playground/process/simple_producer.py` (`uv run simple-producer`)
  - `src/mqtt_playground/process/simple_consumer.py` (`uv run simple-consumer`)
  - `src/mqtt_playground/process/simple_producer_event.py` (`uv run simple-producer-event`): alternative version of the producer
    where the main thread waits for the `on_connect` callback with a `threading.Event`
  - `src/mqtt_playground/process/simple_producer_issue.py` (`uv run simple-producer-issue`): intentionally wrong version of the producer
    that starts publishing without waiting for the `on_connect` callback (see the comments in the file and the
    [Asynchronous Model of Paho](#asynchronous-model-of-paho) section)

- **Producer**:
  - Connect to the MQTT Broker and start publishing only after a successful connection (`on_connect`).
  - Publish `n` messages (e.g., 1000) with simple numeric values to `sensor/temperature` topic.
  - Message properties: `QoS = 0`, `Retained = false`.

- **Consumer**:
  - Connect to the MQTT Broker.
  - Subscribe to `#` topic to receive all messages.
  - Read and display the received numeric values.

### 2. JSON Producer & Consumer

![](images/json_producer_consumer.png)

In the second exercise, we build on the basics of MQTT by creating a producer and consumer 
that handle structured data in JSON format. This exercise introduces the concept of message serialization and deserialization using JSON, 
as a common format for IoT data exchange.

The Producer establishes a connection to the MQTT Broker, similar to the first exercise.
Once connected, the Producer publishes a series of n messages to the sensor/temperature topic. 
This time, instead of sending simple numeric values, the Producer uses the `MessageDescriptor` class to create structured messages in JSON format. 
Each JSON message contains more organized data associated with the temperature sensor.
The messages are published with a Quality of Service (QoS) level of 0, meaning no guaranteed delivery, and the Retained flag is set to false, instructing the Broker not to retain the messages.

The Consumer also connects to the MQTT Broker and subscribes to the # topic to capture all messages.
Upon receiving each message, the Consumer deserializes the JSON payload back into the MessageDescriptor class format, 
allowing it to process and interpret the structured data effectively.

- **Python Files**:
  - `src/mqtt_playground/process/json_producer.py` (`uv run json-producer`)
  - `src/mqtt_playground/process/json_consumer.py` (`uv run json-consumer`)
  - `src/mqtt_playground/dto/message_descriptor.py`

- **Producer**:
  - Connect to the MQTT Broker.
  - Publish `n` messages to `sensor/temperature` topic using structured JSON messages with `MessageDescriptor` class.
  - Message properties: `QoS = 0`, `Retained = false`.

- **Consumer**:
  - Connect to the MQTT Broker.
  - Subscribe to `#` topic to receive JSON messages.
  - Deserialize JSON messages using `MessageDescriptor` class.

### 3. Device Producer & Consumer

![](images/device_producer_consumer.png)

In this exercise, we implement an MQTT-based system that not only transmits sensor data but also shares device-specific information. 
This exercise introduces device registration and data streaming using multiple MQTT topics.

The Producer connects to the MQTT Broker.
It first publishes device information, such as device ID and other metadata, in JSON format using the `DeviceDescriptor` class. 
This information is published to a specific topic in the format `device/<id>/info`, where `<id>` represents the unique identifier of the device. 
The Retained flag is set to true for this message, meaning that the Broker will store this device information for any new subscribers 
who connect after the initial publication.
In addition to device info, the Producer also publishes sensor data (e.g., temperature readings) as JSON messages to the `device/<id>/sensor/temperature` topic.
These sensor messages are set with a Quality of Service (QoS) level of 0 (best effort) and with the Retained flag set to false.

The `Consumer` connects to the MQTT Broker and subscribes to two topics:

- `device/+/info` to receive the descriptors of all registered devices (with + acting as a wildcard for the device ID).
- `device/+/sensor/#` to receive all sensor data for each registered device (using + for device ID and # to match any sensor-related topics).

As messages are received, the Consumer deserializes them into appropriate classes: DeviceDescriptor for device information and MessageDescriptor 
for sensor data, enabling it to interpret and process the different data types.

- **Python Files**:
  - `src/mqtt_playground/process/device_producer.py` (`uv run device-producer`)
  - `src/mqtt_playground/process/device_consumer.py` (`uv run device-consumer`)
  - `src/mqtt_playground/dto/device_descriptor.py`
  - `src/mqtt_playground/dto/message_descriptor.py`

- **Producer**:
  - Connect to the MQTT Broker.
  - Publish device information in JSON format with `DeviceDescriptor` class to `device/<id>/info` topic, setting `Retained = true`.
  - Publish sensor data as JSON to `device/<id>/sensor/temperature` topic.
  - Sensor message properties: `QoS = 0`, `Retained = false`.

- **Consumer**:
  - Connect to the MQTT Broker.
  - Subscribe to `device/+/info` to receive device descriptors and `device/+/sensor/#` for sensor data.
  - Deserialize messages into `DeviceDescriptor` and `MessageDescriptor` classes as appropriate.

### 4. Authorized Producer & Consumer

![](images/auth_producer_consumer.png)

In this example, we implement an MQTT system with user authentication, 
securing access to specific data topics. 
This exercise highlights the use of authentication credentials in MQTT, enabling message privacy and user-based data handling.

The Producer connects to the MQTT Broker, providing a username and password for authentication. 
This setup restricts access to the MQTT Broker, ensuring that only authenticated clients can publish or subscribe to topics.
After successfully connecting, the Producer publishes n messages (e.g., 1000) containing temperature values to a user-specific topic, 
`/iot/user/<username>/sensor/temperature`. Here, `<username>` represents the authenticated user's identifier, helping to separate data streams by user.
Each message is published with a Quality of Service (QoS) level of 0 (best effort) and with the Retained flag set to false.

The Consumer connects to the MQTT Broker using the same username and password as the Producer, ensuring it can access only the 
topics associated with this authenticated user.
Once authenticated, the Consumer subscribes to the topic `/iot/user/<username>/#`, which allows it to receive all messages published under this user’s namespace, 
including the temperature data from sensor/temperature. As messages arrive, the Consumer reads and displays the received values, allowing to observe data flow within the confines of a secured, user-specific topic structure.

- **Python Files**:
  - `src/mqtt_playground/process/auth_producer.py` (`uv run auth-producer`)
  - `src/mqtt_playground/process/auth_consumer.py` (`uv run auth-consumer`)
  - `src/mqtt_playground/process/auth_admin_consumer.py` (`uv run auth-admin-consumer`)

- **Configuration**: set the address of the broker with authentication enabled in `config.yaml` (`broker.host` and `broker.port`)
  and the account credentials (`username`, `password`, `account_topic_prefix`) in the variables at the beginning of each script.

- **Producer**:
  - Connect to the MQTT Broker using username and password.
  - Publish `n` messages to `/iot/user/<username>/sensor/temperature` topic.
  - Message properties: `QoS = 0`, `Retained = false`.
  
- **Consumer**:
  - Connect to the MQTT Broker with the same credentials as the producer.
  - Subscribe to `/iot/user/<username>/#` topic.
  - Read and display received messages.

### 5. MQTT IoT Smart Object

![](images/mqtt_smart_object_v3.png)

In this subsection outlines the core characteristics of a traditional MQTT-enabled IoT device designed for telemetry and event-based data generation
together with the management of incoming actions. 

**MQTT Smart Object Design**:
- Usually an MQTT Smart Object manages a list of resources, such as various types of sensors (e.g., light, temperature, humidity). Each sensor represents a distinct resource that periodically generates data.
- Telemetry: The Smart Object publishes telemetry data from each sensor at regular intervals, updating subscribers with current readings. Telemetry messages are generally non-retained, as they are time-sensitive data snapshots.
- Event: In addition to telemetry, the Smart Object can generate and publish event messages associated with its operational status. These events, such as alerts or notifications, are retained by the Broker to ensure new consumers can access the latest event data even if they connect after the initial event is published.
- Actions: The Smart Object can also subscribe to specific topics to receive commands or actions from external sources. These incoming messages allow the device to perform tasks or respond to adjustments, enabling bidirectional communication and control within the MQTT ecosystem.

This example encapsulates the typical roles of an MQTT IoT device in the Smart Object file `mqtt_smart_object.py`, from telemetry and event generation to optional actuation capabilities, 
showing how MQTT Smart Objects enable comprehensive and interactive IoT applications.
To emulate an external controller for the device the file `mqtt_smart_object_controller.py` is provided, which can send commands to the Smart Object and receive its telemetry and event data.

- **Python Files**:
  - `src/mqtt_playground/process/`:
    - `mqtt_smart_object.py`: MQTT Smart Object implementation (`uv run mqtt-smart-object`).
    - `mqtt_smart_object_controller.py`: Smart Object Controller for sending commands and receiving data (`uv run mqtt-smart-object-controller`).
  - `src/mqtt_playground/dto/`:
    - `device_descriptor.py`: Device Descriptor class for device information.
    - `message_descriptor.py`: Message Descriptor class for telemetry and event data.
    - `event_descriptor.py`: Event Descriptor class for event data.
    - `action_descriptor.py`: Action Descriptor class for incoming actions.

- **MQTT Smart Object**:
  - Connect to the MQTT Broker.
  - Publish device information `/device/<device_id>/info` topic, setting `Retained = true`.
  - Publish telemetry data from available sensors on the topic `/device/<device_id>/telemetry/<sensor_id>`
    - Telemetry messages include also both sensors and variations on the actuator status (e.g., switch ON/OFF).
  - Publish event messages based on device status on the topic `/device/<device_id>/event`
  - Subscribe to action topics to receive incoming commands on topic `/device/<device_id>/action/<action_id>`

- **MQTT Smart Object Controller**:
  - Connect to the MQTT Broker
  - Subscribe to device `info`, `telemetry`, and `event` topics of the Smart Object
  - When the received value (e.g., temperature) is above a certain threshold, send an action command to the Smart Object to switch `OFF` the actuator
  - Start a Timer to send a command to the Smart Object to switch `ON` the actuator after a certain time interval

#### Threads & Timer Information

In this example we use the `threading` library to manage the MQTT Smart Object and Controller in separate threads 
and timer to execute functions at specific intervals. The `threading` library provides a way to run multiple functions concurrently,

In Python, threading allows for the execution of multiple operations concurrently within a program. This can be particularly useful for performing background tasks without interrupting the main program flow. The `Timer` class, part of the threading module, enables scheduling functions to run after a specified interval, making it ideal for delayed or periodic tasks.

Threading is a way to achieve concurrent execution in Python. Each thread runs independently and can perform tasks such as I/O operations, computations, or interacting with the user.

##### Key Concepts

- **Thread**: The smallest unit of a process that can be scheduled and executed.
- **Main Thread**: The default thread where the Python program starts.
- **Subthread**: Additional threads created to perform concurrent tasks.

Here's a simple example to illustrate how threading works in Python:

```python
import threading
import time

def print_numbers():
    for i in range(10):
        print(i)
        time.sleep(1)

# Create a thread
thread = threading.Thread(target=print_numbers)

# Start the thread
thread.start()

# Continue with the main program
print("Thread started!")
```

Explanation:

- Import threading: Import the threading module to work with threads.
- Define Function: Create a function (`print_numbers`) that prints numbers from 0 to 9 with a delay of 1 second.
- Create a Thread: Initialize a thread that targets the `print_numbers` function.
- Start the Thread: Use `thread.start()` to begin execution of the thread.
- Main Program: The main program continues to execute without waiting for the thread to finish.

##### Timer Class

A Timer is a subclass of Thread that allows you to schedule a function to run after a specified interval. 
This is useful for tasks that need to be executed after a delay or at regular intervals.

Here's an example of how to use the Timer class:

```python
import threading

def greet():
    print("Hello, world!")

# Create a timer
timer = threading.Timer(5, greet)

# Start the timer
timer.start()

print("Timer started!")
```

In this example, we'll create a `Timer` that passes parameters to the target function when it executes.

## Code Example

```python
import threading

def greet(name, message):
    print(f"Hello, {name}! {message}")

# Parameters to be passed to the target function
name = "Alice"
message = "Welcome to the Python threading tutorial."

# Create a Timer
timer = threading.Timer(5, greet, args=(name, message))

# Start the Timer
timer.start()

print("Timer started! The greet function will run after 5 seconds with the given parameters.")
```
---

## MQTT Client Tools

During the development and the debugging of an MQTT application it is very useful to have a **graphical MQTT client**:
a desktop application that acts as a generic MQTT client and allows to interact with a broker without writing any code.
With an MQTT client tool you can:

- **manage the connections** to one or more brokers (host, port, client id, credentials, TLS, MQTT version, keep alive, ...);
- **subscribe to topics**, also using the wildcards `+` and `#`, and observe in real time the messages published by the producers;
- **inspect the messages**: payload (plain text or JSON), QoS, Retained flag and the history of the values of each topic;
- **publish messages manually** on any topic, choosing payload, QoS and Retained flag, e.g., to test a consumer
  or to send a command to a device without a dedicated producer.

Two popular, free and cross-platform (Windows, macOS, Linux) MQTT clients are:

- [MQTT Explorer](https://mqtt-explorer.com/): it shows all the topics of the broker as a **hierarchical tree**,
  making it easy to understand the topic structure of an application. It keeps the history of the messages of each topic,
  highlights the differences between consecutive JSON payloads and can plot numeric values on charts.
- [MQTTX](https://mqttx.app/): developed by EMQ, it has a **chat-like interface** in which the subscriptions are listed
  on the left and the received and published messages are shown as conversation bubbles.
  It supports MQTT 3.1, 3.1.1 and 5.0 and is also available as a command line tool (MQTTX CLI) and as a web application.

### Connection Management

The first step is to create a connection to the broker, using the same parameters of `config.yaml`
(e.g., protocol `mqtt://`, host `127.0.0.1` or a [public broker](#mqtt-broker), port `1883`).
Username and password are required only for brokers with authentication
(e.g., the [Authorized Producer & Consumer](#4-authorized-producer--consumer) example).
Both tools allow to save multiple connections, so you can easily switch between a local broker and a public one.

MQTT Explorer - Connection configuration:

![](images/mqtt_explorer.png)

MQTTX - Connection configuration (with the advanced parameters such as MQTT version, Keep Alive and Clean Start):

![](images/mqttx_1.png)

> **Note:** the Client ID must be unique on the broker. MQTTX generates a random Client ID for each connection,
> so it does not conflict with the clients of the playground (e.g., `clientId0001-Consumer`).
> If you set it manually, choose a different value, otherwise the broker disconnects one of the two clients.

### Receiving Messages on Topics

Once connected, the client can subscribe to the topics of interest and show the received messages.

In **MQTT Explorer**, the subscription to all the topics (`#`) is automatic: the topic tree on the left is built
as soon as new messages arrive, and selecting a topic shows on the right its last value, QoS, history and
a panel to publish new messages:

![](images/mqtt_explorer_2.png)

In **MQTTX**, the subscriptions are created explicitly with the **New Subscription** button (specifying topic filter
and QoS). Each subscription has a different color, used also for the received messages. The bottom panel allows
to publish a message choosing payload format, QoS, Retained flag and topic:

![](images/mqttx_2.png)

### Using an MQTT Client with the Playground

Some examples of how an MQTT client tool can be used together with the examples of the playground:

- **Observe the producers**: run `uv run device-producer` and subscribe to `device/#` to see both the
  (retained) device info on `device/<id>/info` and the telemetry on `device/<id>/sensor/temperature`.
- **Test the consumers**: run `uv run json-consumer` and publish manually on the topic `device/temperature`
  a JSON payload such as:

  ```json
  {"timestamp": 1700000000, "value_type": "TEMPERATURE_SENSOR", "value": 25.5}
  ```

- **Act as the Smart Object Controller**: run `uv run mqtt-smart-object` and publish on the topic
  `device/device001/action/switch` the following payload to switch `OFF` (or `ON`) the actuator,
  then observe the switch telemetry on `device/device001/telemetry/switch`:

  ```json
  {"action_type": "SWITCH", "action_value": "OFF"}
  ```

- **Understand the Retained flag**: connect the client after the producer has published the device info and
  check that the last retained message is immediately delivered on subscription, while telemetry messages are not.
