import threading

class DriverActionsList:
    class ActionList:
        def __init__(self, device, dal):
            self.device = device
            self.dal = dal
        
        def __setitem__(self, k, v):
            with self.dal.cv:
                self.dal.list[self.device, k] =  v
                self.dal.cv.notify()

    def __init__(self):
        self.list = {}
        self.cv = threading.Condition()

    def add(self, device):
        return type(self).ActionList(device, self)

    def pop(self, timeout=0.5):
        with self.cv:
            self.cv.wait_for(lambda: self.list, timeout)
            if self.list:
                t, v = self.list.popitem()
                return (*t, v)
            else:
                # timeout
                return None

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

    def __init__(self):
        self.thread = BluezBLEDriver.BluezThread(self)
        self.action_list = DriverActionsList()
        self.thread.start()

    def connect(self, device):
        device.action_list = self.action_list.add(device)

    def set(self, device, k, v):
        print(type(self).__name__, device, k, "<=", v)
