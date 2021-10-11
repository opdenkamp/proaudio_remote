import time
from .zone import *
from .value import *
import logging

_LOGGER = logging.getLogger(__name__)

def _zonefmt(conn, inp, digital, zone):
    if isinstance(zone, AudioZone):
        return zone.zonefmt
    z = conn.get_by_name(inp, digital, zone)
    if z is not None:
        return z.zonefmt
    return str(zone)

class AudioZoneOutput(AudioZone):
    def __init__(self, nb, conn):
        super().__init__(nb, conn)
        self._volume = self.register_value(ZoneValue('volume', self._refresh_volume))
        self._mute = self.register_value(ZoneValue('mute', self._refresh_mute))
        self._bass = self.register_value(ZoneValue('bass', self._refresh_bass, refresh_time=0))
        self._treble = self.register_value(ZoneValue('treble', self._refresh_treble, refresh_time=0))
        self._mirror = self.register_value(ZoneValue('mirror', self._refresh_mirror, refresh_time=0))
        self._delay = self.register_value(ZoneValue('delay', self._refresh_delay, refresh_time=0))
        i = 1
        self._eq = []
        while i < 6:
            self._eq.append(self.register_value(ZoneValue('eq zone ' + str(i), self._refresh_eq, i, refresh_time=0)))
            i = i + 1

    @property
    def volume(self):
        volume = self._volume.get()
        if volume is not None:
            volume = int(volume)
        return volume

    @volume.setter
    def volume(self, volume):
        cmd = "^VPZ @{},{}$".format(self.zonefmt, str(volume))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._volume.set(volume)

    @property
    def muted(self):
        return self._mute.get()

    @muted.setter
    def muted(self, muted):
        cmd = "^VMZ @{},{}$".format(self.zonefmt, "1" if muted else "0")
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._mute.set(muted)

    def toggle_mute(self):
        cmd = "^VMZ @{},+$".format(self.zonefmt)
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._mute.reset()

    @property
    def bass(self):
        return self._bass.get()

    @bass.setter
    def bass(self, bass):
        cmd = "^BAZ @{},{}$".format(self.zonefmt, str(bass))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._bass.set(bass)

    @property
    def treble(self):
        return self._treble.get()

    @treble.setter
    def treble(self, treble):
        cmd = "^TRZ @{},{}$".format(self.zonefmt, str(treble))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._treble.set(treble)

    @property
    def mirror(self):
        return self._mirror.get()

    @mirror.setter
    def mirror(self, mirror):
        cmd = "^LZ @{},{}$".format(self.zonefmt, _zonefmt(self._conn, False, self.is_digital, mirror))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._mirror.set(mirror)

    @property
    def delay(self):
        return int(self._delay.get())

    @delay.setter
    def delay(self, delay):
        cmd = "^LSZ @{},{}$".format(self.zonefmt, str(delay))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._delay.set(delay)

    @property
    def switch(self):
        raise Exception("not implemented")

    @switch.setter
    def switch(self, source):
        raise Exception("not implemented")

    @property
    def switch_delay(self):
        raise Exception("not implemented")

    @switch_delay.setter
    def switch_delay(self, delay):
        raise Exception("not implemented")

    @property
    def eq(self):
        # read all 5 equaliser values of an output and return them as array
        rv = []
        while len(rv) < 5:
            rv.append(self.get_eq_band(len(rv) + 1))
        return rv

    @eq.setter
    def eq(self, values):
        # change all 5 equaliser values of an output
        cnt = 0
        while cnt < 5:
            self.set_eq_band(cnt + 1, values[cnt])
            cnt += 1

    def get_eq_band(self, band):
        val = None
        if (int(band) >= 1 and int(band) <= 5):
            val = self._eq[int(band) - 1].get()
        if val is not None:
            val = (float(val) - 128) * 0.5
        return val

    def set_eq_band(self, band, value):
        # change the equaliser setting of a single band (1-5) of an output
        value = (int(value) * 2) + 128
        data = "^EQ{}Z @{},{}$".format(band, self.zonefmt, value)
        rv = self._conn.send_command(data).zone_resp()
        if rv is not None:
            self._eq[int(band) - 1].set(value)

    def set_eq_flat(self):
        self.eq = [0, 0, 0, 0, 0]

    @property
    def audio_type(self):
        return "unknown"

    def dump(self):
        zi = "Zone {}\n".format(repr(self))
        zi += "switched to: {}\n".format(repr(self.switch))
        zi += "input gain: {}\n".format(str(self.switch.gain))
        zi += "volume: {}\n".format(str(self.volume))
        zi += "muted: {}\n".format(str(self.muted))
        zi += "eq: {}\n".format(str(self.eq))
        zi += "bass: {}\n".format(str(self.bass))
        zi += "treble: {}\n".format(str(self.treble))
        #zi += "type: {}\n".format(str(self.audio_type))
        return zi

    def _refresh_volume(self):
        cmd = "^VPZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    def _refresh_mute(self):
        cmd = "^VMZ @{}?$".format(self.zonefmt)
        return (self._conn.send_command(cmd).zone_resp() == 1)

    def _refresh_bass(self):
        cmd = "^BAZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    def _refresh_treble(self):
        cmd = "^TRZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    def _refresh_mirror(self):
        cmd = "^LZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    def _refresh_delay(self):
        cmd = "^LSZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    def _refresh_eq(self, band):
        # read the equaliser setting of a single band (1-5) of an output
        data = "^EQ{}Z @{}?$".format(band, self.zonefmt)
        return self._conn.send_command(data).zone_resp()

class AudioZoneAnalogOutput(AudioZoneOutput):
    def __init__(self, nb, conn=None):
        super().__init__(nb, conn)
        self._switch = self.register_value(ZoneValue('switch', self._refresh_switch, refresh_time=0))
        self._switch_delay = self.register_value(ZoneValue('switch delay', self._refresh_switch_delay, refresh_time=0))
        self._audio_type = self.register_value(ZoneValue('audio type', self._refresh_audio_type))

    @property
    def is_analog(self):
        return True

    @property
    def audio_type(self):
        return self._audio_type.get()

    def _refresh_audio_type(self):
        cmd = "^ATZ @{}?$".format(self.zonefmt)
        rv = self._conn.send_command(cmd).zone_resp()
        if rv == 1:
            return "no input"
        elif rv == 2:
            return "PCM stereo"
        elif rv == 3:
            return "Encoded SPDIF"
        return "unknown"

    @property
    def switch(self):
        return self._switch.get()

    @switch.setter
    def switch(self, source):
        cmd = "^SZ @{},{}$".format(self.zonefmt, _zonefmt(self._conn, True, self.is_digital, source))
        _LOGGER.warning(">> {}".format(cmd))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._switch.set(source)

    @property
    def switch_delay(self):
        return self._switch_delay.get()

    @switch_delay.setter
    def switch_delay(self, delay):
        cmd = "^DZ @{},{}$".format(self.zonefmt, str(delay))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._switch_delay.set(delay)

    def _refresh_switch_delay(self):
        cmd = "^DZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    @property
    def sources(self):
        return self._conn.inputs

    def _refresh_switch(self):
        cmd = "^SZ @{}?$".format(self.zonefmt)
        return self._conn.get_by_id(True, False, self._conn.send_command(cmd).zone_resp())

    def __repr__(self):
        return "analog output {}".format(str(self._nb))

class AudioZoneDigitalOutput(AudioZoneOutput):
    def __init__(self, nb, conn=None):
        super().__init__(nb, conn)
        self._switch = self.register_value(ZoneValue('switch', self._refresh_switch, refresh_time=0))
        self._switch_delay = self.register_value(ZoneValue('switch delay', self._refresh_switch_delay, refresh_time=0))

    @property
    def is_digital(self):
        return True

    @property
    def switch(self):
        return self._switch.get()

    @switch.setter
    def switch(self, source):
        cmd = "^DSZ @{},{}$".format(self.zonefmt, _zonefmt(self._conn, True, self.is_digital, source))
        _LOGGER.info("set_switch({}) = {}".format(source, cmd))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._switch.set(source)

    @property
    def switch_delay(self):
        return self._switch_delay.get()

    @switch_delay.setter
    def switch_delay(self, delay):
        cmd = "^DDZ @{},{}$".format(self.zonefmt, str(delay))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._switch_delay.set(delay)

    def _refresh_switch(self):
        cmd = "^DSZ @{}?$".format(self.zonefmt)
        return self._conn.get_by_id(True, True, self._conn.send_command(cmd).zone_resp())

    def _refresh_switch_delay(self):
        cmd = "^DDZ @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

    @property
    def sources(self):
        return self._conn.inputs_digital

    def __repr__(self):
        return "digital output {}".format(str(self._nb))

