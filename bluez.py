#!/usr/bin/env python

from xml.etree import ElementTree
import re

class DBusNode:
    def __init__(self, bus, service, path=None):
        self.bus = bus
        self.service = service
        if path is None:
            path = '/' + service.replace('.','/')
        self.path = path

    @property
    def proxy(self):
        if 'proxy' not in self.__dict__:
            self.__dict__['proxy'] = self.bus.get(self.service, self.path)
        return self.__dict__['proxy']

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            return getattr(self.proxy, name)

    def clear_cache(self):
        del self.__dict__['proxy']

    def get_children(self, filt, Cls, key=lambda n,v: n):
        children = {}
        for n in [e.attrib['name'] for e in ElementTree.fromstring(self.proxy.Introspect()) if e.tag == 'node']:
            if re.match(filt, n):
                v = Cls(self.bus, self.service, self.path+'/'+n)
                children[key(n,v)] = v
        return children

    def __repr__(self):
        return '{}({}, \'{}\', \'{}\')'.format(type(self).__name__, self.bus, self.service, self.path)

class DBusBluez(DBusNode):
    def __init__(self):
        super().__init__(pydbus.SystemBus(), 'org.bluez')

    @property
    def adapters(self):
        return self.get_children('^hci\d+', DBusAdapter)

class DBusAdapter(DBusNode):
    @property
    def devices(self):
        return self.get_children('^dev_', DBusDevice, key=lambda n,d: d.proxy.Address)

class DBusDevice(DBusNode):
    @property
    def services(self):
        return self.get_children('^service', DBusGattService, key=lambda n,s: s.proxy.UUID)

class DBusGattService(DBusNode):
    @property
    def characteristics(self):
        return self.get_children('^char', DBusGattCharacteristic, key=lambda n,c: c.proxy.UUID)

class DBusGattCharacteristic(DBusNode):
    pass
