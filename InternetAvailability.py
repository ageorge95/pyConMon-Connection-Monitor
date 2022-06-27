from logging import getLogger
from subprocess import check_call, DEVNULL
from typing import AnyStr
import socket

machine_and_port_to_ping = r'google.com:80'

class InternetAvailability():
    _log: getLogger = None

    def __init__(self,
                 machine_and_port_to_ping: AnyStr = machine_and_port_to_ping):
        if not self._log:
            self._log: getLogger = getLogger()

        self.machine_and_port_to_ping = machine_and_port_to_ping

    def check_online_status(self) -> int:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 Second Timeout
            error = sock.connect_ex(('google.com', 80))
            if not error:
                self._log.info(f"According to {self.machine_and_port_to_ping} you are ONline !")
                return 1
            else:
                self._log.warning(f"According to {self.machine_and_port_to_ping} you are OFFline !")
                return 0
        # an exception might happen if an address is provided which cannot be resolved by the DNS
        except:
            self._log.warning(f"According to {self.machine_and_port_to_ping} you are OFFline !")
            return 0