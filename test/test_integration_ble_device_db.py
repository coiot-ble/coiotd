import time
import unittest
import ble
from coiot_device import CoiotDevice
import coiot_drivers
import coiot_db
import gatt_uuid
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
        self.db = coiot_db.CoiotDB(db_filename)
        self.db_device = self.db.install()
        self.db_device.install_interface(coiot_db.Switchable, On=False)
        self.db_device.install_interface(coiot_drivers.BLEDriverParameters,
                                         Mac="00:01:02:03:04:05")

        # ble
        self.adapter = MockBluezAdapter({
                "00:01:02:03:04:05": {
                    gatt_uuid.AUTOMATION_IO: StubDigitalAutomationIO()
                }
            })
        self.ble_device = self.adapter.devices["00:01:02:03:04:05"]
        self.ble_service = self.ble_device.services[gatt_uuid.AUTOMATION_IO]
        self.ble = ble.BleClient(self.adapter)

        self.ble_driver = coiot_drivers.BluezBLEDriver(self.ble)

        # devices
        self.updates = set()
        self.devices = CoiotDevice.load(self.db, lambda d: self.updates.add(d))

    def tearDown(self):
        self.ble_driver.thread.stop()

    def test_setup(self):
        self.assertEqual(1, len(self.devices))
        self.assertEqual(self.devices[0].On, False)

    def test_switch(self):
        self.devices[0].On = True
        time.sleep(0.01)
        self.assertEqual([True], self.ble_service.digital.value)
        self.assertEqual(self.devices[0].On, False)
        self.assertEqual(1, len(self.updates))
        self.updates.pop().update()
        self.assertEqual(self.devices[0].On, True)
