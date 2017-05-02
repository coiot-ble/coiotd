#! /usr/bin/env python
import coiot_device
import coiot_db
import coiot_drivers
import os
import unittest

class TestCoiotDevice(unittest.TestCase):
    def setup(self):
        filename = "/tmp/coiot.db"
        os.remove(filename)
        self.db = coiot_db.CoiotDB(filename)
        d = self.db.install("BLE")
        d.install_interface(coiot_db.Displayable, Name = "Foo")
        self.ble = coiot_drivers.BluezBLEDriver()
        self.devices = coiot_device.load_coiot_devices(self.db, {"BLE": self.ble}) 

    def test_setup(self):
        self.setup()
        self.devices[0].Name = "Bar"
        self.assertEqual("Foo", self.devices[0].Name)

        self.ble.thread.stop()
