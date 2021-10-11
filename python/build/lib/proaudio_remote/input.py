from .zone import *
from .value import *
import logging

_LOGGER = logging.getLogger(__name__)

class AudioZoneInput(AudioZone):
    """ Audio input zone """

    def __init__(self, nb, conn):
        super().__init__(nb, conn)
        self._gain = self.register_value(ZoneValue('gain', self._refresh_gain, refresh_time=0))
        self._delay = self.register_value(ZoneValue('delay', self._refresh_delay, refresh_time=0))

    @property
    def delay(self):
        return self._delay.get()

    @delay.setter
    def delay(self, delay):
        cmd = "^LSI @{},{}$".format(self.zonefmt, str(delay))
        rv = self._conn.send_command(cmd)
        if rv is not None:
            self._delay.set(delay)

    @property
    def gain(self):
        return self._gain.get()

    @gain.setter
    def gain(self, gain):
        data = "^GAI @{},{}$".format(str(self), str(gain))
        rv = self._conn.send_command(data).zone_resp()
        if rv is not None:
            self._gain.set(gain)

    def _refresh_gain(self):
        data = "^GAI @{}?$".format(str(self))
        return self._conn.send_command(data).zone_resp()

    def _refresh_delay(self):
        cmd = "^LSI @{}?$".format(self.zonefmt)
        return self._conn.send_command(cmd).zone_resp()

class AudioZoneAnalogIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # Analog audio input, 1 based
        super().__init__(nb, conn)

    @property
    def is_analog(self):
        return True

    def __repr__(self):
        return "analog input {}".format(str(self._nb))

class AudioZoneAnalogCoaxIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # PCM from coax input, 1 based
        # only PCM can be converted to analog
        super().__init__(nb + 32, conn)

    @property
    def is_analog(self):
        return True

    def __repr__(self):
        return "PCM coax input {}".format(str(self._nb - 32))

class AudioZoneAnalogOpticalIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # PCM from optical input, 1 based
        # only PCM can be converted to analog
        super().__init__(nb + 64, conn)

    @property
    def is_analog(self):
        return True

    def __repr__(self):
        return "PCM optical input {}".format(str(self._nb - 64))

class AudioZoneDigitalCoaxIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # PCM, Dolby or DTS from coax input, 1 based
        super().__init__(nb + 32, conn)

    @property
    def is_digital(self):
        return True

    def __repr__(self):
        return "digital coax input {}".format(str(self._nb - 32))

class AudioZoneDigitalOpticalIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # PCM, Dolby or DTS from optical input, 1 based
        super().__init__(nb + 64, conn)

    @property
    def is_digital(self):
        return True

    def __repr__(self):
        return "digital optical input {}".format(str(self._nb - 64))

class AudioZoneDigitalAnalogMirrorIn(AudioZoneInput):
    def __init__(self, nb, conn=None):
        # PCM input that mirrors analog outputs on the same card, 1 based
        # only PCM can be converted to analog
        super().__init__(nb + 128, conn)

    @property
    def is_analog(self):
        return True

    def __repr__(self):
        return "PCM mirror input {}".format(str(self._nb - 128))

