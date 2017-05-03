class CoiotDevice:
    """
    This object acts in the intersection between the driver object
    (that actually accesses the device), the DB object (acting as a cache)
    and the DBus object (API)
    """
    def __init__(self, db):
        self._db = db
        self._action_lists = []

    def __getattr__(self, k):
        if k.startswith('_'):
            return super().__getattr__(k)
        return getattr(self._db, k)

    def __setattr__(self, k, v):
        if k.startswith('_'):
            super().__setattr__(k, v)
            return
        setattr(self._db, "Future"+k, v)
        for al in self._action_lists:
            al[k] = v

    def update(self, k, v):
        setattr(self._db, k, v)

    def add_action_list(self, al):
        self._action_lists.append(al)

    @classmethod
    def load(Cls, db):
        return [CoiotDevice(d) for d in db.devices]
