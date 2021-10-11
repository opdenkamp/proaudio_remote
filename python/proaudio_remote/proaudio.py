#!/usr/bin/python3

import os
import logging
from typing import Tuple

from .zone import *
from .input import *
from .output import *
from .connection import *

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

class RemoteCallbacks():
    def on_connected(self, remote):
        _LOGGER.info("connected to: " + str(remote.target_ip))

    def on_connection_lost(self, remote):
        _LOGGER.info("connection to " + str(remote.target_ip) + " lost")

    def on_zone_updated(self, remote, zone):
        _LOGGER.info("zone updated: " + str(zone))

class Remote(ConnectionCallback):
    ''' Main component that handles the network connections and registration of remote devices '''
    def __init__(self, target_ip:str, model:str=None, callbacks:RemoteCallbacks=None):
        self._model_version = None
        self._model = model
        self.inputs_analog = []
        self.inputs_digital = []
        self.inputs = []
        self.outputs_analog = []
        self.outputs_digital = []
        self.outputs = []
        self._ports_created = False
        self._callbacks = callbacks
        self._conn = Connection(self, target_ip)

    def close(self):
        self._conn.close()

    @property
    def target_ip(self):
        return self._conn.target_ip

    def _set_extio(self):
        return self.send_command("^XS +32768$")

    def _read_model_version(self):
        ver = str(self.send_command("^V ?$")).split(",")
        model = ver[0].split('"')
        self._model_version = [model[1], ver[1], ver[2]]

    def on_connected(self):
        _LOGGER.debug("connected to {}".format(self.target_ip))
        self._set_extio()
        self._read_model_version()
        self._create_ports()

        if self._callbacks is not None:
            try:
                self._callbacks.on_connected(self)
            except Exception as cbx:
                _LOGGER.error("callback failed: " + str(cbx))
        return True

    def on_connection_lost(self):
        for bay in self.inputs:
            bay.reset()
        for bay in self.outputs:
            bay.reset()
        
        if self._callbacks is not None:
            try:
                self._callbacks.on_connection_lost(self)
            except Exception as cbx:
                _LOGGER.error("callback failed: " + str(cbx))

    @property
    def connected(self):
        return self._conn.connected

    def send_command(self, cmd):
        return self._conn.send_command(cmd)

    def get_by_id(self, inp, digital, nb):
        v = self.inputs if inp else self.outputs
        for bay in v:
            if bay.zone == int(nb):
                return bay
        return "(unknown zone {})".format(nb)

    def get_by_name(self, inp, digital, nb):
        nb = str(nb).replace("'", "")
        v = self.inputs if inp else self.outputs
        for bay in v:
            if repr(bay) == str(nb):
                return bay
        return None

    def _create_ports(self):
        if self._ports_created:
            return
        self._ports_created = True
        ptr = 0
        while ptr < self.nb_outputs_analog:
            ptr += 1
            o = AudioZoneAnalogOutput(ptr, self)
            self.outputs_analog.append(o)
            self.outputs.append(o)
        ptr = 0
        while ptr < self.nb_outputs_digital:
            ptr += 1
            o = AudioZoneDigitalOutput(ptr, self)
            self.outputs_digital.append(o)
            self.outputs.append(o)
        ptr = 0
        while ptr < self.nb_inputs_analog:
            ptr += 1
            o = AudioZoneAnalogIn(ptr, self)
            self.inputs_analog.append(o)
            self.inputs.append(o)
        self.inputs_analog.append(AudioZoneDisconnected(False))
        ptr = 0
        while ptr < self.nb_inputs_coax:
            ptr += 1
            o = AudioZoneAnalogCoaxIn(ptr, self)
            self.inputs_digital.append(o)
            self.inputs.append(o)
        ptr = 0
        while ptr < self.nb_inputs_optical:
            ptr += 1
            o = AudioZoneAnalogOpticalIn(ptr, self)
            self.inputs_digital.append(o)
            self.inputs.append(o)
        ptr = 0
        while ptr < self.nb_outputs_analog:
            ptr += 1
            o = AudioZoneDigitalAnalogMirrorIn(ptr, self)
            self.inputs_digital.append(o)
            self.inputs.append(o)
        self.inputs_digital.append(AudioZoneDisconnected(True))
        self.inputs.append(AudioZoneDisconnected(True))

    def get_power(self):
        return str(self.send_command("^P ?$")[4:5]) == '1'

    def set_power(self, pwr):
        if self.get_power() != pwr:
            _LOGGER.info("Powering {}".format("on" if pwr else "off"))
        cmd = "^P {}$".format("1" if pwr else "0")
        return self.send_command(cmd)

    def get_version_info(self):
        if self._version is None:
            try:
                ver = str(self.send_command("^V ?$", is_init_cmd=True)).split(",")
                model = ver[0].split('"')
                self._version = [model[1], ver[1], ver[2]]
            except Exception:
                pass
        return self._version

    @property
    def nb_ports(self):
        if self.model == "ProAudio8":
            return 8
        elif self.model == "ProAudio16":
            return 16
        elif self.model == "ProAudio32":
            return 32
        elif self.model == "ProAudio64":
            return 64
        return 0

    @property
    def nb_inputs_analog(self):
        return self.nb_ports

    @property
    def nb_inputs_optical(self):
        return 8

    @property
    def nb_inputs_coax(self):
        return self.nb_ports

    @property
    def nb_outputs_digital(self):
        return self.nb_ports

    @property
    def nb_outputs_analog(self):
        return self.nb_ports

    @property
    def model(self):
        if self._model is not None:
            return str(self._model)
        return self._model_version[0] if self._model_version is not None else None

    @property
    def version(self):
        return self._model_version[1] if self._model_version is not None else None

    @property
    def serial(self):
        return self._model_version[2] if self._model_version is not None else None

    def on_zone_updated(self, zone):
        if self._callbacks is not None:
            try:
                self._callbacks.on_zone_updated(zone)
            except Exception as cbx:
                _LOGGER.error("callback failed: " + str(cbx))

    def poll(self):
        for bay in self.inputs:
            if bay.poll():
                self.on_zone_updated(bay)
        for bay in self.outputs:
            if bay.poll():
                self.on_zone_updated(bay)

    def __str__(self):
        return "model:{} version:{} serial:{}".format(self.model, self.version, self.serial)

