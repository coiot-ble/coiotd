#! /usr/bin/env python
from coiot.device import CoiotDevice
import coiot.db
import os
import unittest
from test.mock_driver import MockDeviceDriver


class TestCoiotDevice(unittest.TestCase):
    def setUp(self):
        filename = "/tmp/coiot.db"
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        self.db = coiot.db.CoiotDB(filename)
        dbd = self.db.install()
        dbd.install_interface(coiot.db.Displayable, Name="Foo")
        MockDeviceDriver.register()
        self.devices = CoiotDevice.load(self.db)

    def tearDown(self):
        MockDeviceDriver.unregister()

    def test_setup(self):
        self.assertEqual(1, len(self.devices))
        self.assertEqual("Foo", self.devices[0].Name)

    def test_set(self):
        MockDeviceDriver.driver.register.assert_called_once()
        d = self.devices[0]
        d.Name = "Bar"
        self.assertEqual("Foo", d.Name)
        self.assertEqual("Bar", d.driver.Name)
        d.update("Name", "Bar")
        self.assertEqual("Bar", d.Name)
