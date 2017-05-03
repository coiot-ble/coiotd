#! /usr/bin/env python
import coiot_device
import coiot_db
import coiot_drivers
import os
import unittest


class TestCoiotDevice(unittest.TestCase):
    def setUp(self):
        filename = "/tmp/coiot.db"
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        self.db = coiot_db.CoiotDB(filename)
        d = self.db.install()
        d.install_interface(coiot_db.Displayable, Name="Foo")
        self.ble = coiot_drivers.BluezBLEDriver()
        self.devices = coiot_device.CoiotDevice.load(self.db)

    def tearDown(self):
        self.ble.thread.stop()

    def test_setup(self):
        self.devices[0].Name = "Bar"
        self.assertEqual("Foo", self.devices[0].Name)
