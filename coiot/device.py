import logging

log = logging.getLogger('Device')


class CoiotDevice:
    """
    This object acts in the intersection between the driver object
    (that actually accesses the device), the DB object (acting as a cache)
    and the DBus object (API)
    """
    def __init__(self, db, notify_update):
        self.db = db
        self.action_lists_set = []
        self.action_list_update = {}
        self.notify_update = notify_update
        if hasattr(self.db, 'driver'):
            self.db.driver.connect(self)

    def __getattr__(self, k):
        if k[0].islower():
            return super().__getattr__(k)
        return getattr(self.db, k)

    def __setattr__(self, k, v):
        if k[0].islower():
            super().__setattr__(k, v)
            return
        log.info('set {} {} = {}'.format(self, k, v))
        setattr(self.db, "Future"+k, v)
        for al in self.action_lists_set:
            al[k] = v

    def __dir__(self):
        return object.__dir__(self) + [p for p in dir(self.db)
                                       if p[0].isupper()]

    def update(self):
        while self.action_list_update:
            k, v = self.action_list_update.popitem()
            log.info('update {} {} = {}'.format(self, k, v))
            setattr(self.db, k, v)

    def queue_update(self, k, v):
        self.action_list_update[k] = v
        self.notify_update(self)
        log.info("waiting for update to {} {} = {}".format(self, k, v))

    def add_action_list(self, al):
        log.info('add action list {}'.format(self))
        self.action_lists_set.append(al)

    @classmethod
    def load(Cls, db, notify_update):
        return [CoiotDevice(d, notify_update) for d in db.devices]

    def __str__(self):
        return "{}({}, driver={})".format(type(self).__name__, self.db,
                                          self.db.driver)
