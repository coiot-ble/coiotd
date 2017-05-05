#! /usr/bin/env python
from coiot_dbus import DBusDevice, CoiotDBus, COIOT_DISPLAYABLE1_DBUS
import unittest
from unittest.mock import Mock


class CoiotDBusBasicTest(unittest.TestCase):
    """
    Very basic DBus tests, the goal is not to test that the DBus interface
    is correct, but rather that it correctly interfaces with the underlying
    CoiotDevice (straightforward set or get, displays correct devices).
    Testing the DBus interface [will be] done through a fully-featured
    COIoT DBus client.
    """
    def setUp(self):
        self.bus = Mock()
        self.bus.register_object.return_value = Mock()
        self.bus.register_object.return_value.__enter__ = Mock(return_value=(Mock(), None))
        self.bus.register_object.return_value.__exit__ = None

        self.device = Mock()
        self.device.ID = "1"
        self.device.Name = "foo"
        self.device.Type = "Bar"

        self.coiot_bus = CoiotDBus(self.bus)
        self.dbus_device = DBusDevice(self.device, COIOT_DISPLAYABLE1_DBUS)

    def test_setup(self):
        self.bus.publish.assert_called_once()
        self.assertEqual('org.coiot', self.bus.publish.call_args[0][0])

        self.bus.register_object.assert_called_once()
        register_args = self.bus.register_object.call_args[0]
        self.assertEqual(self.dbus_device, register_args[0])
        self.assertEqual('/org/coiot/1', register_args[1])
