import logging
_LOGGER = logging.getLogger(__name__)

class AudioZone():
    """ Audio input or output zone """
    def __init__(self, nb, conn=None):
        self._nb = nb
        self._conn = conn
        self._values = []

    def register_value(self, value):
        self._values.append(value)
        return value

    def poll(self):
        changed = False
        for val in self._values:
            if val.poll():
                changed = True
        return changed

    @property
    def connected(self):
        """ check if the zone can be accessed """
        return self._conn.connected

    @property
    def zone(self):
        """ zone number used by the switch """
        return int(self._nb)

    @property
    def zonefmt(self):
        """ zone number returned by the switch commands (3 digits) """
        return "{0:03d}".format(self.zone)

    @property
    def is_analog(self):
        """ True if this is an analog zone """
        return False

    @property
    def is_digital(self):
        """ True if this is a digital zone """
        return False

    def reset(self):
        for val in self._values:
            val.reset()

    def _on_update(self):
        if self._conn is not None:
            self._conn.on_zone_updated(self)

    def __repr__(self):
        return "unknown zone {}".format(str(self.zone))

    def __str__(self):
        return self.zonefmt

class AudioZoneDisconnected(AudioZone):
    """ Disconnected audio source (no audio routed to the output) """

    def __init__(self, digital):
        super().__init__(0)
        self._digital = digital

    @property
    def is_analog(self):
        """ True if this is an analog input """
        return not self._digital

    @property
    def is_digital(self):
        """ True if this is a digital input """
        return self._digital

    @property
    def gain(self):
        """ Get the current gain setting for this input """
        return 0

    def __repr__(self):
        return "disconnected"

