import coiot.db
import logging
import unittest.mock

log = logging.getLogger('Test')


def register():
    @coiot.db.CoiotDBInterface.declare
    class MockDriverDevice:

        @classmethod
        def load(Cls, self):
            self.driver = unittest.mock.Mock()
            self.list = {}
            self.driver.connect = lambda d: d.add_action_list(self.list)
            log.info('Mock driver loaded for {}'.format(self))
            return True
