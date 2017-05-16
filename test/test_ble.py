import logging
import sys
import unittest
from unittest.mock import Mock
from gi.repository import GLib
from ble import driver, gatt_uuid

log = logging.getLogger('BLE')
log.addHandler(logging.StreamHandler(sys.stdout))
log.level = logging.DEBUG


def aio_offset(i):
    if i is None:
        return {}
    return {'offset': GLib.Variant('q', i)}


class TestBle(unittest.TestCase):
    """
    A single device, with a single digital io
    """
    def setUp(self):
        self.gpio = Mock()
        self.gpio.ReadValue.return_value = [0]

        aiod = Mock()
        aiod.characteristics = {
                gatt_uuid.formatUUID(gatt_uuid.DIGITAL): self.gpio
            }

        self.device = Mock()
        self.device.services = {
                gatt_uuid.formatUUID(gatt_uuid.AUTOMATION_IO): aiod
            }
        self.device.proxy.Alias = "Coiot dev"
        self.device.proxy.Connected = True

        self.adapter = Mock()
        self.adapter.devices = {"00:01:02:03:04:05": self.device}

        self.driver = driver.BluezBLEDriver(self.adapter, None,
                                            autostart=False)

    def test_setup(self):
        self.assertTrue(self.adapter.proxy.Powered)
        self.driver.refresh_devices()
        self.gpio.ReadValue.assert_called_once_with(aio_offset(None))
        self.assertEqual(1, len(self.driver.ble_devices))

        client_device = self.driver.ble_devices["00:01:02:03:04:05"]
        self.assertEqual(1, len(client_device))
        self.assertEqual(False, client_device[0].On)

    def test_switch_online_offline(self):
        cache = Mock()
        cache.Mac = "00:01:02:03:04:05"
        cache.Idx = 0
        self.assertTrue(self.driver.register(cache) is not None)

        self.device.proxy.Connected = False
        self.driver.refresh_devices()
        self.assertTrue(cache.Mac not in self.driver.ble_devices)

        self.device.proxy.Connected = True
        self.driver.refresh_devices()
        self.assertTrue(cache.Mac in self.driver.ble_devices)


class TestDigital(TestBle):
    """
    A single device, with a single digital io
    """

    def setUp(self):
        super().setUp()
        self.driver.refresh_devices()
        self.client_device = self.driver.ble_devices["00:01:02:03:04:05"]

    def test_setup(self):
        pass

    def test_switch_on_off(self):
        self.client_device[0].On = True
        self.gpio.WriteValue.assert_called_once_with([1], aio_offset(0))

        self.gpio.WriteValue.reset_mock()
        self.client_device[0].On = False
        self.gpio.WriteValue.assert_called_once_with([0], aio_offset(0))

    def test_write_does_no_read(self):
        self.gpio.ReadValue.reset_mock()
        self.client_device[0].On = True
        self.gpio.ReadValue.assert_not_called()


class TestMultipleDigital(TestBle):
    """
    A single device, with multiple digital io
    """
    def setUp(self):
        super().setUp()
        self.gpio.ReadValue.return_value = [0, 0]

    def test_setup(self):
        self.driver.refresh_devices()
        self.assertEqual(1, len(self.driver.ble_devices))

        client_device = self.driver.ble_devices["00:01:02:03:04:05"]
        self.assertEqual(2, len(client_device))
        self.gpio.ReadValue.assert_called_once_with(aio_offset(None))

        self.gpio.ReadValue = Mock(return_value=[0])
        self.assertEqual(False, client_device[0].On)
        self.gpio.ReadValue.assert_called_once_with(aio_offset(0))

        self.gpio.ReadValue = Mock(return_value=[1])
        self.assertEqual(True, client_device[1].On)
        self.gpio.ReadValue.assert_called_once_with(aio_offset(1))

    def test_value(self):
        self.driver.refresh_devices()

        client_device = self.driver.ble_devices["00:01:02:03:04:05"]
        client_device[0].On = True
        self.gpio.WriteValue.assert_called_once_with([1], aio_offset(0))
        client_device[1].On = False
        self.gpio.WriteValue.assert_called_with([0], aio_offset(1))
