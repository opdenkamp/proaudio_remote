from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number import NumberEntity
import logging
from typing import Optional
from .const import *
from homeassistant.helpers.typing import (
    HomeAssistantType,
    ConfigType
)
from homeassistant.const import (
    STATE_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


def setup_proaudio_sensors(hass, add_entities):
    if not hass.data[DOMAIN]['remote'].connected:
        return False
    if hass.data[DOMAIN]['sensors_registered']:
        return True
    ents = []
    for bay in hass.data[DOMAIN]['remote'].outputs:
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "eq1", "100Hz band"))
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "eq2", "330Hz band"))
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "eq3", "1000Hz band"))
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "eq4", "3300Hz band"))
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "eq5", "10000Hz band"))
        ents.append(P8AudioNumber(hass, hass.data[DOMAIN]['remote'], bay, "delay", "audio delay"))
    if len(ents) == 0:
        return False
    add_entities(ents)
    hass.data[DOMAIN]['sensors_registered'] = True
    return True

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    def _late_setup(dev):
        setup_proaudio_sensors(hass, add_entities)

    if discovery_info is None:
        return

    if not setup_proaudio_sensors(hass, add_entities):
        async_dispatcher_connect(hass, SIGNAL_PROAUDIO_CONNECTED, _late_setup)

class P8AudioNumber(NumberEntity):
    def __init__(self, hass, remote, bay, sns_type, friendly_name):
        self.hass = hass
        self._dev = remote
        self._bay = bay
        self._type = sns_type
        self._name = friendly_name
        self._attr_mode = "slider"
        if sns_type[0:2] == 'eq':
            self._attr_native_min_value = -20
            self._attr_native_step = 0.5
            self._attr_native_max_value = 20
            self._attr_native_unit_of_measurement = "dB"
        elif sns_type == 'delay':
            self._attr_native_min_value = 0
            self._attr_native_step = (1.0 / 48.0)
            self._attr_native_max_value = 170.65
            self._attr_native_unit_of_measurement = "ms"

        #self._attr_entity_category = "TODO"
        self._attr_unique_id = "{} {} {} {}".format(DOMAIN, self._dev.serial, repr(self._bay), sns_type)

        async_dispatcher_connect(self.hass, SIGNAL_PROAUDIO_ZONE_UPDATE, self._on_update)

    @property
    def should_poll(self):
        return False

    @property
    def native_value(self) -> float:
        val = None
        if self._type[0:2] == 'eq':
            eqv = self._type[2]
            val = self._bay.get_eq_band(eqv)
        elif self._type == 'delay':
            val = round(float(self._bay.delay) / 48.0, 2)
        else:
            raise Exception("invalid type")
        return val if val is not None else STATE_UNKNOWN

    async def async_set_native_value(self, value: float) -> None:
        if self._type[0:2] == 'eq':
            eqv = self._type[2]
            self._bay.set_eq_band(eqv, value)
            self.async_write_ha_state()
        elif self._type == 'delay':
            self._bay.delay = int((value) * 48)
            self.async_write_ha_state()
        else:
            raise Exception("invalid type")

    def _on_update(self, zone):
        if self._bay == zone:
            self.async_write_ha_state()

    @property
    def available(self):
        return self._dev is not None

    @property
    def name(self):
        return "{} {}".format(repr(self._bay), self._type)

    @property
    def extra_state_attributes(self):
        data = {}
        data['controller'] = self._dev.serial
        data['friendly_name'] = "{} {}".format(repr(self._bay), self._name)
        return data

    @property
    def device_info(self):
        return {
            'identifiers': {
                (NUMBER_DOMAIN, DOMAIN, self._dev.serial, repr(self._bay), self._type)
             },
            'name': self.name,
            'manufacturer': 'Pulse-Eight',
            'via_device': (DOMAIN, self._dev.serial),
        }
