import time
import unittest
from coiot.device import CoiotDevice
from ble import client, driver, gatt_uuid
import coiot.db
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
        self.db_device.install_interface(driver.BLEDriverParameters,
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

        self.driver = driver.BluezBLEDriver(self.client)

        # devices
        self.updates = set()
        self.devices = CoiotDevice.load(self.db, lambda d: self.updates.add(d))

    def tearDown(self):
        self.driver.thread.stop()

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
