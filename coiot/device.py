import logging

log = logging.getLogger('Device')


class CoiotDevice:
    """
    This object acts in the intersection between the driver object
    (that actually accesses the device), the DB object (acting as a cache)
    and the DBus object (API)
    """
    def __init__(self, db):
        self.db = db

        if not hasattr(self.db, "driver"):
            raise AttributeError("{} has no driver".format(self.db))

        if hasattr(self.db.driver, 'register'):
            self.driver = self.db.driver.register(self)

    def __getattr__(self, k):
        if k[0].islower():
            return super().__getattr__(k)
        return getattr(self.db, k)

    def __setattr__(self, k, v):
        if k[0].islower():
            super().__setattr__(k, v)
            return
        log.info('set {}.{} = {}'.format(self.ID, k, v))
        setattr(self.db, "Future"+k, v)
        setattr(self.driver, k, v)

    def __dir__(self):
        return object.__dir__(self) + [p for p in dir(self.db)
                                       if p[0].isupper()]

    def update(self, k, v):
        log.info('update {}.{} = {}'.format(self.ID, k, v))
        setattr(self.db, k, v)

    @classmethod
    def load(Cls, db):
        valid_devices = []
        for d in db.devices.values():
            try:
                valid_devices.append(CoiotDevice(d))
            except AttributeError as e:
                log.error(e)
        return valid_devices

    def __str__(self):
        return "device {}".format(self.ID)
