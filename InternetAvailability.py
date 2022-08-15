from logging import getLogger
from typing import AnyStr
from subprocess import check_output

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
        test_results = check_output(f'powershell "Test-NetConnection -Port {self.port_to_ping} -ComputerName {self.machine_to_ping}"').decode('utf-8')
        self._log.info(f'Current ping results:\n{test_results.strip()}')
        if 'TcpTestSucceeded : True' in test_results:
            self._log.info(f"According to {self.machine_and_port_to_ping} you are ONline !")
            return 1
        else:
            self._log.warning(f"According to {self.machine_and_port_to_ping} you are OFFline !")
            return 0