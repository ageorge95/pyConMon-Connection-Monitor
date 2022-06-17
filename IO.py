from json import load,\
    dump
from typing import Dict,\
    AnyStr
from logging import getLogger
from os import path
from time import sleep
from traceback import format_exc
from datetime import datetime
from InternetAvailability import InternetAvailability

class IO_handler():

    _log: getLogger = None

    def __init__(self,
                 server_used: AnyStr = 'data'):
        if not self._log:
            self._log: getLogger = getLogger()

        self.server_used = server_used

    def save_data(self,
                  object: Dict) -> None:
        try:
            retry = 0
            while True:
                retry += 1
                if retry == 5:
                    raise Exception('Maximum number of retries reached !')

                try:
                    with open(f'{self.server_used}.json', 'w') as json_out_handle:
                        dump(object,
                             json_out_handle,
                             indent=2)
                    self._log.info(f"Successfully saved {path.abspath(f'{self.server_used}.json')} at retry {retry} !")
                except:
                    self._log.warning(f"Failed to save {path.abspath(f'{self.server_used}.json')} at retry {retry} !\n{format_exc(chain=False)}")
                    sleep(2)
        except:
            self._log.error(f"Failed to save {path.abspath(f'{self.server_used}.json')} !")

    def load_data(self) -> Dict:
        if path.isfile(f'{self.server_used}.json'):
            try:
                with open(f'{self.server_used}.json', 'r') as json_in_handle:
                    return load(json_in_handle)
            except:
                self._log.error(f"Failed to load {path.abspath(f'{self.server_used}.json')} !\n{format_exc(chain=False)}")
        else:
            self._log.warning(f"{path.abspath(f'{self.server_used}.json')} not found. Bootstrapping a new data dict ...")
            return {datetime.now(): InternetAvailability().check_online_status()}