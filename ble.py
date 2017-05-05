import gatt_uuid
from gatt_uuid import formatUUID
from gi.repository import GLib
import logging

log = logging.getLogger('BLE')


class BleAutomationIODigitalSingle:
    def __init__(self, ble_device, index):
        self.ble = ble_device
        self.index = index

    @property
    def on(self):
        return self.ble.read(self.index)

    @on.setter
    def on(self, value):
        return self.ble.write(value, self.index)


class BleAutomationIODigital:
    def __init__(self, characteristic):
        self.characteristic = characteristic
        self.gpios = [BleAutomationIODigitalSingle(self, i)
                      for i in range(0, len(self.read()))]

    @classmethod
    def readwrite_param(Cls, offset):
        if offset is None:
            return {}
        else:
            return {"offset": GLib.Variant('q', offset)}

    def read(self, offset=None):
        r = self.characteristic.ReadValue(self.readwrite_param(offset))
        if offset is not None:
            return bool(r[0])
        else:
            return r

    def write(self, value, offset=None):
        p = self.readwrite_param(offset)
        if offset is not None:
            self.characteristic.WriteValue([int(value)], p)
        else:
            self.characteristic.WriteValue(value, p)


class BleClient:
    def __init__(self, adapter):
        log.info("new BleClient with adapter {}".format(adapter))
        self.adapter = adapter
        self.adapter.proxy.Powered = True

    @property
    def devices(self):
        return {a: d for (a, d) in self.adapter.devices.items()
                if 'coiot' in d.proxy.Alias.lower()}

    def get_services_by_uuid(self, uuid):
        uuid = formatUUID(uuid)
        r = {}
        for a, d in self.devices.items():
            for u, s in d.services.items():
                if u == uuid:
                    r[a] = s
                    break
        return r

    def get_characteristics_by_uuid(self, service_uuid, characteristic_uuid):
        service_uuid, characteristic_uuid = formatUUID(service_uuid,
                                                       characteristic_uuid)
        r = {}
        for (a, s) in self.get_services_by_uuid(service_uuid).items():
            for u, c in s.characteristics.items():
                if u == characteristic_uuid:
                    r[a] = c
                    break
        return r

    def get_every_single_gpio(self):
        gpios = {}
        cc = self.get_characteristics_by_uuid(gatt_uuid.AUTOMATION_IO,
                                              gatt_uuid.DIGITAL)
        for n, c in cc.items():
            gpios[n] = BleAutomationIODigital(c).gpios

        return gpios

    def connect(self):
        for d in self.devices.values():
            log.info("connect to {}".format(d))
            d.proxy.Connect()
