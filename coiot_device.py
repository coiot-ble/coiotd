class CoiotDevice:
    """
    This object acts in the intersection between the driver object
    (that actually accesses the device), the DB object (acting as a cache)
    and the DBus object (API)
    """
    def __init__(self, db, notify_update):
        self._db = db
        self._action_lists_set = []
        self._action_list_update = {}
        self._notify_update = notify_update
        if hasattr(self._db, 'driver'):
            self._db.driver.connect(self)

    def __getattr__(self, k):
        if k.startswith('_'):
            return super().__getattr__(k)
        return getattr(self._db, k)

    def __setattr__(self, k, v):
        if k.startswith('_'):
            super().__setattr__(k, v)
            return
        setattr(self._db, "Future"+k, v)
        for al in self._action_lists_set:
            al[k] = v

    def update(self):
        while self._action_list_update:
            k, v = self._action_list_update.popitem()
            setattr(self._db, k, v)

    def queue_update(self, k, v):
        self._action_list_update[k] = v
        self._notify_update(self)

    def add_action_list(self, al):
        self._action_lists_set.append(al)

    @classmethod
    def load(Cls, db, notify_update):
        return [CoiotDevice(d, notify_update) for d in db.devices]
