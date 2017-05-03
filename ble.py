from gatt_uuid import formatUUID, UUID_SERVICE, UUID_CHARACTERISTIC
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


class BleClient:
    def __init__(self, adapter):
        self.adapter = adapter
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
        cc = self.get_characteristics_by_uuid(UUID_SERVICE.AUTOMATION_IO, UUID_CHARACTERISTIC.DIGITAL)
        for n, c in cc.items():
            gpios[n] = BleAutomationIODigital(c).gpios

        return gpios

    def connect(self):
        for d in self.devices.values():
            d.proxy.Connect()
