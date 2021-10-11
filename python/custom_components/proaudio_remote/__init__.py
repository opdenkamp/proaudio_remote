from .const import *
from homeassistant.helpers.typing import (
    HomeAssistantType,
    ConfigType
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
import proaudio_remote as p8

class ProAudioCallbacks(p8.RemoteCallbacks):
    def __init__(self, hass):
        self.hass = hass

    def on_connected(self, remote):
        dispatcher_send(self.hass, SIGNAL_PROAUDIO_CONNECTED, remote)

    def on_connection_lost(self, remote):
        dispatcher_send(self.hass, SIGNAL_PROAUDIO_DISCONNECTED, remote)

    def on_zone_updated(self, zone):
        dispatcher_send(self.hass, SIGNAL_PROAUDIO_ZONE_UPDATE, zone)

async def async_setup(hass: HomeAssistantType, config: ConfigEntry) -> bool:
    hass.data[DOMAIN] = {
            'remote': p8.Remote("proaudio.p8.dmb.opdenkamp.eu", callbacks=ProAudioCallbacks(hass)),
            'registered': False,
            'sensors_registered': False,
    }
    hass.helpers.discovery.load_platform(MEDIA_PLAYER_DOMAIN, DOMAIN, {}, config)
    hass.helpers.discovery.load_platform(NUMBER_DOMAIN, DOMAIN, {}, config)
    return True
