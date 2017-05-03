import gatt_uuid
from gatt_uuid import formatUUID


class MockBluezAdapter:
    def __init__(self, devices):
        self.devices = {k: MockDBusDevice(v) for (k, v) in devices.items()}

        class MockBluezAdapterProxy:
            def __init__(self):
                self.Powered = False
        self.proxy = MockBluezAdapterProxy()


class MockDBusDevice:
    def __init__(self, services):
        self.services = {formatUUID(k): v for (k, v) in services.items()}

        class MockDBusDeviceProxy:
            def __init__(self):
                self.Alias = "CoiotMock"
                self.Name = "CoiotMock"
                self.connected = False

            def Connect(self):
                self.connected = True

        self.proxy = MockDBusDeviceProxy()


class MockDBusGattService:
    def __init__(self, characteristics):
        self.characteristics = {formatUUID(k): v
                                for (k, v) in characteristics.items()}


class StubDigitalAutomationIO(MockDBusGattService):
    def __init__(self, inputs=1):
        class StubDigital:
            def __init__(self, inputs):
                self.value = [False] * inputs

            def ReadValue(self, darg):
                if 'offset' in darg:
                    assert(darg['offset'].is_signature('q'))
                    offset = darg['offset'].get_uint16()
                    return [self.value[offset]]
                else:
                    offset = None
                    return self.value[:]

            def WriteValue(self, value, darg):
                if 'offset' in darg:
                    assert(darg['offset'].is_signature('q'))
                    assert(len(value) == 1)
                    offset = darg['offset'].get_uint16()
                    self.value[offset] = bool(value[0])
                else:
                    assert(len(value) == len(self.value))
                    self.value = [bool(v) for v in value]
        self.digital = StubDigital(inputs)
        super().__init__({gatt_uuid.DIGITAL: self.digital})
