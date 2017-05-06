import threading


class DeviceActionList:
    class ActionList:
        def __init__(self, device, dal):
            self.device = device
            self.dal = dal

        def __setitem__(self, k, v):
            with self.dal.cv:
                self.dal.list[self.device, k] = v
                self.dal.cv.notify()

    def __init__(self):
        self.list = {}
        self.cv = threading.Condition()

    def new(self, device):
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
