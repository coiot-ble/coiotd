#! /usr/bin/env python

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
    def __init__(self, proxy, *interfaces):
        self.proxy = proxy
        self.interfaces = interfaces
        CoiotDBus.instance.register_device(self)

    def __setattr__(self, key, value):
        if key[0].islower():
            object.__setattr__(self, key, value)
            return
        setattr(self.proxy, key, value)

    def __getattr__(self, key):
        if key[0].islower():
            return object.__getattr__(self, key)
        return getattr(self.proxy, key)


class CoiotDBusDeviceInterface:
    def __init__(self, device, path):
        self.device = device
        self.path = "/org/coiot/" + path
        self.dbus = '<node>{}</node>'.format("".join(device.interfaces))

    def register_on(self, bus):
        return bus.register_object(self.device, self.path, self.dbus)


class CoiotDBus:
    instance = None

    def __init__(self, bus):
        self.bus = bus
        root_interface = ('/org/coiot', self,
                       "<node>{}</node>".format(INTROSPECTABLE_DBUS))
        self.publication = self.bus.publish('org.coiot', root_interface)
        CoiotDBus.instance = self

    def register_device(self, device):
        d = CoiotDBusDeviceInterface(device, device.ID).register_on(self.bus)
        self.publication._at_exit(d.__exit__)
