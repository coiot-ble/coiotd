import sqlite3
import logging
from coiot.datetime import CoiotDatetime

log = logging.getLogger('DB')


class CoiotDBInterface:
    interfaces = set()

    @classmethod
    def declare(Cls, Interface):
        Cls.interfaces.add(Interface)
        log.info('declare {}'.format(Interface.__name__))
        return Interface

    @classmethod
    def load_all(Cls, device):
        for Interface in Cls.interfaces:
            device.load_interface(Interface)
        log.info('load {}'.format(device))


@CoiotDBInterface.declare
class Displayable:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT DISPLAYABLE.ID, DISPLAYABLE.Name, DISPLAYABLE_TYPE.Name
            FROM DISPLAYABLE
            LEFT JOIN DISPLAYABLE_TYPE
            ON DISPLAYABLE_TYPE.ID = DISPLAYABLE.Type
            WHERE Device = ?
            """, (self.id,)).fetchone()

        if r is None:
            return False

        self.__id, self.name, self.type = r
        return True

    @classmethod
    def install(Cls, self, Name, Type=None):
        if Type is not None:
            r = self.db.execute("""
                INSERT INTO DISPLAYABLE(Device, Name, Type)
                SELECT ?, ?, ID
                FROM DISPLAYABLE_TYPE
                WHERE Name = ?
                """, (self.id, Name, Type))
        else:
            r = self.db.execute("""
                INSERT INTO DISPLAYABLE(Device, Name)
                VALUES(?, ?)
                """, (self.id, Name))
        if r.lastrowid is None:
            raise Exception("Could not install the Displayable interface, "
                            "have you specified a correct type ?")
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
            LEFT JOIN DISPLAYABLE_TYPE
            ON DISPLAYABLE_TYPE.ID = DISPLAYABLE.Type
            WHERE DISPLAYABLE.ID = ?
            """, (self.__id,)).fetchone()[0]

    @Type.setter
    def Type(self, value):
        if value is None:
            self.db.execute("""
                UPDATE DISPLAYABLE
                SET Type = NULL
                WHERE ID = ?
                """, (self.__id,))
        else:
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
    def install(Cls, self, On):
        r = self.db.execute("""
            INSERT INTO SWITCHABLE(Device, FutureOn)
            VALUES(?, ?);
            """, (self.id, On,))
        self.__id = r.lastrowid
        self.db.execute("""
            INSERT INTO SWITCHABLE_LOG(Date, Switchable, Value)
            VALUES(?, ?, ?)
            """, (CoiotDatetime.now().epoch, self.__id, On))

    @property
    def On(self):
        return bool(self.db.execute("""
            SELECT Value
            FROM SWITCHABLE_LOG
            WHERE Switchable = ?
            ORDER BY ID DESC
            LIMIT 1
            """, (self.__id,)).fetchone()[0])

    @On.setter
    def On(self, value):
        self.db.execute("""
            INSERT INTO SWITCHABLE_LOG(Date, Switchable, Value)
            VALUES(?, ?, ?)
            """, (CoiotDatetime.now().epoch, self.__id, value))

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


def Composite():
    """
    Kind of a magical class that can have interfaces installed on a
    per-instance basis
    """

    def add_interface(Interface):
        CompositeCls.__bases__ = (Interface,) + CompositeCls.__bases__
        CompositeCls.__name__ = ", ".join([b.__name__
                                           for b in CompositeCls.__bases__
                                           if b is not DefaultObject])

    class DefaultObject:
        pass

    class CompositeCls(DefaultObject):
        def load_interface(self, Interface):
            if Interface.load(self):
                add_interface(Interface)

        def install_interface(self, Interface, *args, **kwargs):
            """
            Set up support for the given interface in the database
            """
            Interface.install(self, *args, **kwargs)
            add_interface(Interface)

    return CompositeCls


def CoiotDBDevice(*arg, **kw):
    """
    A bit complicated as a wrapper: acts as a constructor for the CoiotDBDevice
    generic class.
    This class checks for any interface the device supports when initialized
    and implements the associated interfaces. Interfaces can also be added at
    runtime, they will then be saved in the database.

    New interfaces need at least two class methods: load() and install().
    * load() sets up the given object from the database and returns True iif
    this was succesful (ie the object implements the interface in database)
    * install() add database support for the given interface
    See Switchable definition of these functions for more details.

    Any field implemented by the interface will be made available to the cache
    as a field to be get/set.
    Fields starting with "Future" are understood as future version of given
    properties. eg the field FutureFoo is the future of the property Foo
    Regular attributes or properties can be used indiferently. COIoT expects to
    always be able to set or get a field so if read-only or write-only
    properties are not supported (this is a database after all).
    """
    class CoiotDBDevice(Composite()):
        def __init__(self, db, did, pdid, last_online_epoch=None, Error=False):
            self.db = db
            self.id = did
            self.pdid = pdid
            self.online = False
            self.error = Error
            if last_online_epoch is None:
                last_online_epoch = self.db.execute("""
                    SELECT Date
                    FROM DEVICE_STATUS_LOG
                    WHERE Device = ?
                    ORDER BY ID DESC
                    LIMIT 1
                    """, (self.id,)).fetchone()[0]
            self.last_online = CoiotDatetime.from_epoch(last_online_epoch)
            CoiotDBInterface.load_all(self)

            def forbidden_attr(self, k, *args):
                raise AttributeError(k)
            self.__setattr__ = forbidden_attr

        def log_status(self):
            self.db.execute("""
                INSERT INTO DEVICE_STATUS_LOG(Device, Date, Online, Error)
                VALUES(?, ?, ?, ?)
                """, (self.id, CoiotDatetime.now().epoch,
                      self.online, self.error))

        @property
        def ID(self):
            return str(self.id)

        @property
        def Online(self):
            return self.online

        @Online.setter
        def Online(self, v):
            if self.online != v:
                self.online = v
                self.log_status()

        @property
        def LastOnline(self):
            return self.last_online.epoch * 1000

        @property
        def Error(self):
            return self.error

        @Error.setter
        def Error(self, v):
            if self.error != v:
                self.error = v
                self.log_status()

        def __str__(self):
            return "{}<{}>".format(type(self).__name__,
                                   self.__class__.__bases__[0].__name__)

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
        d = []
        for did, pdid, Error in self.db.execute("""
                SELECT DEVICE.ID, Parent, DEVICE_STATUS_LOG.Error
                FROM DEVICE
                JOIN DEVICE_STATUS_LOG
                ON DEVICE_STATUS_LOG.Device = DEVICE.ID
                GROUP BY DEVICE.ID
                ORDER BY DEVICE_STATUS_LOG.ID DESC
                """):
            d.append(CoiotDBDevice(self.db, did, pdid, Error=bool(Error)))
        return d

    def install(self, parent=None):
        if parent is None:
            pdid = None
        else:
            pdid = parent.id

        r = self.db.execute("""
            INSERT INTO DEVICE(Parent)
            VALUES(?)
            """, (pdid,))
        device = CoiotDBDevice(self.db, r.lastrowid, pdid,
                               CoiotDatetime.now().epoch)
        self.db.execute("""
            INSERT INTO DEVICE_STATUS_LOG(Date, Device)
            VALUES(?, ?)
            """, (device.last_online.epoch, device.id,))
        return device
