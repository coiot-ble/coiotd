def formatUUID(*uuids):
    uuid_r = []
    for uuid in uuids:
        if type(uuid) is int:
            uuid_r.append('{:08x}-0000-1000-8000-00805f9b34fb'.format(uuid))
        else:
            uuid_r.append(uuid)
    return tuple(uuid_r) if len(uuid_r) > 1 else uuid_r[0]


class UUID:
    def __init__(self, value):
        self.value = formatUUID(value)

    def __eq__(self, other):
        return self.value == other

    def __hash__(self):
        return hash(self.value)


class ServiceUUID(UUID):
    pass


AUTOMATION_IO = ServiceUUID(0x1815)


class CharacteristicUUID(UUID):
    pass


DIGITAL = CharacteristicUUID(0x2a56)
