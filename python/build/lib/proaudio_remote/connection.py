import logging
import socket
import _thread as thread
import threading
import time
from .response import *

_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.DEBUG)

class ConnectionCallback():
    def on_connected(self):
        pass

    def on_connection_lost(self):
        pass

    def on_update(self, data):
        pass

    def poll(self):
        pass

class Connection():
    def __init__(self, callback:ConnectionCallback, target_ip:str):
        self._target_ip = target_ip
        self._callback = callback
        self._socket = None
        self._last_connect = 0
        self._stop = False
        self._lock = threading.RLock()
        thread.start_new_thread(self._run, ())

    @property
    def target_ip(self):
        return self._target_ip

    @property
    def connected(self):
        with self._lock:
            return (self._socket is not None)

    def close(self):
        self._stop = True
        with self._lock:
            if self._socket is not None:
                self._socket.close()
                self._socket = None

    def send_command(self, cmd):
        rv = None
        with self._lock:
            con = self.connection()
            if con is None:
                raise Exception('not connected')
            try:
                _LOGGER.debug('tx: ' + str(cmd))
                con.sendall(cmd.encode())
                return self._read_response(cmd)
            except Exception as e:
                if self._socket is not None:
                    self._socket.close()
                    self._socket = None
                    self._callback.on_connection_lost()
                raise e

    def _read_response(self, cmd):
        cnt = 0
        while cnt < 5:
            cnt = cnt + 1
            resp_data = self._socket.recv(1024)
            if resp_data is None:
                raise Exception('command timed out')
            _LOGGER.debug('rx: ' + str(resp_data))
            try:
                return CommandResponse(cmd, resp_data)
            except Exception as e:
                # process update
                self._callback.on_update(resp_data)
        return None

    def connection(self):
        connected = False
        now = time.time()
        if (self._socket is None) and ((now - self._last_connect) >= 10):
            self._last_connect = now
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(1)
                self._socket.connect((self._target_ip, 50005))
                connected = True
                _LOGGER.debug("connected to " + str(self._target_ip))
            except Exception as e:
                self._socket = None
                _LOGGER.debug("failed to connect to " + str(self._target_ip) + ": "+ str(e))

        if connected:
            try:
                if not self._callback.on_connected():
                    self._socket = None
            except Exception as e:
                _LOGGER.debug("callback failed: " + str(e))
                if self._socket is not None:
                    self._socket.close()
                    self._socket = None
                    self._callback.on_connection_lost()
                    raise e
        return self._socket

    def _run(self):
        _LOGGER.debug("connection thread running")
        while not self._stop:
            try:
                if self.connection() is not None:
                    self._callback.poll()
            except Exception:
                if self._socket is not None:
                    self._socket.close()
                    self._socket = None
                    self._callback.on_connection_lost()
            time.sleep(1)
