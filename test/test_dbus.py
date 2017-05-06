#! /usr/bin/env python
from coiot_dbus import DBusDevice, CoiotDBus
import unittest
from unittest.mock import Mock
from xml.etree import ElementTree


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

        self.coiot_bus = CoiotDBus(self.bus)

    def test_setup(self):
        self.bus.publish.assert_called_once()
        self.assertEqual('org.coiot', self.bus.publish.call_args[0][0])

class CoiotDBusDisplayableTest(CoiotDBusBasicTest):
    """
    One displayable object on the bus
    """
    def setUp(self):
        super().setUp()

        self.device = Mock()
        self.device.ID = "1"
        self.device.Name = "foo"
        self.device.Type = "Bar"

        self.dbus_device = DBusDevice(self.device)

    def test_setup(self):
        self.bus.register_object.assert_called_once()
        register_args = self.bus.register_object.call_args[0]
        self.assertEqual(self.dbus_device, register_args[0])
        self.assertEqual('/org/coiot/1', register_args[1])
        # interface inference
        et = ElementTree.fromstring(register_args[2])
        self.assertTrue(any((e.tag == "interface"
                             and e.attrib['name'] == "org.coiot.Displayable1"
                             for e in et)))

    def test_get(self):
        self.assertEqual(self.device.Name, self.dbus_device.Name)
        self.assertEqual(self.device.Type, self.dbus_device.Type)

    def test_set(self):
        self.dbus_device.Name = "Foo"
        self.assertEqual("Foo", self.device.Name)

class CoiotDBusMultipleInterfacesTest(CoiotDBusBasicTest):
    """
    One object on the bus with interfaces Displayable1, Switchable1, Sensor1
    """
    def setUp(self):
        super().setUp()

        self.device = Mock()
        self.device.ID = "1"
        self.device.Name = "foo"
        self.device.Type = "Bar"
        self.device.On = False
        self.device.SwitchableLog = lambda f, t: [(1, False), (2, True)]
        self.device.Value = 1337
        self.device.Exponent = -2
        self.device.Unit = "Degree C"
        self.device.MeasureDate = 3
        self.device.SensorLog = lambda f, t: [(1, 1234), (2, 1515)]
        self.dbus_device = DBusDevice(self.device)

    def test_setup(self):
        self.bus.register_object.assert_called_once()
        register_args = self.bus.register_object.call_args[0]
        self.assertEqual(self.dbus_device, register_args[0])
        self.assertEqual('/org/coiot/1', register_args[1])
        # interface inference
        et = ElementTree.fromstring(register_args[2])
        for itname in ('Displayable1', 'Sensor1', 'Switchable1'):
            self.assertTrue(any((e.tag == "interface"
                                 and e.attrib['name'] == "org.coiot." + itname
                                 for e in et)))

    def test_get(self):
        self.assertEqual(self.device.Name, self.dbus_device.Name)
        self.assertEqual(self.device.Type, self.dbus_device.Type)

    def test_set(self):
        self.dbus_device.Name = "Foo"
        self.assertEqual("Foo", self.device.Name)
