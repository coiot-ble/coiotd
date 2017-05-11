import coiot.db
import logging
import unittest.mock

log = logging.getLogger('Test')


class MockDeviceDriver:
    driver = unittest.mock.Mock()

    @classmethod
    def load(Cls, self):
        if hasattr(self, 'driver'):
            log.error("{}: {} already has a driver: {}".format(Cls, self,
                                                               self.driver))
            return
        self.driver = Cls.driver
        log.info('Mock driver loaded for {}'.format(self))
        return True

    @classmethod
    def register(Cls):
        coiot.db.CoiotDBInterface.declare(Cls)

    @classmethod
    def unregister(Cls):
        coiot.db.CoiotDBInterface.undeclare(Cls)
