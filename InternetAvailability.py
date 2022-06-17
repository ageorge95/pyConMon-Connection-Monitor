from logging import getLogger
from subprocess import check_call, DEVNULL
from typing import AnyStr

# NOTE: google-public-dns-a.google.com is google's public DNS: 8.8.8.8
# NOTE: 8.8.8.8 may be blocked by your company's fire3wall or by your ISP, in this case find out the DNS server by using echo | nslookup | findstr "Default\ Server"
trusted_website_to_ping_config = r'8.8.8.8'

class InternetAvailability():
    _log: getLogger = None

    def __init__(self,
                 trusted_website_to_ping: AnyStr = trusted_website_to_ping_config):
        if not self._log:
            self._log: getLogger = getLogger()

        self.trusted_website_to_ping = trusted_website_to_ping

    def check_online_status(self) -> int:
        try:
            check_call(f"ping {self.trusted_website_to_ping} -n 1",
                      stdout=DEVNULL)
            self._log.info(f"According to {self.trusted_website_to_ping} you are ONline !")
            return 1
        except:
            self._log.warning(f"According to {self.trusted_website_to_ping} you are OFFline !")
            return 0