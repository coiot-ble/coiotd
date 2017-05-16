import threading
from coiot.device_action_list import DeviceActionList, DALDevice
from . import db_interface
import logging
import time

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
                dkprev = tuple(self.driver.client.devices.keys())
                self.driver.client.refresh_devices()
                for a in [a
                          for a in self.driver.client.devices.keys()
                          if a not in dkprev]:
                    self.driver.update_status(a, Online=True)
                for a in [a
                          for a in dkprev
                          if a not in self.driver.client.devices.keys()]:
                    self.driver.update_status(a, Online=False)
                if not self.driver.client.devices:
                    time.sleep(1)
                else:
                    t = self.driver.action_list.pop()
                    if t is not None:
                        self.driver.ble_set(*t)

    def __init__(self, client, updates):
        self.client = client
        self.thread = BluezBLEDriver.BluezThread(self)
        self.action_list = DeviceActionList()
        self.updates = updates
        self.devices = {}
        db_interface.BLEDriverParameters.register_driver(self)
        self.thread.start()

    def stop(self):
        self.thread.stop()

    def ble_set(self, device, k, v):
        log.info("{} {} = {}".format(device.Mac, k, v))
        if self.client is not None:
            ble_dev = self.client.devices[device.Mac][device.Idx]
            setattr(ble_dev, k, v)
        self.updates.set(device, k, v)
        log.info("success {} {} = {}".format(device.Mac, k, v))

    def update_status(self, Mac, Online):
        self.updates.set(self.devices[Mac], 'Online', Online)

    def declare_error(self, Mac):
        self.updates.set(self.devices[Mac], 'Error', True)
        self.updates.set(self.devices[Mac], 'Online', False)

    def register(self, dev):
        self.devices[dev.Mac] = DALDevice(dev, self.updates)
        return DALDevice(dev, self.action_list)

    def __str__(self):
        return type(self).__name__
