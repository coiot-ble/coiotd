import soco
import soco.exceptions
import threading
from coiot.device_action_list import DeviceActionList
from coiot.db import CoiotDBInterface, sqlite_cast
import logging
import time

log = logging.getLogger('SONOS')


class SonosDevice:
    @classmethod
    def load(Cls, self):
        r = self.db.execute("""
            SELECT ID, Zone
            FROM DRIVER_SONOS
            WHERE Device = ?
            """, self.id).fetchone()
        if r is None:
            return False

        self.__id, self.Zone = r
        SonosDevice._SonosDevice__update(self)
        log.info("driver {} loaded for {}".format(Cls.__name__, self))
        return True

    @classmethod
    def install(Cls, self, Zone):
        Zone = sqlite_cast(str, Zone)

        r = self.db.execute("""
            INSERT INTO DRIVER_SONOS(Device, Zone)
            VALUES(?, ?)
            """, self.id, Zone)
        self.__id = r.lastrowid
        self.Zone = Zone
        self.__update()
        log.info("install driver {} for {}".format(Cls.__name__, self))

    def __update(self):
        player = SonosDriver.instance.get_player(self.Zone)
        for f in dir(player):
            if f[0].isupper():
                setattr(self, f, getattr(player, f))

    @classmethod
    def register(Cls):
        CoiotDBInterface.declare(Cls)

    @property
    def driver(self):
        return SonosDriver.instance


class SonosPlayer:
    def __init__(self, driver, soco):
        self.driver = driver
        self.soco = soco

    def update_device(self, Playing=None):
        if Playing is not None:
            self.driver.set_zone_device(self.soco.player_name,
                                        'Playing', Playing)

    @property
    def Playing(self):
        cti = self.soco.get_current_transport_info()
        return cti['current_transport_state'] == 'PLAYING'

    @Playing.setter
    def Playing(self, v):
        if v:
            self.soco.play()
        else:
            self.soco.pause()

    @property
    def Volume(self):
        return self.soco.volume / 100.0

    @Volume.setter
    def Volume(self, v):
        self.soco.volume = round(v * 100)

    @classmethod
    def hms_to_s(Cls, hms):
        if not hms:
            return 0
        hms = hms.split(':')
        return (int(hms[0]) * 60 + int(hms[1])) * 60 + int(hms[2])

    @classmethod
    def s_to_hms(Cls, ts):
        h, m, s = int(ts / 3600), int(ts / 60) % 60, ts % 60
        return '{}:{:02}:{:02}'.format(h, m, s)

    @property
    def SongDuration(self):
        cti = self.soco.get_current_track_info()
        return SonosPlayer.hms_to_s(cti['duration'])

    @property
    def CurrentTime(self):
        cti = self.soco.get_current_track_info()
        return SonosPlayer.hms_to_s(cti['position'])

    @CurrentTime.setter
    def CurrentTime(self, ts):
        self.soco.seek(SonosPlayer.s_to_hms(ts))

    @property
    def CurrentSong(self):
        cti = self.soco.get_current_track_info()

        return cti['uri']

    @CurrentSong.setter
    def CurrentSong(self, v):
        self.soco.clear_queue()
        if v:
            self.soco.add_uri_to_queue(v)
            self.soco.play_from_queue(0)
            self.update_device(Playing=True)

    @property
    def NextSong(self):
        q = self.soco.get_queue(1, 1)

        if not q:
            return ''

        dt = q[0].to_dict()
        return dt['resources'][0]['uri']

    @NextSong.setter
    def NextSong(self, v):
        while self.NextSong:
            self.soco.remove_from_queue(1)
        self.soco.add_uri_to_queue(v)


class SonosDriver:
    instance = None

    class SonosThread(threading.Thread):
        def __init__(self, driver):
            super().__init__()
            self.driver = driver
            self.stopped = False
            self.last_tick = None
            self.refresh = {}

        def stop(self):
            self.stopped = True

        def run(self):
            while not self.stopped:
                tick = time.time()
                if not self.last_tick:
                    self.last_tick = tick

                if tick - self.last_tick > 1:
                    elapsed = int(tick - self.last_tick)
                    self.tick(elapsed)
                    self.last_tick += elapsed

                t = self.driver.action_list.pop()
                if t is not None:
                    try:
                        self.driver.set_soco(*t)
                    except soco.exceptions.SoCoUPnPException as e:
                        log.error(e)
                        d = t[0]
                        d.db._SonosDevice__update()

        def tick(self, elapsed):
            for d in self.driver.devices.values():
                if d.Playing:
                    self.driver.updates.set(d, 'CurrentTime',
                                            d.CurrentTime + elapsed)
                    self.refresh.setdefault(d, 0)
                    self.refresh[d] += elapsed
                    if self.refresh[d] > 10:
                        self.refresh[d] = 0

                        playing = self.driver.get_soco(d, 'Playing')
                        if not playing:
                            log.error("{} stopped playing".format(d))
                            self.driver.set_soco(d, 'Playing', playing)

    def __init__(self, updates):
        SonosDevice.register()
        self.updates = updates
        self.action_list = DeviceActionList()
        self.zones = [SonosPlayer(self, z) for z in soco.discover()]
        self.devices = {}
        self.thread = SonosDriver.SonosThread(self)
        self.thread.start()
        SonosDriver.instance = self

    def set(self, device, k, v):
        self.action_list.set(device, k, v)

    def set_soco(self, device, k, v):
        player = self.get_player(device.Zone)
        setattr(player, k, v)
        self.updates.set(device, k, v)
        log.info("success SONOS \"{}\" {} = {}".format(device.Zone, k, v))

    def get_soco(self, device, k):
        player = self.get_player(device.Zone)
        return getattr(player, k)

    def get_player(self, Zone):
        return next(iter([z for z in self.zones
                          if z.soco.player_name == Zone]))

    def set_zone_device(self, Zone, k, v):
        self.updates.set(self.devices[Zone], k, v)

    def register(self, device, dbd):
        self.devices[device.Zone] = device