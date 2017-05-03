import unittest
from gatt_uuid import formatUUID, UUID_SERVICE, UUID_CHARACTERISTIC
import ble

class MockBluezAdapter:
    def __init__(self, devices):
        self.devices = { k:MockDBusDevice(v) for (k,v) in devices.items() }
        class MockBluezAdapterProxy:
            def __init__(self):
                self.Powered = False
        self.proxy = MockBluezAdapterProxy()

class MockDBusDevice:
    def __init__(self, services):
        self.services = { formatUUID(k): v for (k,v) in services.items() }
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
        self.characteristics = {formatUUID(k): v for (k,v) in characteristics.items()}

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
                    return [self.value]

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
        super().__init__({UUID_CHARACTERISTIC.DIGITAL: self.digital})

class TestBle(unittest.TestCase):
    def setUp(self):
        self.mock_digital = StubDigitalAutomationIO()
        self.adapter = MockBluezAdapter({
                "00:01:02:03:04:05" : {
                    UUID_SERVICE.AUTOMATION_IO : self.mock_digital
                }
            })
        self.ble = ble.BleClient(self.adapter)

    def test_setup(self):
        self.assertTrue(self.adapter.proxy.Powered)
        self.ble.connect()
        self.assertEqual(1, len(self.ble.get_every_single_gpio()))
        self.assertTrue(self.adapter.devices["00:01:02:03:04:05"].proxy.connected)

class TestDigital(TestBle):
    def test_switch_on_off(self):
        gpios = self.ble.get_every_single_gpio()
        self.assertEqual(len(gpios['00:01:02:03:04:05']), 1)
        gpios['00:01:02:03:04:05'][0].on = True
        self.assertEqual(self.mock_digital.digital.value, [True])
        gpios['00:01:02:03:04:05'][0].on = False
        self.assertEqual(self.mock_digital.digital.value, [False])
