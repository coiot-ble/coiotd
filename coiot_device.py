import threading

class CoiotDevice:
    def __init__(self, db):
        self.db = db
        self.list_not_empty = threading.Condition()
        self.action_list = {}

    def get(self, k):
        return self.db.get(k)

    def get_future(self, k):
        return self.db.get_future(k)

    def set(self, k, v):
        with self.list_not_empty:
            self.db.set_future(k, v)
            self.action_list[k] = v
            self.list_not_empty.notify()

    def update(self, k, v):
        self.db.set(k, v)

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
            self.actual = actual
            self.future = future

        def get(self, k):
            return self.actual[k]

        def get_future(self, k):
            return self.future[k]

        def set(self, k, v):
            self.actual[k] = v

        def set_future(self, k, v):
            self.future[k] = v

    def setup(self):
        self.a, self.f = {'foo': 1, 'bar': 'azerty'}, {}
        self.dut = CoiotDevice(CoiotDeviceUnitTest.MockDBProxy(self.a, self.f))

    def test_get(self):
        self.setup()

        self.assertEqual(1, self.dut.get('foo'))
        self.assertEqual('azerty', self.dut.get('bar'))

    def test_set_update(self):
        self.setup()

        self.dut.set('foo', 2)
        self.assertEqual(1, self.dut.get('foo'))
        self.dut.update('foo', 2)
        self.assertEqual(2, self.dut.get('foo'))

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

        self.dut.set('foo', 2)
        self.dut.set('bar', 'qwerty')
        time.sleep(0.1)
        self.assertEqual(2, self.dut.get('foo'))
        self.assertEqual('qwerty', self.dut.get('bar'))
