import sqlite3

class CoiotDBInterface:
    interfaces = set()

    @classmethod
    def declare(Cls, Interface):
        Cls.interfaces.add(Interface)
        return Interface

    @classmethod
    def load_all(Cls, device):
        for Interface in Cls.interfaces:
            device.load_interface(Interface)

@CoiotDBInterface.declare
class Displayable:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT DISPLAYABLE.ID, DISPLAYABLE.Name, DISPLAYABLE_TYPE.Name
            FROM DISPLAYABLE
            JOIN DISPLAYABLE_TYPE
            ON DISPLAYABLE_TYPE.ID = DISPLAYABLE.Type
            WHERE Device = ?
            """, (self.id,)).fetchone()

        if r is None:
            return False

        self.__id, self.name, self.type = r
        return True

    @classmethod
    def install(Cls, self):
        r = self.db.execute("""
            INSERT INTO DISPLAYABLE(Device, Name, Type)
            SELECT ?, ?, ID
            FROM DISPLAYABLE_TYPE
            WHERE Name = ?
            """, (self.id, self.name, self.type))
        if r.lastrowid is None:
            raise Exception("Could not install the Displayable interface, have you specified a correct type ?")
        self.__id = r.lastrowid

    @property
    def Name(self):
        return self.db.execute("""
            SELECT Name
            FROM DISPLAYABLE
            WHERE ID = ?
            """, (self.__id,)).fetchone()[0]

    @Name.setter
    def Name(self, value):
        self.db.execute("""
            UPDATE DISPLAYABLE
            SET Name = ?
            WHERE ID = ?
            """, (value, self.__id,))

    @property
    def Type(self):
        return self.db.execute("""
            SELECT DISPLAYABLE_TYPE.Name
            FROM DISPLAYABLE
            JOIN DISPLAYABLE_TYPE
            ON DISPLAYABLE_TYPE.ID = DISPLAYABLE.Type
            WHERE DISPLAYABLE.ID = ?
            """, (self.__id,)).fetchone()[0]

    @Type.setter
    def Type(self, value):
        self.db.execute("""
            UPDATE DISPLAYABLE
            SET Type = (
                SELECT ID
                FROM DISPLAYABLE_TYPE
                WHERE Name = ?)
            WHERE ID = ?
            """, (value, self.__id,))

@CoiotDBInterface.declare
class Switchable:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, FutureOn
            FROM SWITCHABLE
            WHERE Device = ?;
            """, (self.id,)).fetchone()

        if r is None:
            return False

        self.__id, self.future_on = r[0], bool(r[1])
        return True

    @classmethod
    def install(Cls, self):
        r = self.db.execute("""
            INSERT INTO SWITCHABLE(Device, FutureOn)
            VALUES(?, ?);
            """, (self.id, self.future_on,))
        self.__id = r.lastrowid

    @property
    def On(self):
        return bool(self.db.execute("""
            SELECT Value
            FROM SWITCHABLE_LOG
            WHERE Switchable = ?
            ORDER BY ID DESC
            """, (self.__id,)).fetchone()[0])

    @On.setter
    def On(self, value):
        self.db.execute("""
            INSERT INTO SWITCHABLE_LOG(Switchable, Value)
            VALUES(?, ?)
            """, (self.__id, value))

    @property
    def FutureOn(self):
        return bool(self.db.execute("""
            SELECT FutureOn
            FROM SWITCHABLE
            WHERE ID = ?
            """, (self.__id,)).fetchone()[0])

    @FutureOn.setter
    def FutureOn(self, value):
        self.db.execute("""
            UPDATE SWITCHABLE
            SET FutureOn = ?
            WHERE ID = ?
            """, (value, self.__id,))

def CoiotDBDevice(*arg, **kw):
    """
    A bit complicated as a wrapper: acts as a constructor for the CoiotDBDevice generic class.
    This class checks for any interface the device supports when initialized and implements
    the associated interfaces. Interfaces can also be added at runtime, they will then be
    saved in the database.

    New interfaces need at least two class methods: load() and install().
    * load() sets up the given object from the database and returns True iif this was succesful (ie the
    object implements the interface in database)
    * install() add database support for the given interface
    See Switchable definition of these functions for more details.

    Any field implemented by the interface will be made available to the cache as a field to be get/set.
    Fields starting with "Future" are understood as future version of given properties.
    eg the field FutureFoo is the future of the property Foo
    Regular attributes or properties can be used indiferently. COIoT expects to always be able to set or get
    a field so if read-only or write-only properties are not supported (this is a database after all).
    """
    def Composite():
        class DefaultObject: pass
        class CompositeCls(DefaultObject):
            def load_interface(self, Interface):
                if Interface.load(self):
                    CompositeCls.__bases__ = (Interface,) + CompositeCls.__bases__

            def install_interface(self, Interface):
                """
                Set up support for the given interface in the database
                """
                Interface.install(self)
                CompositeCls.__bases__ = (Interface,) + CompositeCls.__bases__

        return CompositeCls

    class CoiotDBDevice(Composite()):
        def __init__(self, db, did, pdid):
            self.db = db
            self.id = did
            self.pdid = pdid
            CoiotDBInterface.load_all(self)

    return CoiotDBDevice(*arg, **kw)

class CoiotDB:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.isolation_level = None
        version = next(iter(self.db.execute("PRAGMA USER_VERSION")))[0]
        if version != 1:
            with open('sql/create_db.sql') as f:
                self.db.executescript(f.read())

    @property
    def devices(self):
        d = {}
        for driver, did, parent in self.db.execute("""
            SELECT Driver, ID, Parent
            FROM DEVICE
            WHERE ONLINE = 1;
            """):
            d.setdefault(driver, []).append(CoiotDBDevice(self.db, did, parent))
        return d

    def install(self, driver, parent):
        if parent is None:
            pdid = None
        else:
            pdid = parent.id

        r = self.db.execute("""
            INSERT INTO DEVICE(Driver, Parent, Online)
            VALUES(?, ?, ?);""",
            (driver, pdid, True))
        device = CoiotDBDevice(self.db, r.lastrowid, pdid)
        return device

import unittest

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

        d = self.db.install("BLE", None)
        self.assertTrue('BLE' in self.db.devices)
        self.assertEqual(1, len(self.db.devices['BLE']))

    def test_install_with_parent(self):
        self.setup()
        parent = self.db.install("BLE", None)
        device = self.db.install("BLE", parent)
        self.assertEqual(2, len(self.db.devices['BLE']))

    def test_install_switchable_inheritance(self):
        self.setup()
        device = self.db.install("BLE", None)
        d2 = self.db.install("BLE", None)

        device.future_on = False
        device.install_interface(Switchable)

        self.assertTrue(isinstance(device, Switchable))
        self.assertTrue(not isinstance(d2, Switchable))

class OneDeviceTestSetup(CoiotDBTestSetup):
    """
    Test setup: a device with no interface in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device = self.db.install("BLE", None)

    def reload(self):
        self.setup(cleanup = False)
        self.device = self.db.devices['BLE'][0]

    def test_reload(self):
        self.setup(cleanup = False)
        self.assertTrue('BLE' in self.db.devices)
        self.assertEqual(1, len(self.db.devices['BLE']))
        self.device = self.db.devices['BLE'][0]

class DisplayableUnitTest(OneDeviceTestSetup):
    """
    Test setup: a Displayable device in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device.name = "Desk lamp"
            self.device.type = "Lamp"
            self.device.install_interface(Displayable)

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

class SwitchableUnitTest(OneDeviceTestSetup):
    """
    Test setup: a Switchable device in database.
    """
    def setup(self, cleanup=True, **kwargs):
        super().setup(cleanup=cleanup, **kwargs)
        if cleanup:
            self.device.future_on = False
            self.device.install_interface(Switchable)

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
            self.device.future_on = False
            self.device.install_interface(Switchable)
            self.device.name = "Bed socket"
            self.device.type = "Wall Socket"
            self.device.install_interface(Displayable)

    def test_setup_install(self):
        self.setup()
        self.assertTrue(isinstance(self.device, Switchable))
        self.assertTrue(isinstance(self.device, Displayable))
