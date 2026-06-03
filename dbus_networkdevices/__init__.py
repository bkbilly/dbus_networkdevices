import threading
from jeepney import DBusAddress, MatchRule, Properties, message_bus
from jeepney.io.blocking import open_dbus_connection

NM_BUS = 'org.freedesktop.NetworkManager'


def _get_prop(conn, object_path, interface, prop):
    addr = DBusAddress(object_path, bus_name=NM_BUS, interface=interface)
    reply = conn.send_and_get_reply(Properties(addr).get(prop))
    # Properties.Get returns a variant (type_signature, value)
    return reply.body[0][1]


class DBUSNetworkDevices():
    """docstring for DBUSNetworkDevices"""

    def __init__(self, callback=None):
        self.callback = callback

        if self.callback is not None:
            self.prev_send = None
            self.signal_conn = open_dbus_connection(bus='SYSTEM')

            for rule in [
                MatchRule(type='signal', interface='org.freedesktop.DBus.ObjectManager',
                          member='InterfacesAdded', path_namespace='/org/freedesktop'),
                MatchRule(type='signal', interface='org.freedesktop.DBus.ObjectManager',
                          member='InterfacesRemoved', path_namespace='/org/freedesktop'),
                MatchRule(type='signal', interface='org.freedesktop.DBus.Properties',
                          member='PropertiesChanged', path='/org/freedesktop/resolve1'),
            ]:
                self.signal_conn.send_and_get_reply(message_bus.AddMatch(rule))

            self.dbus_callback()
            threading.Thread(target=self._signal_loop, daemon=True).start()

    def _signal_loop(self):
        while True:
            self.signal_conn.recv_messages()
            try:
                self.dbus_callback()
            except Exception:
                pass

    def dbus_callback(self):
        conn = open_dbus_connection(bus='SYSTEM')
        self.network_devices = self.get_network_devices(conn)
        if self.prev_send != self.network_devices:
            self.prev_send = self.network_devices
            self.callback(self.network_devices)

    def get_network_devices(self, conn=None):
        if conn is None:
            conn = open_dbus_connection(bus='SYSTEM')

        active_connections = _get_prop(
            conn,
            '/org/freedesktop/NetworkManager',
            NM_BUS,
            'ActiveConnections',
        )

        networkdevices = []
        for connection in active_connections:
            name = _get_prop(conn, connection, 'org.freedesktop.NetworkManager.Connection.Active', 'Id')
            conn_type = _get_prop(conn, connection, 'org.freedesktop.NetworkManager.Connection.Active', 'Type')
            specific_object = _get_prop(conn, connection, 'org.freedesktop.NetworkManager.Connection.Active', 'SpecificObject')
            devices = _get_prop(conn, connection, 'org.freedesktop.NetworkManager.Connection.Active', 'Devices')

            networkdevice = {"name": name, "type": conn_type}

            if "AccessPoint" in specific_object:
                strength = _get_prop(conn, specific_object, 'org.freedesktop.NetworkManager.AccessPoint', 'Strength')
                hw_address = _get_prop(conn, specific_object, 'org.freedesktop.NetworkManager.AccessPoint', 'HwAddress')
                frequency = _get_prop(conn, specific_object, 'org.freedesktop.NetworkManager.AccessPoint', 'Frequency')
                networkdevice["wifi"] = {
                    "ssid": name,
                    "strength": strength,
                    "mac": hw_address,
                    "freq": frequency,
                }

            interfaces = []
            ipv4 = []
            ipv6 = []
            for device in devices:
                iface = _get_prop(conn, device, 'org.freedesktop.NetworkManager.Device', 'Interface')
                ip4_config = _get_prop(conn, device, 'org.freedesktop.NetworkManager.Device', 'Ip4Config')
                ip6_config = _get_prop(conn, device, 'org.freedesktop.NetworkManager.Device', 'Ip6Config')
                interfaces.append(iface)

                if ip4_config != '/':
                    address_data4 = _get_prop(conn, ip4_config, 'org.freedesktop.NetworkManager.IP4Config', 'AddressData')
                    if address_data4:
                        address4 = address_data4[0]["address"][1]
                        prefix4 = address_data4[0]["prefix"][1]
                        ipv4.append(f"{address4}/{prefix4}")

                if ip6_config != '/':
                    address_data6 = _get_prop(conn, ip6_config, 'org.freedesktop.NetworkManager.IP6Config', 'AddressData')
                    if address_data6:
                        address6 = address_data6[0]["address"][1]
                        prefix6 = address_data6[0]["prefix"][1]
                        ipv6.append(f"{address6}/{prefix6}")

            networkdevice["interface"] = ",".join(interfaces)
            networkdevice["ipv4"] = ",".join(ipv4)
            networkdevice["ipv6"] = ",".join(ipv6)
            networkdevices.append(networkdevice)

        return networkdevices
