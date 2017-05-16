from coiot.db import CoiotDBInterface, sqlite_cast
import logging

log = logging.getLogger('BLE')


class BLEDriverParameters:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, Mac, Idx
            FROM DRIVER_BLE
            WHERE Device = ?
            """, self.id).fetchone()
        if r is None:
            return False
        self.__id, self.Mac, self.Idx = r
        return True

    @classmethod
    def install(Cls, self, Mac, Idx=None):
        Mac = sqlite_cast(str, Mac)
        Idx = sqlite_cast(int, Idx)
        r = self.db.execute("""
            INSERT INTO DRIVER_BLE(Device, Mac, Idx)
            VALUES(?, ?, ?)
            """, self.id, Mac, Idx)
        self.__id = r.lastrowid
        self.Mac = Mac
        self.Idx = Idx

    @property
    def driver(self):
        if hasattr(BLEDriverParameters, 'driver'):
            return BLEDriverParameters.driver
        else:
            return None

    @classmethod
    def register(Cls):
        CoiotDBInterface.declare(Cls)

    @classmethod
    def register_driver(Cls, driver):
        Cls.driver = driver
