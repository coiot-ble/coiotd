import datetime
from datetime import timezone


class CoiotDatetime:
    def __init__(self, dt):
        self.datetime = dt.replace(tzinfo=timezone.utc)
        self.epoch = dt.timestamp()

    @classmethod
    def now(Cls):
        return Cls(datetime.datetime.now())

    @classmethod
    def from_epoch(Cls, epoch):
        dt = datetime.datetime.utcfromtimestamp(epoch)
        return Cls(dt)
