import time
import logging
_LOGGER = logging.getLogger(__name__)

class ZoneValue():
    def __init__(self, name, refresh_cmd, refresh_param=None, refresh_time=30):
        self.name = name
        self.cmd = refresh_cmd
        self.cmd_param = refresh_param
        self.timeout = refresh_time
        self.reset()

    def poll(self):
        if self.timeout > 0:
            last_value = self.last_value
            value = self.get()
            return ((last_value is None) and (value is not None)) or ((last_value is not None) and (last_value != value))
        return False

    def reset(self):
        self.last_refresh = None
        self.last_value = None

    def get(self):
        now = time.time()
        if (self.last_refresh is None) or ((now - self.last_refresh) >= self.timeout): 
            self.last_refresh = now
            if self.cmd_param is None:
                self.last_value = self.cmd()
            else:
                self.last_value = self.cmd(self.cmd_param)
        return self.last_value

    def set(self, value):
        self.last_refresh = time.time()
        self.last_value = value

    def __repr__(self):
        return "{}: {}".format(self.name, str(self.last_value))
