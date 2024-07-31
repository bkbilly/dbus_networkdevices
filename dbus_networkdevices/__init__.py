import threading
from dasbus.loop import EventLoop
from dasbus.client.handler import GLibClient
from dasbus.connection import SystemMessageBus


class DBUSNetworkDevices():
    """docstring for DBUSNetworkDevices"""

    def __init__(self, callback=None):
        self.callback = callback
        self.bus = SystemMessageBus()

        if self.callback is not None:
            self.prev_send = None
            GLibClient.subscribe_signal(
                self.bus.connection,
                service_name=None,
                object_path="/org/freedesktop",
                interface_name="org.freedesktop.DBus.ObjectManager",
                signal_name="InterfacesAdded",
                callback=self.dbus_callback,
            )
            GLibClient.subscribe_signal(
                self.bus.connection,
                service_name=None,
                object_path="/org/freedesktop",
                interface_name="org.freedesktop.DBus.ObjectManager",
                signal_name="InterfacesRemoved",
                callback=self.dbus_callback,
            )
            GLibClient.subscribe_signal(
                self.bus.connection,
                service_name=None,
                object_path="/org/freedesktop/resolve1",
                interface_name="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                callback=self.dbus_callback,
            )
            self.dbus_callback(None)
            loop = EventLoop()
            threading.Thread(target=loop.run, daemon=True).start()

    def dbus_callback(self, iface):
        self.network_devices = self.get_network_devices()
        if self.prev_send != self.network_devices:
            self.prev_send = self.network_devices
            self.callback(self.network_devices)

    def get_network_devices(self):
        proxy = self.bus.get_proxy(
            service_name="org.freedesktop.NetworkManager",
            object_path="/org/freedesktop/NetworkManager",
            interface_name="org.freedesktop.DBus.Properties",
        )
        active_connections = proxy.Get("org.freedesktop.NetworkManager", "ActiveConnections")
        networkdevices = []
        for connection in active_connections:
            net_proxy = self.bus.get_proxy(
                service_name="org.freedesktop.NetworkManager",
                object_path=connection,
                interface_name="org.freedesktop.NetworkManager.Connection.Active",
            )
            networkdevice = {
                "name": net_proxy.Id,
                "type": net_proxy.Type,
            }
            if "AccessPoint" in net_proxy.SpecificObject:
                wifi_proxy = self.bus.get_proxy(
                    service_name="org.freedesktop.NetworkManager",
                    object_path=net_proxy.SpecificObject,
                    interface_name="org.freedesktop.NetworkManager.AccessPoint",
                )
                networkdevice["wifi"] = {
                    "ssid": net_proxy.Id,
                    "strength": wifi_proxy.Strength,
                    "mac": wifi_proxy.HwAddress,
                    "freq": wifi_proxy.Frequency,
                }

            interfaces = []
            ipv4 = []
            ipv6 = []
            for device in net_proxy.Devices:
                dev_proxy = self.bus.get_proxy(
                    service_name="org.freedesktop.NetworkManager",
                    object_path=device,
                    interface_name="org.freedesktop.NetworkManager.Device",
                )
                interfaces.append(dev_proxy.Interface)

                ip4_proxy = self.bus.get_proxy(
                    service_name="org.freedesktop.NetworkManager",
                    object_path=dev_proxy.Ip4Config,
                    interface_name="org.freedesktop.NetworkManager.IP4Config",
                )
                if len(ip4_proxy.AddressData) > 0:
                    address4 = ip4_proxy.AddressData[0]["address"].get_string()
                    prefix4 = ip4_proxy.AddressData[0]["prefix"].get_uint32()
                    ipv4.append(f"{address4}/{prefix4}")

                ip6_proxy = self.bus.get_proxy(
                    service_name="org.freedesktop.NetworkManager",
                    object_path=dev_proxy.Ip6Config,
                    interface_name="org.freedesktop.NetworkManager.IP6Config",
                )
                if len(ip6_proxy.AddressData) > 0:
                    address6 = ip6_proxy.AddressData[0]["address"].get_string()
                    prefix6 = ip6_proxy.AddressData[0]["prefix"].get_uint32()
                    ipv6.append(f"{address6}/{prefix6}")
            networkdevice["interface"] = ",".join(interfaces)
            networkdevice["ipv4"] = ",".join(ipv4)
            networkdevice["ipv6"] = ",".join(ipv6)

            networkdevices.append(networkdevice)
        return networkdevices
