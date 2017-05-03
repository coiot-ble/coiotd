def formatUUID(*uuids):
    uuid_r = []
    for uuid in uuids:
        if type(uuid) is int:
            uuid_r.append('{:08x}-0000-1000-8000-00805f9b34fb'.format(uuid))
        else:
            uuid_r.append(uuid)
    return tuple(uuid_r) if len(uuid_r) > 1 else uuid_r[0]

class UUID_SERVICE:
    AUTOMATION_IO = 0x1815

class UUID_CHARACTERISTIC:
    DIGITAL = 0x2a56
