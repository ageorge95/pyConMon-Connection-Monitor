from json import load,\
    dump
from typing import Dict
from logging import getLogger
from os import path
from time import sleep
from traceback import format_exc
from datetime import datetime
from InternetAvailability import InternetAvailability

class IO_handler():

    _log: getLogger = None

    def __init__(self):
        if not self._log:
            self._log: getLogger = getLogger()

    def save_data(self,
                  object: Dict) -> None:
        try:
            retry = 0
            while True:
                retry += 1
                if retry == 5:
                    raise Exception('Maximum number of retries reached !')

                try:
                    with open('data.json', 'w') as json_out_handle:
                        dump(object,
                             json_out_handle,
                             indent=2)
                    self._log.info(f"Successfully saved {path.abspath('data.json')} at retry {retry} !")
                except:
                    self._log.warning(f"Failed to save {path.abspath('data.json')} at retry {retry} !\n{format_exc(chain=False)}")
                    sleep(2)
        except:
            self._log.error(f"Failed to save {path.abspath('data.json')} !")

    def load_data(self) -> Dict:
        if path.isfile('data.json'):
            try:
                with open('data.json', 'r') as json_in_handle:
                    return load(json_in_handle)
            except:
                self._log.error(f"Failed to load {path.abspath('data.json')} !\n{format_exc(chain=False)}")
        else:
            self._log.warning(f"{path.abspath('data.json')} not found. Bootstrapping a new data dict ...")
            return {datetime.now(): InternetAvailability().check_online_status()}