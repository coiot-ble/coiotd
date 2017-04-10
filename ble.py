import bluez
from gi.repository import GLib


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
        self.gpios = [ BleAutomationIODigitalSingle(self, i) for i in range(0, len(self.read())) ]

    def read(self, offset=None):
        if offset is not None:
            return bool(self.characteristic.ReadValue({"offset": GLib.Variant('q', offset)})[0])
        else:
            return self.characteristic.ReadValue({})

    def write(self, value, offset=None):
        if offset is not None:
            self.characteristic.WriteValue([int(value)], {"offset": GLib.Variant('q', offset)})
        else:
            self.characteristic.WriteValue(value, {})


def formatUUID(*uuids):
    uuid_r = []
    for uuid in uuids:
        if type(uuid) is int:
            uuid_r.append('{:08x}-0000-1000-8000-00805f9b34fb'.format(uuid))
        else:
            uuid_r.append(uuid)
    return tuple(uuid_r) if len(uuid_r) > 1 else uuid_r[0]


class BleClient:
    def __init__(self, adapter='hci0'):
        self.adapter = bluez.DBusBluez().adapters[adapter]
        self.adapter.proxy.Powered = True

    @property
    def devices(self):
        return { a: d for (a,d) in self.adapter.devices.items() if 'coiot' in d.proxy.Alias.lower() }

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
        service_uuid, characteristic_uuid = formatUUID(service_uuid, characteristic_uuid)
        r = {}
        for (a, s) in self.get_services_by_uuid(service_uuid).items():
            for u, c in s.characteristics.items():
                if u == characteristic_uuid:
                    r[a] = c
                    break
        return r

    def get_every_single_gpio(self):
        gpios = {}
        cc = self.get_characteristics_by_uuid(0x1815, 0x2a56)
        for n, c in cc.items():
            gpios[n] = BleAutomationIODigital(c).gpios

        return gpios

    def connect(self):
        for d in self.devices.values():
            d.proxy.Connect()
