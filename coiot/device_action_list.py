import threading


class DeviceActionList:
    def __init__(self):
        self.list = {}
        self.cv = threading.Condition()

    def __bool__(self):
        return bool(self.list)

    def set(self, d, k, v):
        with self.cv:
            self.list[d, k] = v
            self.cv.notify()

    def pop(self, timeout=0.5):
        with self.cv:
            self.cv.wait_for(lambda: self.list, timeout)
            if self.list:
                (d, k), v = self.list.popitem()
                return (d, k, v)
            else:
                # timeout
                return None


class DALDevice:
    """
    Abstraction to access a device from another thread:
    - setting attribute will be done through the DeviceActionList
    - getting attributes is done from the device directly
    """
    def __init__(self, device, dal):
        self.dal = dal
        self.device = device

    def __getattr__(self, k):
        if not k[0].isupper():
            return super().__getattr__(k)
        return getattr(self.device, k)

    def __setattr__(self, k, v):
        if not k[0].isupper():
            super().__setattr__(k, v)
        else:
            if v != getattr(self.device, k):
                self.dal.set(self.device, k, v)
