from .const import *
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.const import (
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import (
    HomeAssistantType,
    ConfigType
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

import proaudio_remote as p8
from datetime import *

import logging

_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.DEBUG)

def setup_proaudio(hass, add_entities):
    if not hass.data[DOMAIN]['remote'].connected:
        return False
    if hass.data[DOMAIN]['registered']:
        return True
    ents = []
    for bay in hass.data[DOMAIN]['remote'].outputs:
        ent = ProAudioEntity(hass, hass.data[DOMAIN]['remote'], bay)
        ents.append(ent)
    if len(ents) == 0:
        return False
    add_entities(ents)
    hass.data[DOMAIN]['registered'] = True
    return True

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    def _late_setup(dev):
        setup_proaudio(hass, add_entities)

    if discovery_info is None:
        return

    if not setup_proaudio(hass, add_entities):
        async_dispatcher_connect(hass, SIGNAL_PROAUDIO_CONNECTED, _late_setup)

class ProAudioEntity(MediaPlayerEntity):
    def __init__(self, hass, remote, bay):
        self._remote = remote
        self._bay = bay
        async_dispatcher_connect(hass, SIGNAL_PROAUDIO_CONNECTED, self._on_connect)
        async_dispatcher_connect(hass, SIGNAL_PROAUDIO_DISCONNECTED, self._on_disconnect)
        async_dispatcher_connect(hass, SIGNAL_PROAUDIO_ZONE_UPDATE, self._on_update)

    def _on_update(self, zone):
        if self._bay == zone:
            self.async_write_ha_state()

    def _on_connect(self, remote):
        _LOGGER.debug("connection restored")
        self.async_write_ha_state()

    def _on_disconnect(self, remote):
        _LOGGER.debug("connection lost")
        self.async_write_ha_state()

    @property
    def name(self):
        return repr(self._bay)

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        try:
            if not self.available:
                return STATE_UNAVAILABLE
            muted = self._bay.muted
            if muted is None:
                return STATE_UNKNOWN
            return STATE_OFF if muted else STATE_ON
        except Exception:
            return STATE_UNAVAILABLE

    @property
    def supported_features(self):
        return SUPPORT_BAY_AUDIO_OUTPUT

    def set_volume_level(self, volume):
        if not self.available:
            _LOGGER.warning("failed to update volume setting: not connected")
            return False
        try:
            self._bay.volume = int(volume * 100)
            return True
        except Exception:
            return False

    def volume_up(self):
        if not self.available:
            _LOGGER.warning("failed to update volume setting: not connected")
            return False
        try:
            self._bay.volume = "+"
            return True
        except Exception:
            return False

    def volume_down(self):
        if not self.available:
            _LOGGER.warning("failed to update volume setting: not connected")
            return False
        try:
            self._bay.set_volume("-")
            return True
        except Exception:
            return False

    def mute_volume(self, mute):
        if not self.available:
            _LOGGER.warning("failed to update mute setting: not connected")
            return False
        try:
            self._bay.mute = mute
            return True
        except Exception:
            return False

    def turn_on(self):
        return self.mute_volume(False)

    def turn_off(self):
        return self.mute_volume(True)

    @property
    def source(self):
        if not self.available:
            return STATE_UNAVAILABLE
        src = self._bay.switch
        return repr(src) if src is not None else STATE_UNKNOWN

    @property
    def source_list(self):
        if not self.available:
            return []
        return [repr(bay) for bay in self._bay.sources]

    @property
    def volume_level(self):
        try:
            if not self.available:
                return STATE_UNAVAILABLE
            vol = self._bay.volume
            return vol / 100.0 if vol is not None else STATE_UNKNOWN
        except Exception:
            return STATE_UNAVAILABLE

    @property
    def is_volume_muted(self):
        if not self.available:
            return True
        muted = self._bay.muted
        return muted if muted is not None else STATE_UNKNOWN

    def select_source(self, source, power:bool=True):
        if not self.available:
            _LOGGER.warning("failed to switch to " + str(source) + ": not connected")
            return False
        if power:
            self.mute_volume(False)
        try:
            self._bay.switch = source
            self.async_write_ha_state()
            _LOGGER.warning("switched to " + str(source))
            return True
        except Exception as e:
            _LOGGER.warning("failed to switch to " + str(source) + ": " + str(e))
            return False

    @property
    def unique_id(self):
        return "{} {}".format(self._remote.serial, repr(self._bay))

    @property
    def available(self):
        return (self._bay is not None) and (self._bay.connected)

    @property
    def extra_state_attributes(self):
        data = {}
        data['serial'] = self._remote.serial
        data['model'] = self._remote.model
        data['version'] = self._remote.version
        return data
