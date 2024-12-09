# Call2MQTT

**Call2MQTT** is a Python-based tool that listens for incoming calls (and optionally SMS messages, if enabled) from a GSM modem and publishes corresponding events to an MQTT broker. This solution is useful for integrating telephony events into IoT platforms, home automation systems, notification services, or any environment that leverages MQTT as a communication layer.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Environment Variables and Configuration](#environment-variables-and-configuration)
- [MQTT Topics](#mqtt-topics)
- [Logging](#logging)
- [Error Handling and Restarts](#error-handling-and-restarts)
- [Example Workflow](#example-workflow)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

Call2MQTT connects to a GSM modem, listens for incoming calls and (if you enable SMS support) incoming SMS messages, and then publishes these events to a specified MQTT broker. For each call or SMS received, a JSON message containing caller ID, timestamp, and related details is published to predefined MQTT topics.

This tool can be integrated into home automation systems (e.g., Home Assistant), monitoring dashboards, or custom notification workflows by subscribing to the MQTT topics where call and SMS events are published.

## Key Features

- **Incoming Call Detection:** Listens for incoming calls and publishes caller details to MQTT.
- **Incoming SMS Detection (Optional):** If uncommented and configured, can publish received SMS messages to MQTT.
- **Modem Integration:** Uses [python-gsmmodem](https://github.com/freedomobjects/python-gsmmodem) to interface with GSM modems over serial.
- **MQTT Integration:** Uses the [Paho MQTT client](https://pypi.org/project/paho-mqtt/) for publishing messages to MQTT brokers.
- **Automatic Modem Reconnect:** If the modem times out or encounters an issue, the script publishes a restart event and attempts to reinitialize the connection.
- **Configurable Logging:** Provides detailed logs to help with debugging.

## Architecture

1. **Modem Initialization:** The script connects to a GSM modem through a specified serial port and baud rate.
2. **Event Handlers:**
   - **Incoming Calls:** When a call is detected, the modem callback is triggered, the number is processed, and a JSON payload is published to the MQTT `INCOMING_CALL_TOPIC_NAME`.
   - **Incoming SMS (if enabled):** When an SMS is received, the callback parses the message and publishes its details to `INCOMING_SMS_TOPIC_NAME`.
3. **MQTT Publishing:** 
   - On start, a timestamp is published to `START_TOPIC_NAME`.
   - On error, an error message is published to `ERROR_TOPIC_NAME`.
   - On periodic timeouts or restarts, a count of restarts is published to `RESTART_TOPIC_NAME`.

## Prerequisites

- A working GSM modem (e.g., USB 3G/4G modem) compatible with `python-gsmmodem`.
- Python 3.6+ installed on the system.
- An MQTT broker accessible on your network.
- Basic knowledge of MQTT and access credentials for the broker.
- A properly configured `config.py` (see [Configuration](#configuration)).

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/call2mqtt.git
   cd call2mqtt
   ```

2. **Install Dependencies:**
   Make sure you have the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Required Python packages typically include:
   - `paho-mqtt`
   - `python-gsmmodem`
   - Other standard libraries (logging, json, re, etc. are included with Python).

3. **Hardware Setup:**
   - Ensure your GSM modem is connected to the system and the correct serial port (e.g. `/dev/ttyUSB0`) is known.
   - Insert a SIM card if necessary and ensure the PIN (if set) is available.

## Configuration

A `config.py` file is expected to provide key configuration variables. For example:

```python
# config.py example
MQTT_BROKER_HOST = "mqtt.example.com"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_LOGIN = "username"
MQTT_BROKER_PASSWORD = "password"
MQTT_CLIENT_ID = "call2mqtt_client"

MODEM_PORT = "/dev/ttyUSB0"
MODEM_BAUDRATE = 115200
MODEM_SIM_PIN = "1234"  # If needed, otherwise None
MODEM_RESTART_TIMEOUT_SEC = 60

INCOMING_CALL_TOPIC_NAME = "telephony/incoming_call"
INCOMING_SMS_TOPIC_NAME = "telephony/incoming_sms"
START_TOPIC_NAME = "telephony/service_start"
RESTART_TOPIC_NAME = "telephony/service_restart"
ERROR_TOPIC_NAME = "telephony/error"

DEBUG = False
```

Adjust these values according to your environment.

## Usage

1. **Run the Script:**
   ```bash
   ./call2mqtt.py
   ```
   
   or
   
   ```bash
   python3 call2mqtt.py
   ```

2. **Continuous Execution:**
   It's recommended to run this script as a service or under a supervisor (systemd, docker, pm2, etc.) to maintain continuous operation and handle restarts.

## Environment Variables and Configuration

- **Modem Configuration:**
  - `MODEM_PORT`: The serial port where the GSM modem is connected (e.g. `/dev/ttyUSB0`).
  - `MODEM_BAUDRATE`: The baud rate to communicate with the modem (e.g. `115200`).
  - `MODEM_SIM_PIN`: SIM card PIN if required, else `None`.

- **MQTT Configuration:**
  - `MQTT_BROKER_HOST`: Hostname or IP address of the MQTT broker.
  - `MQTT_BROKER_PORT`: Port the MQTT broker listens on (default is typically `1883`).
  - `MQTT_BROKER_LOGIN` & `MQTT_BROKER_PASSWORD`: Credentials for MQTT authentication.
  - `MQTT_CLIENT_ID`: A unique ID for the MQTT client instance.

- **Topics:**
  - `INCOMING_CALL_TOPIC_NAME`: Topic to publish incoming call events.
  - `INCOMING_SMS_TOPIC_NAME`: Topic to publish incoming SMS messages.
  - `START_TOPIC_NAME`: Topic to publish when the service starts.
  - `RESTART_TOPIC_NAME`: Topic to publish when the service restarts due to a timeout.
  - `ERROR_TOPIC_NAME`: Topic to publish error messages.

- **Other Parameters:**
  - `MODEM_RESTART_TIMEOUT_SEC`: Time (in seconds) after which the modem listener restarts if no activity is observed.
  - `DEBUG`: Set `True` for debug-level logging.

## MQTT Topics

- **`START_TOPIC_NAME`** (`telephony/service_start`):  
  Publishes the current timestamp when the service starts.
  
  **Example message:**
  ```json
  "2024-12-09 12:00:00"
  ```

- **`INCOMING_CALL_TOPIC_NAME`** (`telephony/incoming_call`):  
  Publishes details of an incoming call as JSON.
  
  **Example message:**
  ```json
  {
    "number_orig": "+1234567890",
    "type": 129,
    "phone_number": "+1234567890"
  }
  ```

- **`INCOMING_SMS_TOPIC_NAME`** (`telephony/incoming_sms`): *(If SMS callback is enabled)*  
  Publishes details of an incoming SMS message.
  
  **Example message:**
  ```json
  {
    "number": "+1234567890",
    "time": "2024-12-09 12:01:00",
    "text": "Hello from SMS!"
  }
  ```

- **`RESTART_TOPIC_NAME`** (`telephony/service_restart`):  
  Published each time the modem handling loop restarts due to a timeout or interruption.
  
  **Example message:**
  ```json
  1
  ```
  (An integer incrementing with each restart)

- **`ERROR_TOPIC_NAME`** (`telephony/error`):  
  Publishes error messages as strings to notify subscribers of issues.
  
  **Example message:**
  ```json
  "Exception('Modem not responding')"
  ```

## Logging

Logs are printed to stdout. The logging level can be controlled through the `DEBUG` flag in `config.py`. The timestamp, log level, and message are included.

Example Log Output:
```
2024-12-09 12:00:00    INFO: Init MQTT connection to 'mqtt.example.com:1883' as client 'call2mqtt_client'...
2024-12-09 12:00:00    INFO: Publish message '2024-12-09 12:00:00' to topic 'telephony/service_start', result=(0, 1), status=SUCCESS
2024-12-09 12:00:00    INFO: Init modem on port /dev/ttyUSB0, baudrate=115200...
2024-12-09 12:00:05    INFO: Waiting for incoming calls (60)...
2024-12-09 12:05:00    INFO: Incoming call from: number=+1234567890, type=129
```

## Error Handling and Restarts

- If the modem throws an exception or a timeout occurs, the script:
  - Logs a warning.
  - Publishes an error message to `ERROR_TOPIC_NAME`.
  - Attempts to close and reinitialize the modem connection.
  - Publishes a restart event to `RESTART_TOPIC_NAME`.

This ensures the tool is resilient and can recover from transient errors.

## Example Workflow

1. **Service Start:**  
   - Script starts and publishes the start timestamp to `telephony/service_start`.

2. **Incoming Call:**  
   - A call arrives on the modem.
   - The script captures the caller ID, logs it, and publishes a JSON message to `telephony/incoming_call`.

3. **No Activity / Timeout:**  
   - If no incoming call or SMS is detected within `MODEM_RESTART_TIMEOUT_SEC`, the script triggers a restart.
   - `telephony/service_restart` topic gets a numeric increment to indicate the restart count.

4. **Error Condition:**  
   - If the modem disconnects, fails to respond, or another exception occurs, the script logs the error and publishes it to `telephony/error`.
   - The script then attempts to reinitialize the modem and continue listening.

## Troubleshooting

- **No MQTT Messages:**  
  Check that the `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, and credentials are correct. Verify the MQTT broker is running and accessible.
  
- **No Modem Response:**  
  Ensure the correct `MODEM_PORT` is configured. Check that the modem is properly connected and not being used by another process.
  
- **PIN Error:**  
  If your SIM is PIN-locked, ensure `MODEM_SIM_PIN` is set in `config.py`.
  
- **Insufficient Permissions:**  
  On Linux, you may need to add your user to the `dialout` group or run with `sudo` to access the serial device.

## License

This project is provided under the [MIT License](LICENSE). See the [LICENSE](LICENSE) file for details.
```