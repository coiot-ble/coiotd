import bluez

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
        self.adapter.Powered = True

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

    def connect(self):
        for d in self.devices.values():
            d.proxy.Connect()
