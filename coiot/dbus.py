#! /usr/bin/env python
import glob
from xml.etree import ElementTree
import logging

log = logging.getLogger('DBus')

INTROSPECTABLE_DBUS = """
<interface name="org.freedesktop.Introspectable">
</interface>
"""


class DBusDevice:
    def __init__(self, bus, proxy):
        self.proxy = proxy
        self.interfaces = set((i for i in (bus.get_interface_for(f)
                                           for f in dir(self.proxy)
                                           if f[0].isupper())
                               if i is not None))
        bus.register_device(self)

    def __setattr__(self, key, value):
        if key[0].islower():
            super().__setattr__(key, value)
            return
        log.debug("set {}.{} = {}".format(self.proxy, key, value))
        setattr(self.proxy, key, value)

    def __getattr__(self, key):
        if key[0].islower():
            return super().__getattr__(key)
        v = getattr(self.proxy, key)
        log.debug("get {}.{} = {}".format(self.proxy, key, v))

        return v if v is not None else ''


class CoiotDBusDeviceInterface:
    def __init__(self, device, path):
        self.device = device
        self.path = "/org/coiot/device/" + path
        self.dbus = '<node>{}</node>'.format("".join(device.interfaces))

    def register_on(self, bus):
        log.info('register {}'.format(self))
        return bus.register_object(self.path, self.device, self.dbus)

    def __str__(self):
        return "{} {}".format(self.path,
                              [e.attrib['name']
                               for e in ElementTree.fromstring(self.dbus)])


def CoiotDBusInterface(xml):
    class Interface:
        def __init__(self, et):
            self.et = et

        @property
        def fields(self):
            return [e.attrib['name']
                    for e in self.et]

        def __str__(self):
            return 'CoiotDBusInterface<{}>'.format(self.et.attrib['name'])

        def xml(self):
            return ElementTree.tostring(self.et).decode('utf-8')

    et = ElementTree.fromstring(xml)
    for e in et:
        if e.tag == 'interface':
            return Interface(e)


class CoiotDBus:
    def __init__(self, bus):
        self.bus = bus
        root_interface = ('/org/coiot/device', self,
                          "<node>{}</node>".format(INTROSPECTABLE_DBUS))
        self.publication = self.bus.publish('org.coiot', root_interface)
        self.known_interfaces = []
        for path in glob.glob('dbus-1/interfaces/org.coiot.*.xml'):
            with open(path, 'r') as f:
                self.known_interfaces.append(CoiotDBusInterface(f.read()))

    def register_device(self, device):
        d = CoiotDBusDeviceInterface(device, device.ID).register_on(self.bus)
        self.publication._at_exit(d.__exit__)

    def get_interface_for(self, field):
        for i in self.known_interfaces:
            if field in i.fields:
                return i.xml()
        return None
