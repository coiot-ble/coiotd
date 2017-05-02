import threading

def load_coiot_devices(db, drivers):
    """
    Initialize devices

    First look into database to get all saved devices, then connect each one to the right
    driver; finally return them for the caller to create the DBus interfaces
    """
    db_devices = db.devices
    devices = []
    for drivername in db_devices:
        assert(drivername in drivers)

        for db_device in db_devices[drivername]:
            device = CoiotDevice(db_device)
            drivers[drivername].connect(device)
            devices.append(device)

    return devices

class CoiotDevice:
    """
    This object acts in the intersection between the driver object (that actually
    access the device), the DB object (acting as a cache) and the DBus object (API)
    """
    def __init__(self, db):
        self.__dict__['db'] = db

    def __getattr__(self, k):
        return getattr(self.db, k)

    def __setattr__(self, k, v):
        if k == "action_list":
            self.__dict__[k] = v
            return
        setattr(self.db, "Future"+k, v)
        self.action_list[k] = v

    def update(self, k, v):
        setattr(self.db, k, v)
