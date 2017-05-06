from coiot.action_list import DeviceActionList
import threading
import coiot.db
from . import client, gatt_uuid
import logging

log = logging.getLogger('BLE')


@coiot.db.CoiotDBInterface.declare
class BLEDriverParameters:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, Mac
            FROM DRIVER_BLE
            WHERE Device = ?
            """, (self.id,)).fetchone()
        if r is None:
            return False
        self.__id, self.Mac = r
        log.info("driver loaded for {}".format(self))
        return True

    @classmethod
    def install(Cls, self, Mac):
        r = self.db.execute("""
            INSERT INTO DRIVER_BLE(Device, Mac)
            VALUES(?, ?)
            """, (self.id, Mac))
        self.__id = r.lastrowid
        self.Mac = Mac
        log.info("install driver for {}".format(self))

    @property
    def driver(self):
        return BluezBLEDriver.instance


class BluezBLEDriver:
    class BluezThread(threading.Thread):
        def __init__(self, driver):
            super().__init__()
            self.driver = driver
            self.stopped = False

        def stop(self):
            self.stopped = True

        def run(self):
            while not self.stopped:
                t = self.driver.action_list.pop()
                if t is not None:
                    d, k, v = t
                    self.driver.set(d, k, v)

    def __init__(self, client):
        self.client = client
        self.thread = BluezBLEDriver.BluezThread(self)
        self.action_list = DeviceActionList()
        type(self).instance = self
        self.thread.start()

    instance = None

    def connect(self, device):
        device.add_action_list(self.action_list.new(device))

    def set(self, device, k, v):
        log.info("{} {} = {}".format(device.Mac, k, v))
        if self.client is not None:
            ble_dev = self.client.devices[device.Mac]
            if k == "On":
                sv = ble_dev.services[gatt_uuid.AUTOMATION_IO]
                char = sv.characteristics[gatt_uuid.DIGITAL]
                client.BleAutomationIODigital(char).gpios[0].on = v
        device.queue_update(k, v)
        log.info("success {} {} = {}".format(device.Mac, k, v))

    def __str__(self):
        return type(self).__name__
