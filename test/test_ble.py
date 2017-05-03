import unittest
import gatt_uuid
import ble
from test.mock_ble import MockBluezAdapter, StubDigitalAutomationIO


class TestBle(unittest.TestCase):
    """
    A single device, with a single digital io
    """
    def setUp(self):
        self.adapter = MockBluezAdapter({
                "00:01:02:03:04:05": {
                    gatt_uuid.AUTOMATION_IO: StubDigitalAutomationIO()
                }
            })
        self.device = self.adapter.devices["00:01:02:03:04:05"]
        self.digital_service = self.device.services[gatt_uuid.AUTOMATION_IO]
        self.ble = ble.BleClient(self.adapter)

    def test_setup(self):
        self.assertTrue(self.adapter.proxy.Powered)
        self.ble.connect()
        self.assertTrue(self.device.proxy.connected)


class TestDigital(TestBle):
    """
    A single device, with a single digital io
    """
    def test_gpio_count(self):
        gpio = self.ble.get_every_single_gpio()
        self.assertEqual(1, len(gpio))
        self.assertEqual(1, len(gpio.popitem()[1]))

    def test_switch_on_off(self):
        gpios = self.ble.get_every_single_gpio()
        self.assertEqual(len(gpios['00:01:02:03:04:05']), 1)
        gpios['00:01:02:03:04:05'][0].on = True
        self.assertEqual(self.digital_service.digital.value, [True])
        gpios['00:01:02:03:04:05'][0].on = False
        self.assertEqual(self.digital_service.digital.value, [False])


class TestMultipleDigital(unittest.TestCase):
    """
    A single device, with multiple digital io
    """
    def setUp(self):
        self.adapter = MockBluezAdapter({
                "00:01:02:03:04:05": {
                    gatt_uuid.AUTOMATION_IO: StubDigitalAutomationIO(2)
                }
            })
        self.device = self.adapter.devices["00:01:02:03:04:05"]
        self.digital_service = self.device.services[gatt_uuid.AUTOMATION_IO]
        self.ble = ble.BleClient(self.adapter)
        self.gpio = self.ble.get_every_single_gpio()

    def test_gpio_count(self):
        self.assertEqual(1, len(self.gpio))
        self.assertEqual(2, len(self.gpio.popitem()[1]))

    def test_value(self):
        gpio = self.gpio["00:01:02:03:04:05"]
        gpio[0].on = True
        self.assertEqual(self.digital_service.digital.value, [True, False])
        gpio[1].on = True
        self.assertEqual(self.digital_service.digital.value, [True, True])
        gpio[0].on = False
        self.assertEqual(self.digital_service.digital.value, [False, True])
        gpio[1].on = False
        self.assertEqual(self.digital_service.digital.value, [False, False])
