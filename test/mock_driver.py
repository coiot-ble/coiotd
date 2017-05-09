import coiot.db
import logging
import unittest.mock

log = logging.getLogger('Test')


class MockDriverDevice:
    update_list = {}

    @classmethod
    def load(Cls, self):
        self.driver = unittest.mock.Mock()

        def connect(device):
            device.add_action_list(Cls.update_list.setdefault(device, {}))

        self.driver.connect = connect
        log.info('Mock driver loaded for {}'.format(self))
        return True


def register():
    coiot.db.CoiotDBInterface.declare(MockDriverDevice)
