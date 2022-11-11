from typing import AnyStr,\
    List
from logging import getLogger
from os import path
from time import sleep
from traceback import format_exc
from pickle import load,\
    dump

class IO_handler():

    _log: getLogger = None

    def __init__(self,
                 server_used: AnyStr = 'data'):
        if not self._log:
            self._log: getLogger = getLogger()

        self.server_used = server_used
        self.server_used_replaced = server_used.replace(':', '_')

    def save_data(self,
                  object: List) -> None:

        try:
            retry = 0
            while True:
                retry += 1
                if retry == 5:
                    raise Exception('Maximum number of retries reached !')

                try:
                    with open(f'{self.server_used_replaced}.pickle', 'wb') as pickle_out_handle:
                        dump(object,
                             pickle_out_handle)
                    self._log.info(f"Successfully saved {path.abspath(f'{self.server_used_replaced}.pickle')} at retry {retry} !")
                    break
                except:
                    self._log.warning(f"Failed to save {path.abspath(f'{self.server_used_replaced}.pickle')} at retry {retry} !\n{format_exc(chain=False)}")
                    sleep(2)
        except:
            self._log.error(f"Failed to save {path.abspath(f'{self.server_used_replaced}.pickle')} !")

    def load_data(self) -> List:
        if path.isfile(f'{self.server_used_replaced}.pickle'):
            try:
                with open(f'{self.server_used_replaced}.pickle', 'rb') as json_in_handle:
                    return load(json_in_handle)
            except:
                self._log.error(f"Failed to load {path.abspath(f'{self.server_used_replaced}.pickle')} !\n{format_exc(chain=False)}")
                return []
        else:
            self._log.warning(f"{path.abspath(f'{self.server_used_replaced}.pickle')} not found. Bootstrapping a new data dict ...")
            return []