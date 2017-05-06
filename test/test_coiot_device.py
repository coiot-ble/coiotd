#! /usr/bin/env python
from coiot.device import CoiotDevice
import coiot.db
from ble import driver
import os
import unittest


class TestCoiotDevice(unittest.TestCase):
    def setUp(self):
        filename = "/tmp/coiot.db"
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        self.db = coiot.db.CoiotDB(filename)
        d = self.db.install()
        d.install_interface(coiot.db.Displayable, Name="Foo")
        d.install_interface(driver.BLEDriverParameters,
                            Mac="00:01:02:03:04:05")
        self.ble = driver.BluezBLEDriver(None)
        self.updates = []
        self.devices = CoiotDevice.load(self.db,
                                        lambda d: self.updates.append(d))

    def tearDown(self):
        self.ble.thread.stop()

    def test_setup(self):
        self.devices[0].Name = "Bar"
        self.assertEqual("Foo", self.devices[0].Name)
        self.updates[0].update()
        self.assertEqual("Bar", self.devices[0].Name)
