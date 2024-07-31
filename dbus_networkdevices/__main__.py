import json
import argparse
from . import DBUSNetworkDevices


def main():
    parser = argparse.ArgumentParser(
        prog="dbus-networkdevices",
        description="Gets a list of Network Devices from DBus")
    args = parser.parse_args()

    network_devices = DBUSNetworkDevices().get_network_devices() 
    print(json.dumps(network_devices, indent=2))
