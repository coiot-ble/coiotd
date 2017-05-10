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
