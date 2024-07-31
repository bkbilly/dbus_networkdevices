# DBus Network Devices

[![PyPI](https://img.shields.io/pypi/v/dbus-networkdevices.svg)](https://pypi.python.org/pypi/dbus-networkdevices)
![Python versions](https://img.shields.io/pypi/pyversions/dbus-networkdevices.svg)
![License](https://img.shields.io/pypi/l/dbus-networkdevices.svg)

The `dbus-networkdevices` library empowers Python applications to get the active network devices that are connected to your network.

## Key Features

* **IP Access:** Retrieve interface name, ip addresses, wifi ssid, etc...
* **Real-time Updates:** Utilizes callback functions to provide instant updates of network changes.

## Requirements

* Python 3.7 or later
* `dasdbus` library

## Installation

Install the library using pip:

```bash
pip install dbus-networkdevices
```

## Usage

This library offers two primary usage approaches:

### Command-Line Interaction

If you prefer a quick way to view information or control playback, you can potentially execute the dbus-networkdevices script directly. For more extensive programmatic control, I would recommend using the library within your Python code.

### Programmatic Control

Import the DBUSNetworkDevices class from your Python code:

```python
import json
from dbus_networkdevices import DBUSNetworkDevices

def callback(devices):
    # Handle the list of network devices here
    print(json.dumps(devices, indent=2))

# Create an instance of the class
DBUSNetworkDevices(callback)

# Keep the app running
while True:
    time.sleep(1)
```

## Inspiration

Most python applications use `iwgetid` and information from `/proc/net/wireless` to get the WiFi status, so I created this library to get the information directly from DBus and also include other interfaces.
