#!/usr/bin/env python

import pydbus
from coiot.dbus_node import DBusNode


class DBusBluez(DBusNode):
    def __init__(self):
        super().__init__(pydbus.SystemBus(), 'org.bluez')

    @property
    def adapters(self):
        return self.get_children('^hci\d+', DBusAdapter)


class DBusAdapter(DBusNode):
    @property
    def devices(self):
        return self.get_children('^dev_', DBusDevice,
                                 key=lambda n, d: d.proxy.Address)


class DBusDevice(DBusNode):
    @property
    def services(self):
        return self.get_children('^service', DBusGattService,
                                 key=lambda n, s: s.proxy.UUID)


class DBusGattService(DBusNode):
    @property
    def characteristics(self):
        return self.get_children('^char', DBusGattCharacteristic,
                                 key=lambda n, c: c.proxy.UUID)


class DBusGattCharacteristic(DBusNode):
    pass
