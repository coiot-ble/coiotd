import threading

class CoiotDevice:
    """
    This object acts in the intersection between the driver object (that actually
    access the device), the DB object (acting as a cache) and the DBus object (API)
    """
    def __init__(self, db):
        self.__dict__['db'] = db
        self.__dict__['list_not_empty'] = threading.Condition()
        self.__dict__['action_list'] = {}

    def __getattr__(self, k):
        return getattr(self.db, k)

    def __setattr__(self, k, v):
        with self.list_not_empty:
            setattr(self.db, "Future"+k, v)
            self.action_list[k] = v
            self.list_not_empty.notify()

    def update(self, k, v):
        setattr(self.db, k, v)

    def pop(self):
        with self.list_not_empty:
            while len(self.action_list) == 0:
                self.list_not_empty.wait()
        return self.action_list.popitem()

import time
import unittest
class CoiotDeviceUnitTest(unittest.TestCase):
    class MockDBProxy:
        def __init__(self, actual, future):
            self.__dict__['actual'] = actual
            self.__dict__['future'] = future

        def __getattr__(self, k):
            if k.startswith("Future"):
                return self.future[k.strip("Future")]
            else:
                return self.actual[k]

        def __setattr__(self, k, v):
            if k.startswith("Future"):
                self.future[k.strip("Future")] = v
            else:
                self.actual[k] = v

    def setup(self):
        self.a, self.f = {'Foo': 1, 'Bar': 'azerty'}, {}
        self.dut = CoiotDevice(CoiotDeviceUnitTest.MockDBProxy(self.a, self.f))

    def test_get(self):
        self.setup()

        self.assertEqual(1, self.dut.Foo)
        self.assertEqual('azerty', self.dut.Bar)

    def test_set_update(self):
        self.setup()

        self.dut.Foo = 2
        self.assertEqual(1, self.dut.Foo)
        self.dut.update('Foo', 2)
        self.assertEqual(2, self.dut.Foo)

    def test_set_update_with_thread(self):
        class UpdateNTimesThread(threading.Thread):
            def __init__(self, device, updates):
                super().__init__()
                self.updates = updates
                self.device = device

            def run(self):
                while self.updates > 0:
                    i = self.device.pop()
                    self.device.update(*i)
                    self.updates -= 1
        self.setup()

        t = UpdateNTimesThread(self.dut, 2)
        t.start()
        
        time.sleep(0.1)

        self.dut.Foo = 2
        self.dut.Bar = 'qwerty'
        time.sleep(0.1)
        self.assertEqual(2, self.dut.Foo)
        self.assertEqual('qwerty', self.dut.Bar)
