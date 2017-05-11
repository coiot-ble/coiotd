from coiot.db import CoiotDBInterface, sqlite_cast
import logging

log = logging.getLogger('BLE')


class BLEDriverParameters:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, Mac
            FROM DRIVER_BLE
            WHERE Device = ?
            """, self.id).fetchone()
        if r is None:
            return False
        self.__id, self.Mac = r
        log.info("driver loaded for {}".format(self))
        return True

    @classmethod
    def install(Cls, self, Mac):
        Mac = sqlite_cast(str, Mac)
        r = self.db.execute("""
            INSERT INTO DRIVER_BLE(Device, Mac)
            VALUES(?, ?)
            """, self.id, Mac)
        self.__id = r.lastrowid
        self.Mac = Mac
        log.info("install driver for {}".format(self))

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
