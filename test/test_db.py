import unittest
from coiot_db import CoiotDB, Switchable, Displayable

class CoiotDBTestSetup(unittest.TestCase):
    def setup(self, cleanup=True, filename = "/tmp/coiot.db"):
        if cleanup:
            import os
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
        self.db = CoiotDB(filename)

class CoiotDBUnitTest(CoiotDBTestSetup):
    """
    Test setup: database is empty
    """
    def setup(self, cleanup=True):
        filename = "/tmp/coiot.db"
        if cleanup:
            import os
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
        self.db = CoiotDB(filename)

    def test_creation(self):
        self.setup()

        self.assertEqual(0, len(self.db.devices))

    def test_install_no_parent(self):
        self.setup()

        d = self.db.install()
        self.assertEqual(1, len(self.db.devices))

    def test_install_with_parent(self):
        self.setup()
        parent = self.db.install()
        device = self.db.install(parent)
        self.assertEqual(2, len(self.db.devices))

    def test_install_switchable_inheritance(self):
        self.setup()
        device = self.db.install()
        d2 = self.db.install()

        device.install_interface(Switchable, On = False)

        self.assertTrue(isinstance(device, Switchable))
        self.assertTrue(not isinstance(d2, Switchable))

class OneDeviceTestSetup(CoiotDBTestSetup):
    """
    Test setup: a device with no interface in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device = self.db.install()

    def reload(self):
        self.setup(cleanup = False)
        self.device = self.db.devices[0]

    def test_reload(self):
        self.setup(cleanup = False)
        self.assertEqual(1, len(self.db.devices))
        self.device = self.db.devices[0]

class DisplayableUnitTest(OneDeviceTestSetup):
    """
    Test setup: a Displayable device in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device.install_interface(Displayable, Name = "Desk lamp", Type = "Lamp")

    def test_setup_install(self):
        self.setup()
        self.assertTrue(isinstance(self.device, Displayable))

    def test_load(self):
        self.setup()
        self.test_reload()
        self.assertTrue(isinstance(self.device, Displayable))

    def test_name(self):
        self.setup()
        self.device.Name = "Bed lamp"
        self.reload()
        self.assertEqual("Bed lamp", self.device.Name)

    def test_type(self):
        self.setup()
        self.device.Type = "Wall Socket"
        self.reload()
        self.assertEqual("Wall Socket", self.device.Type)

    def test_type_NULL(self):
        self.setup()
        self.device.Type = None
        self.assertEqual(None, self.device.Type)
        self.reload()
        self.assertEqual(None, self.device.Type)

    def test_install_type_NULL(self):
        self.setup()
        d2 = self.db.install()
        d2.install_interface(Displayable, Name="Foo")
        self.reload()
        self.assertEqual(None, d2.Type)

class SwitchableUnitTest(OneDeviceTestSetup):
    """
    Test setup: a Switchable device in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device.install_interface(Switchable, On = False)

    def test_setup_install(self):
        self.setup()
        self.assertTrue(isinstance(self.device, Switchable))

    def test_load(self):
        self.setup()
        self.test_reload()
        self.assertTrue(isinstance(self.device, Switchable))

    def test_set_on_off(self):
        self.setup()

        self.device.On = True
        self.reload()
        self.assertTrue(self.device.On)

        self.device.On = False
        self.reload()
        self.assertTrue(not self.device.On)

    def test_set_future(self):
        self.setup()

        self.device.On = True
        self.device.FutureOn = False
        self.reload()
        self.assertEqual(self.device.FutureOn, False)

        self.device.On = self.device.FutureOn
        self.reload()
        self.assertEqual(self.device.FutureOn, self.device.On)

        self.device.FutureOn = True
        self.reload()
        self.assertEqual(self.device.FutureOn, True)

class SwitchableAndDisplayableUnitTest(OneDeviceTestSetup):
    """
    Test setup: a device that is switchable and displayable
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device.install_interface(Switchable, On = False)
            self.device.install_interface(Displayable, Name = "Bed socket", Type = "Wall socket")

    def test_setup_install(self):
        self.setup()
        self.assertTrue(isinstance(self.device, Switchable))
        self.assertTrue(isinstance(self.device, Displayable))
