import time
import unittest
from unittest.mock import Mock
from coiot.device import CoiotDevice
from coiot.dbus import DBusDevice, CoiotDBus
from coiot.device_action_list import DeviceActionList
from ble import client, driver, gatt_uuid
import coiot.db
from ble.db_interface import BLEDriverParameters
from test.mock_ble import MockBluezAdapter, StubDigitalAutomationIO


class TestIntegrationBLEDeviceDBSwitchable(unittest.TestCase):
    def setUp(self, cleanup=True, db_filename="/tmp/coiot.db"):
        # database
        if cleanup:
            import os
            try:
                os.remove(db_filename)
            except FileNotFoundError:
                pass
        self.db = coiot.db.CoiotDB(db_filename)
        self.db_device = self.db.install()
        self.db_device.install_interface(coiot.db.Switchable, On=False)
        self.db_device.install_interface(BLEDriverParameters,
                                         Mac="00:01:02:03:04:05")

        # ble
        self.adapter = MockBluezAdapter({
                "00:01:02:03:04:05": {
                    gatt_uuid.AUTOMATION_IO: StubDigitalAutomationIO()
                }
            })
        self.ble_device = self.adapter.devices["00:01:02:03:04:05"]
        self.ble_service = self.ble_device.services[gatt_uuid.AUTOMATION_IO]
        self.client = client.BleClient(self.adapter)

        self.updates = DeviceActionList()
        self.driver = driver.BluezBLEDriver(self.client, self.updates)

        # devices
        self.devices = CoiotDevice.load(self.db)

        # dbus
        self.dbus_bus = Mock()
        reg_rv = Mock()
        reg_rv.__enter__ = Mock(return_value=(Mock(), None))
        reg_rv.__exit__ = None
        self.dbus_bus.register_object.return_value = reg_rv

        self.dbus = CoiotDBus(self.dbus_bus)
        for d in self.devices:
            DBusDevice(self.dbus, d)
        self.dbus_device = self.dbus_bus.register_object.call_args[0][1]

    def tearDown(self):
        self.driver.thread.stop()

    def test_setup(self):
        self.assertEqual(1, len(self.devices))
        self.assertEqual(self.dbus_device.On, False)

    def test_switch(self):
        self.dbus_device.On = True
        time.sleep(0.01)
        self.assertEqual([True], self.ble_service.digital.value)
        self.assertEqual(self.dbus_device.On, False)
        self.assertTrue(self.updates)
        d, k, v = self.updates.pop()
        d.update(k, v)
        self.assertFalse(self.updates)
        self.assertEqual(self.dbus_device.On, True)
