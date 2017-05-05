#! /usr/bin/env python
import pydbus

COIOT_DISPLAYABLE1_DBUS = """
<interface name="org.coiot.Displayable1">
    <property name="Name" type="s" access="readwrite" />
    <property name="Type" type="s" access="readwrite" />
</interface>
"""
COIOT_SWITCHABLE1_DBUS = """
<interface name="org.coiot.Switchable1">
    <property name="On" type="b" access="readwrite" />
</interface>
"""
INTROSPECTABLE_DBUS = """
<interface name="org.freedesktop.Introspectable">
</interface>
"""


class DBusDevice:
    """
    Generic class to use in order to declare a device on DBus.
    Instances of that class act as a dictionnary to give access to
    COIoT specific attributes. This allows for properties to be
    discovered at runtime through a generic mechanism.
    """
    def __init__(self, *interfaces):
        self.interfaces = interfaces

    def keys(self):
        return []

    def items(self):
        return {n: getattr(self, n) for n in self.keys()}.items()

    def __setitem__(self, key, value):
        if key not in self.keys():
            raise KeyError()
        setattr(self, key, value)

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError()
        getattr(self, key)

    def __iter__(self):
        return iter(self.keys())


class DBusDisplayable(DBusDevice):
    def __init__(self, *interfaces):
        super().__init__(COIOT_DISPLAYABLE1_DBUS, *interfaces)

    def keys(self):
        return ["Name", "Type"].extend(super().keys())

    @property
    def Name(self):
        return type(self).__name__


class DBusLamp(DBusDisplayable):
    def __init__(self, device):
        super().__init__(COIOT_SWITCHABLE1_DBUS)
        self.Type = "Lamp"
        self.device = device

    def keys(self):
        return ["On"].extend(super().keys())

    @property
    def On(self):
        return self.device.on

    @On.setter
    def On(self, value):
        self.device.on = value


class CoiotDBusDeviceInterface:
    def __init__(self, device, path):
        self.device = device
        self.path = "/org/coiot/" + path
        self.dbus = '<node>{}</node>'.format("".join(device.interfaces))


class CoiotDBus:
    def __init__(self, client):
        self.client = client
        self.bus = pydbus.SystemBus()
        default_pub = ('/org/coiot', self,
                       "<node>{}</node>".format(INTROSPECTABLE_DBUS))
        self.publication = self.bus.publish('org.coiot', default_pub)
        self.register_devices()

    def register_devices(self):
        for i, d in enumerate(self.client.devices.values()):
            d = self.bus.register_object(CoiotDBusDeviceInterface(d, str(i)))
            self.publication._at_exit(d.__exit__)
