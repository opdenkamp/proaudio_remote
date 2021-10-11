import logging
import time
_LOGGER = logging.getLogger(__name__)

class CommandResponse():
    def __init__(self, cmd, resp):
        self._cmd = cmd
        if resp is not None:
            resp = resp.decode().split("\r\n")
            if resp[0] != '^+$':
                # not a response header
                raise Exception("command failed: " +str(cmd) + " = " + resp[0])
            self._resp = resp[1]
        else:
            self._resp = None

    def zone_resp(self):
        if self._resp is None:
            return None
        exp = self._expected_response_start()
        resp = str(self)
        l = len(exp)+1
        if resp[1:l] != exp:
            raise Exception("invalid response {} to command {} (3) = {} != {}".format(self._resp, self._cmd, resp[1:l], exp))
        return resp[l+1:]

    def _expected_response_start(self):
        cmd_split = self._cmd[1:-1].split("?")
        return "={}".format(cmd_split[0])

    def __str__(self):
        if self._resp is None:
            return None
        if self._resp[0] != '^':
            raise Exception("invalid response {} to command {} (1) = {}".format(self._resp, self._cmd, self._resp[1]))
        if self._resp[-1] != '$':
            raise Exception("invalid response {} to command {} (2)".format(self._resp, self._cmd))
        return self._resp[:-1]

