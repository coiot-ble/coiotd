import soco
import soco.exceptions
import threading
from coiot.device_action_list import DeviceActionList, DALDevice
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

    @classmethod
    def init_interface(Cls, self):
        self.playing = False
        if not SonosDriver.instance:
            return
        try:
            player = SonosDriver.instance.devices[self.Zone]
            self.Online = True
            for f in dir(player):
                if f[0].isupper():
                    setattr(self, f, getattr(player, f))
        except StopIteration:
            self.Online = False

    @classmethod
    def register(Cls):
        CoiotDBInterface.declare(Cls)

    @classmethod
    def autodetect(self):
        return list((z
                     for z, p in SonosDriver.instance.devices.items()
                     if not p.cache))

    @property
    def driver(self):
        return SonosDriver.instance

    def refresh_CurrentTime(self):
        ct = time.time()
        if self.Playing:
            self.current_time += ct - self.refresh_time
        self.refresh_time = ct

    @property
    def CurrentTime(self):
        self.refresh_CurrentTime()
        return int(self.current_time)

    @CurrentTime.setter
    def CurrentTime(self, v):
        self.current_time = v
        self.refresh_time = time.time()

    @property
    def Playing(self):
        return self.playing

    @Playing.setter
    def Playing(self, v):
        self.refresh_CurrentTime()
        self.playing = v


class SonosPlayer:
    def __init__(self, driver, phy):
        self.driver = driver
        self.phy = phy
        self.zone = self.phy.player_name
        self.cache = None

    def safe_transport_info(self):
        try:
            return self.phy.get_current_transport_info()
        except ConnectionError as e:
            log.error(e)
            self.cache.Online = False
            return {'current_transport_state': 'STOPPED'}

    def safe_track_info(self):
        try:
            return self.phy.get_current_track_info()
        except ConnectionError as e:
            log.error(e)
            self.cache.Online = False
            return {'duration': 0, 'position': 0, 'uri': ''}

    @property
    def Playing(self):
        cti = self.safe_transport_info()
        return cti['current_transport_state'] == 'PLAYING'

    @Playing.setter
    def Playing(self, v):
        if v:
            self.phy.play()
        else:
            self.phy.pause()

    @property
    def Volume(self):
        return self.phy.volume / 100.0

    @Volume.setter
    def Volume(self, v):
        self.phy.volume = round(v * 100)

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
        cti = self.safe_track_info()
        return SonosPlayer.hms_to_s(cti['duration'])

    @property
    def CurrentTime(self):
        cti = self.safe_track_info()
        return SonosPlayer.hms_to_s(cti['position'])

    @CurrentTime.setter
    def CurrentTime(self, ts):
        self.phy.seek(SonosPlayer.s_to_hms(ts))

    @property
    def CurrentSong(self):
        cti = self.safe_track_info()

        return cti['uri']

    @CurrentSong.setter
    def CurrentSong(self, v):
        self.phy.clear_queue()
        if v:
            self.phy.add_uri_to_queue(v)
            self.phy.play_from_queue(0)
            self.cache.Playing = False

    @property
    def NextSong(self):
        q = self.phy.get_queue(1, 1)

        if not q:
            return ''

        dt = q[0].to_dict()
        return dt['resources'][0]['uri']

    @NextSong.setter
    def NextSong(self, v):
        while self.NextSong:
            self.phy.remove_from_queue(1)
        self.phy.add_uri_to_queue(v)


class SonosDriver(threading.Thread):
    instance = None

    def __init__(self, cache_update):
        super().__init__()
        self.cache_update = cache_update
        self.player_update = DeviceActionList()
        self.devices = {phy.player_name: SonosPlayer(self, phy)
                        for phy in soco.discover()}
        self.stopped = False
        self.last_tick = None
        self.refresh = {}
        SonosDriver.instance = self
        SonosDevice.register()
        self.start()

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

            t = self.player_update.pop()
            if t is not None:
                d, k, v = t
                try:
                    player = self.devices[d.Zone]
                    setattr(player, k, v)
                    setattr(player.cache, k, v)
                    log.info("update \"{}\" {} = {}".format(d.Zone, k, v))
                except soco.exceptions.SoCoUPnPException as e:
                    log.error(e)

    def tick(self, elapsed):
        for player in self.devices.values():
            self.refresh.setdefault(player, 0)
            self.refresh[player] += elapsed

            if self.refresh[player] > 3:
                self.refresh[player] = 0
                player.cache.Playing = player.Playing

    def register(self, cache):
        self.devices[cache.Zone].cache = DALDevice(cache, self.cache_update)
        return DALDevice(cache, self.player_update)
