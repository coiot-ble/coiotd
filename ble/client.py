from . import gatt_uuid
from gi.repository import GLib
import logging

log = logging.getLogger('BLE')

drivers = []


def BleDriver(o):
    drivers.append(o)
    return o


class CompositeBleDevice:
    def __init__(self):
        self.objects = []

    def extend(self, o):
        self.objects.append(o)

    def __getattr__(self, k):
        if k[0].isupper():
            for o in self.objects:
                if k in dir(o):
                    return getattr(o, k)
        else:
            return super().__getattr__(k)

    def __setattr__(self, k, v):
        if k[0].isupper():
            for o in self.objects:
                if k in dir(o):
                    return setattr(o, k, v)
        else:
            return super().__setattr__(k, v)

    def __dir__(self):
        return [k for o in self.objects for k in dir(o)]


class BleAutomationIODigitalDevice:
    def __init__(self, ble_device, index):
        self.ble = ble_device
        self.index = index

    @property
    def On(self):
        return self.ble.read(self.index)

    @On.setter
    def On(self, value):
        return self.ble.write(value, self.index)


class BleAutomationIODigital:
    def __init__(self, characteristic):
        self.characteristic = characteristic
        self.gpios = {i: BleAutomationIODigitalDevice(self, i)
                      for i in range(0, len(self.read()))}
        log.debug("{} gpios: {}".format(len(self.gpios),
                                        list(self.gpios.keys())))

    @classmethod
    def readwrite_param(Cls, offset):
        if offset is None:
            return {}
        else:
            return {"offset": GLib.Variant('q', offset)}

    def read(self, offset=None):
        log.info('{} start ReadValue'.format(self.__class__.__name__))
        r = self.characteristic.ReadValue(self.readwrite_param(offset))
        log.info('{} ReadValue(offset={}) = {}'.format(self.__class__.__name__,
                                                       offset, r))
        if offset is not None:
            return bool(r[0])
        else:
            return r

    def write(self, value, offset=None):
        p = self.readwrite_param(offset)
        if offset is not None:
            value = [int(value)]
        log.info('{} start WriteValue'.format(type(self).__name__))
        self.characteristic.WriteValue(value, p)
        log.info('{} WriteValue(offset={}) = {}'.format(type(self).__name__,
                                                        offset, value))


@BleDriver
class BleAutomationIODigitalDriver:
    @classmethod
    def probe(Cls, device):
        service = device.services.get(gatt_uuid.AUTOMATION_IO)
        if not service:
            return {}
        characteristic = service.characteristics.get(gatt_uuid.DIGITAL)
        if not characteristic:
            return {}
        return BleAutomationIODigital(characteristic).gpios


class CompositeBleDeviceDict(dict):
    def __getitem__(self, k):
        return super().setdefault(k, CompositeBleDevice())


class BleDevicesDict(dict):
    def __getitem__(self, k):
        return super().setdefault(k, CompositeBleDeviceDict())


class BleClient:
    def __init__(self, adapter):
        log.info("new BleClient with adapter {}".format(adapter))
        self.adapter = adapter
        self.adapter.proxy.Powered = True
        self.devices = {}

    def refresh_devices(self):
        for a, d in self.adapter.devices.items():
            try:
                if a in self.devices:
                    if not d.proxy.Connected:
                        del self.devices[a]
                    else:
                        continue

                if not d.proxy.Connected:
                    continue

                for driver in drivers:
                    driver_devices = driver.probe(d)
                    for i, v in driver_devices.items():
                        da = self.devices.setdefault(a, {})
                        da.setdefault(i, CompositeBleDevice()).extend(v)
            except GLib.Error as e:
                epart = e.message.split(':')
                if epart[0] != "GDBus.Error":
                    raise
                if not epart[1].startswith("org.bluez.Error"):
                    raise
                emsg = ':'.join(epart[1:])
                log.error("{}: {}".format(d, emsg))
