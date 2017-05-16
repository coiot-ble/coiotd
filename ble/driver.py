import threading
from coiot.device_action_list import DeviceActionList, DALDevice
from ble.device import CompositeBleDevice, drivers
from gi.repository import GLib
from . import db_interface
import logging
import time

log = logging.getLogger('BLE')


db_interface.BLEDriverParameters.register()


class BluezBLEDriver(threading.Thread):
    def __init__(self, adapter, updates, autostart=True):
        super().__init__()
        self.adapter = adapter
        self.action_list = DeviceActionList()
        self.updates = updates
        self.cache = {}
        self.ble_devices = {}
        db_interface.BLEDriverParameters.register_driver(self)
        self.stopped = False
        self.adapter.proxy.Powered = True
        if autostart:
            self.start()

    def stop(self):
        self.stopped = True

    def refresh_devices(self):
        for a, d in self.adapter.devices.items():
            try:
                if a in self.ble_devices:
                    if not d.proxy.Connected:
                        del self.ble_devices[a]
                    else:
                        continue

                if not d.proxy.Connected:
                    continue

                for driver in drivers:
                    driver_devices = driver.probe(d)
                    for i, v in driver_devices.items():
                        da = self.ble_devices.setdefault(a, {})
                        da.setdefault(i, CompositeBleDevice()).extend(v)
            except GLib.Error as e:
                epart = e.message.split(':')
                if epart[0] != "GDBus.Error":
                    raise
                if not epart[1].startswith("org.bluez.Error"):
                    raise
                emsg = ':'.join(epart[1:])
                log.error("{}: {}".format(d, emsg))

    def run(self):
        while not self.stopped:
            dkprev = set(self.ble_devices.keys())
            self.refresh_devices()
            for a in set(self.ble_devices.keys()).union(dkprev):
                self.cache[a].Online = (a in self.ble_devices.keys())

            if not self.ble_devices:
                time.sleep(1)
            else:
                t = self.action_list.pop()
                if t is not None:
                    d, k, v = t
                    log.info("{} {} = {}".format(d.Mac, k, v))
                    ble_dev = self.ble_devices[d.Mac][d.Idx]
                    setattr(ble_dev, k, v)
                    setattr(self.devices[d.Mac], k, v)
                    log.info("success {}[{}] {} = {}".format(d.Mac, d.Idx,
                                                             k, v))

    def register(self, cache):
        self.cache[cache.Mac][cache.Idx] = DALDevice(cache, self.updates)
        return DALDevice(cache, self.action_list)

    def __str__(self):
        return type(self).__name__
