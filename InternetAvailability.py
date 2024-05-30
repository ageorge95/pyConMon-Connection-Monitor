from ag95 import configure_logger
from logging import getLogger
from typing import AnyStr
from socket import gethostbyname,\
    create_connection

machine_and_port_to_ping = r'internetbeacon.msedge.net:80'

class InternetAvailability():
    _log: getLogger = None

    def __init__(self,
                 machine_and_port_to_ping: AnyStr = machine_and_port_to_ping):
        if not self._log:
            self._log: getLogger = getLogger()

        self.machine_and_port_to_ping = machine_and_port_to_ping
        self.machine_to_ping = self.machine_and_port_to_ping.split(':')[0]
        self.port_to_ping = int(self.machine_and_port_to_ping.split(':')[1])

    def check_online_status(self) -> int:
        # first check is that the DNS resolution completes successfully
        try:
            gethostbyname(self.machine_to_ping)
            self._log.info(f'DNS resolution completed successfully for {self.machine_to_ping}')
        except:
            self._log.warning(f'DNS resolution failed for {self.machine_to_ping}')
            return 0

        # then check that an actual connection can be made
        try:
            # a max timeout is hardcoded as 10
            conn = create_connection(address=(self.machine_to_ping, self.port_to_ping),
                                     timeout=1)
            conn.close()
            self._log.info(f'A connection was made successfully to {self.machine_to_ping}:{self.port_to_ping}.')
            return 1
        except:
            self._log.warning(f'Could not connect to {self.machine_to_ping}:{self.port_to_ping} !')
            return 0

# only for testing purposes
if __name__ == '__main__':
    configure_logger()

    test = InternetAvailability()
    test.check_online_status()