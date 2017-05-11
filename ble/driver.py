import threading
from coiot.device_action_list import DeviceActionList
from . import client, gatt_uuid, db_interface
import logging

log = logging.getLogger('BLE')


db_interface.BLEDriverParameters.register()


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
                    self.driver.ble_set(*t)

    def __init__(self, client, updates):
        self.client = client
        self.thread = BluezBLEDriver.BluezThread(self)
        self.action_list = DeviceActionList()
        self.updates = updates
        db_interface.BLEDriverParameters.register_driver(self)
        self.thread.start()

    def set(self, device, k, v):
        self.action_list.set(device, k, v)

    def ble_set(self, device, k, v):
        log.info("{} {} = {}".format(device.Mac, k, v))
        if self.client is not None:
            ble_dev = self.client.devices[device.Mac]
            if k == "On":
                sv = ble_dev.services[gatt_uuid.AUTOMATION_IO]
                char = sv.characteristics[gatt_uuid.DIGITAL]
                client.BleAutomationIODigital(char).gpios[0].on = v
        self.updates.set(device, k, v)
        log.info("success {} {} = {}".format(device.Mac, k, v))

    def __str__(self):
        return type(self).__name__
