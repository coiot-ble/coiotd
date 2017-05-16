import sqlite3
import logging
from coiot.datetime import CoiotDatetime
import os
import glob

log = logging.getLogger('DB')


def sqlite_cast(vtype, v):
    """
    Returns the casted version of v, for use in
    database.
    SQLite does not perform any type check or conversion
    so this function should be used anytime a data comes
    from outstide to be put in database.

    This function also handles CoiotDatetime objects and
    accepts "now" as an argument for them (the date will
    then be the calling date of this function).
    """

    if vtype is type(v) or v is None:
        return v

    if vtype is bool:
        if type(v) is int:
            return bool(v)
        elif type(v) is str and v.lower() in ('true', 'false'):
            return v.lower() == 'true'
    elif vtype is int:
        if type(v) in (bool, str):
            return int(v)
    elif vtype is str:
        return str(v)
    elif vtype is CoiotDatetime:
        if type(v) in (float, int):
            return CoiotDatetime.fromepoch(v)
        elif v.lower() == 'now':
            return CoiotDatetime.now()

    raise TypeError("argument of type {} cannot be " +
                    "casted to {}".format(type(v), vtype))


class CoiotDBInterface:
    interfaces = set()

    @classmethod
    def declare(Cls, Interface):
        Cls.interfaces.add(Interface)
        log.info('declare {}'.format(Interface.__name__))
        return Interface

    @classmethod
    def undeclare(Cls, Interface):
        Cls.interfaces.discard(Interface)
        log.info('undeclare {}'.format(Interface.__name__))
        return Interface

    @classmethod
    def load_all(Cls, device):
        for Interface in Cls.interfaces:
            device.load_interface(Interface)
        log.info('load {}'.format(device))

    @classmethod
    def get(Cls, ifname):
        for Interface in Cls.interfaces:
            if Interface.__name__ == ifname:
                return Interface
        return None


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
            """, self.id).fetchone()

        if r is None:
            return False

        self.__id, self.name, self.type = r
        self.FutureName = self.name
        self.FutureType = self.type
        return True

    @classmethod
    def install(Cls, self, Name, Type=None):
        Name = sqlite_cast(str, Name)
        Type = sqlite_cast(str, Type)
        if Type is not None:
            r = self.db.execute("""
                INSERT INTO DISPLAYABLE(Device, Name, Type)
                SELECT ?, ?, ID
                FROM DISPLAYABLE_TYPE
                WHERE Name = ?
                """, self.id, Name, Type)
        else:
            r = self.db.execute("""
                INSERT INTO DISPLAYABLE(Device, Name)
                VALUES(?, ?)
                """, self.id, Name)
        if r.lastrowid is None:
            raise Exception("Could not install the Displayable interface, "
                            "have you specified a correct type ?")
        self.FutureName = Name
        self.FutureType = Type
        self.__id = r.lastrowid

    @property
    def Name(self):
        return self.db.execute("""
            SELECT Name
            FROM DISPLAYABLE
            WHERE ID = ?
            """, self.__id).fetchone()[0]

    @Name.setter
    def Name(self, value):
        value = sqlite_cast(str, value)
        self.db.execute("""
            UPDATE DISPLAYABLE
            SET Name = ?
            WHERE ID = ?
            """, value, self.__id)

    @property
    def Type(self):
        return self.db.execute("""
            SELECT DISPLAYABLE_TYPE.Name
            FROM DISPLAYABLE
            LEFT JOIN DISPLAYABLE_TYPE
            ON DISPLAYABLE_TYPE.ID = DISPLAYABLE.Type
            WHERE DISPLAYABLE.ID = ?
            """, self.__id).fetchone()[0]

    @Type.setter
    def Type(self, value):
        value = sqlite_cast(str, value)
        if value is None:
            self.db.execute("""
                UPDATE DISPLAYABLE
                SET Type = NULL
                WHERE ID = ?
                """, self.__id)
        else:
            self.db.execute("""
                UPDATE DISPLAYABLE
                SET Type = (
                    SELECT ID
                    FROM DISPLAYABLE_TYPE
                    WHERE Name = ?)
                WHERE ID = ?
                """, value, self.__id)


@CoiotDBInterface.declare
class Switchable:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, FutureOn
            FROM SWITCHABLE
            WHERE Device = ?;
            """, self.id).fetchone()

        if r is None:
            return False

        self.__id, self.future_on = r[0], bool(r[1])
        return True

    @classmethod
    def install(Cls, self, On):
        On = sqlite_cast(bool, On)
        r = self.db.execute("""
            INSERT INTO SWITCHABLE(Device, FutureOn)
            VALUES(?, ?);
            """, self.id, On)
        self.__id = r.lastrowid
        self.db.execute("""
            INSERT INTO SWITCHABLE_LOG(Date, Switchable, Value)
            VALUES(?, ?, ?)
            """, CoiotDatetime.now(), self.__id, On)

    @property
    def On(self):
        return bool(self.db.execute("""
            SELECT Value
            FROM SWITCHABLE_LOG
            WHERE Switchable = ?
            ORDER BY ID DESC
            LIMIT 1
            """, self.__id).fetchone()[0])

    @On.setter
    def On(self, value):
        value = sqlite_cast(bool, value)
        self.db.execute("""
            INSERT INTO SWITCHABLE_LOG(Date, Switchable, Value)
            VALUES(?, ?, ?)
            """, CoiotDatetime.now(), self.__id, value)

    @property
    def FutureOn(self):
        return bool(self.db.execute("""
            SELECT FutureOn
            FROM SWITCHABLE
            WHERE ID = ?
            """, self.__id).fetchone()[0])

    @FutureOn.setter
    def FutureOn(self, value):
        value = sqlite_cast(bool, value)
        self.db.execute("""
            UPDATE SWITCHABLE
            SET FutureOn = ?
            WHERE ID = ?
            """, value, self.__id)


def Composite():
    """
    Kind of a magical class that can have interfaces installed on a
    per-instance basis
    """
    class DefaultObject:
        pass

    def add_interface(self, Interface):
        CompositeCls.__bases__ = (Interface,) + CompositeCls.__bases__
        CompositeCls.__name__ = ", ".join([b.__name__
                                           for b in CompositeCls.__bases__
                                           if b is not DefaultObject])
        if hasattr(Interface, 'init_interface'):
            Interface.init_interface(self)

    class CompositeCls(DefaultObject):
        def load_interface(self, Interface):
            if Interface.load(self):
                add_interface(self, Interface)

        def install_interface(self, Interface, *args, **kwargs):
            Interface.install(self, *args, **kwargs)
            add_interface(self, Interface)

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
        def __init__(self, db, did, pdid, last_online=None, Error=False):
            self.db = db
            self.id = did
            self.pdid = pdid
            self.online = False
            self.error = sqlite_cast(bool, Error)
            self.FutureError = self.error
            if last_online is None:
                self.last_online = CoiotDatetime.from_epoch(self.db.execute("""
                    SELECT Date
                    FROM DEVICE_STATUS_LOG
                    WHERE Device = ?
                    ORDER BY ID DESC
                    LIMIT 1
                    """, self.id).fetchone()[0])
            else:
                self.last_online = sqlite_cast(CoiotDatetime, last_online)
            CoiotDBInterface.load_all(self)

            def forbidden_attr(self, k, *args):
                raise AttributeError(k)
            self.__setattr__ = forbidden_attr

        def log_status(self):
            self.db.execute("""
                            INSERT INTO DEVICE_STATUS_LOG(Device, Date,
                                                          Online, Error)
                            VALUES(?, ?, ?, ?)
                            """,
                            self.id, CoiotDatetime.now(),
                            self.online, self.error)

        @property
        def ID(self):
            return str(self.id)

        @property
        def Online(self):
            return self.online

        @Online.setter
        def Online(self, v):
            v = sqlite_cast(bool, v)
            if self.online != v:
                self.online = v
                self.log_status()

        @property
        def LastOnline(self):
            return self.last_online.epoch

        @property
        def Error(self):
            return self.error

        @Error.setter
        def Error(self, v):
            v = sqlite_cast(bool, v)
            if self.error != v:
                self.error = v
                self.log_status()

        def __str__(self):
            return "{}<ID={}, {}>".format(type(self).__name__, self.ID,
                                          self.__class__.__bases__[0].__name__)

    return CoiotDBDevice(*arg, **kw)


class CoiotDB:
    def __init__(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.isolation_level = None
        version = next(iter(self.db.execute("PRAGMA USER_VERSION")))[0]
        if version == 0:
            log.info("create database {}".format(filename))
        curpath = os.path.dirname(os.path.realpath(__file__))
        globexpr = "{}/../sql/*.sql".format(curpath)
        for f in sorted(glob.glob(globexpr)):
            v = int(f.split('/')[-1].split('-')[0])
            if v > version:
                log.info("execute {}".format(f))
                with open(f, 'r') as fd:
                    self.db.executescript(fd.read())
            self.db.execute("PRAGMA USER_VERSION={}".format(v))

    @property
    def devices(self):
        d = {}
        for did, pdid, Error in self.execute("""
                SELECT DEVICE.ID, Parent, DEVICE_STATUS_LOG.Error
                FROM DEVICE
                JOIN DEVICE_STATUS_LOG
                ON DEVICE_STATUS_LOG.Device = DEVICE.ID
                GROUP BY DEVICE.ID
                ORDER BY DEVICE_STATUS_LOG.ID DESC
                """):
            d[did] = CoiotDBDevice(self, did, pdid, Error=bool(Error))
        return d

    def install(self, parent=None):
        if parent is None:
            pdid = None
        else:
            pdid = parent.id

        r = self.execute("""
            INSERT INTO DEVICE(Parent)
            VALUES(?)
            """, pdid)
        device = CoiotDBDevice(self, r.lastrowid, pdid,
                               CoiotDatetime.now())
        self.execute("""
            INSERT INTO DEVICE_STATUS_LOG(Date, Device)
            VALUES(?, ?)
            """, device.last_online, device.id)
        return device

    def execute(self, req, *args):
        """
        Executes the query after performing type conversion on custom types.
        """
        sqlite_args = ()
        for a in args:
            if type(a) is CoiotDatetime:
                a = a.epoch
            sqlite_args += (a,)

        return self.db.execute(req, sqlite_args)
