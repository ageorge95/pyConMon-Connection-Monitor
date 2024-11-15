import sys
sys.path.insert(0, 'CustomTkinter')

from ag95 import configure_logger
from IO import IO_handler
from InternetAvailability import InternetAvailability,\
    machine_and_port_to_ping
from customtkinter import CTk, CTkButton, CTkLabel, CTkComboBox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
    NavigationToolbar2Tk
import matplotlib.dates as md
import matplotlib.pyplot as plt
from time import sleep
from threading import Thread
from logging import getLogger
from datetime import datetime,\
    timedelta
from argparse import ArgumentParser

# Optional CLI interface
parser = ArgumentParser(description='Optional CLI interface for the connectivity monitor.')

parser.add_argument('-a',
                    '--address',
                    type=str,
                    help='The address to be used for the connectivity check; Must be like "machine_name:port"',
                    default=machine_and_port_to_ping)

parser.add_argument('-t',
                    '--title',
                    type=str,
                    help='Additional string to append to the window title.',
                    default='')

args = parser.parse_args()
address_to_be_used = args.address
title = args.title


class handle_exit():
    def __init__(self):
        self.to_exit = False

    def exit(self):
        print('Exit command received.')
        self.to_exit = True

class App(IO_handler):
    def __init__(self,
                 root):

        self.root = root

        self._log = getLogger()
        super(App, self).__init__(server_used=address_to_be_used)

        self.stop_updating = False

        self.data = self.load_data()

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1, 1, 1)

        xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
        self.ax1.xaxis.set_major_formatter(xfmt)
        self.ax1.tick_params(axis='x',
                             labelrotation=45)

        self.axvspans = []
        for pair in self.data:
            if type(self.data[0]) == type(list()):
                self.axvspans.append(self.ax1.axvspan(pair[0]['date'],
                                                      pair[1]['date'],
                                                      color = 'green' if pair[1]['status'] else 'red'))

        self.fig.tight_layout()

        self.label_server_used = CTkLabel(master=root,
                                          text=f"Using {address_to_be_used} to check the connectivity.")
        self.label_server_used.pack()

        self.label_current_status = CTkLabel(master=root,
                                             text="Current status is INITIALIZED",
                                             text_color='orange')
        self.label_current_status.pack()

        self.canvas = FigureCanvasTkAgg(self.fig,
                                        master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)


        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()
        self.toolbar.pack(side='left')

        self.button_stop_resume = CTkButton(master=root,
                                            text='STOP/ RESUME',
                                            command=self.stop_resume_action)
        self.button_stop_resume.pack(side='right')

        self.input_combobox_cycle_time = CTkComboBox(master=root,
                                                     values=['Cycle 10 sec',
                                                             'Cycle 30 sec',
                                                             'Cycle 1*60 sec',
                                                             'Cycle 2*60 sec',
                                                             'Cycle 3*60 sec',
                                                             'Cycle 4*60 sec',
                                                             'Cycle 5*60 sec'])
        self.input_combobox_cycle_time.pack(side='right')
        self.seconds_combobox_cycle_time = lambda : int(eval(self.input_combobox_cycle_time.get().split(' ')[1]))

        self.input_combobox_max_history_h = CTkComboBox(master=root,
                                                        values = ['History 1*24 h',
                                                                  'History 2*24 h',
                                                                  'History 3*24 h',
                                                                  'History 4*24 h',
                                                                  'History 5*24 h',
                                                                  'History 6*24 h',
                                                                  'History 7*24 h'])
        self.seconds_combobox_max_history_s = lambda: 60*60*int(eval(self.input_combobox_max_history_h.get().split(' ')[1]))
        self.input_combobox_max_history_h.pack(side='right')

    def stop_resume_action(self):
        # flip the bool value
        self.stop_updating = not self.stop_updating

        # update the status label
        self.label_current_status.configure(require_redraw=True,
                                            **{'text': f"Current status is {'PAUSED' if self.stop_updating else 'RESUMED'}",
                                               'text_color': 'orange'})
        self._log.info('STOP command received.')

class Interaction_Handler():
    def __init__(self,
                 app_obj: App,
                 to_exit: handle_exit = False):

        self.to_exit = to_exit
        self.app_obj = app_obj

        self.InternetAvailability_obj = InternetAvailability(machine_and_port_to_ping=address_to_be_used)
        self.IO_orchestrator = IO_handler(server_used=address_to_be_used)

        self.max_history_s = self.app_obj.input_combobox_max_history_h._values[-1]
        self.max_history_s = 60 * 60 * int(eval(self.max_history_s.split(' ')[1]))

    def decimate_data(self):
        # NOTE: app_obj.data is al ist of lists or dicts
        # each sublist contains two dicts [from_timestamp_data, to_timestamp_data]

        # ONLY decimate the data if app_obj.data has data in it
        if len(self.app_obj.data) > 0:
            # if the first element is a dict, meaning that this is the first time the tool was launched
            # then overwrite the first entry with a bootstrapped list
            if isinstance(self.app_obj.data[0], dict):
                to_overwrite = [self.app_obj.data[0],
                                self.app_obj.data[0]]
                self.app_obj.data[0] = to_overwrite

            # remove entries that are too old
            oldest_date_allowed = datetime.now() - timedelta(seconds=self.max_history_s)
            new_data_array = []
            for index, elmnt in enumerate(self.app_obj.data):
                if isinstance(elmnt, list):
                    # if the to_timestamp_data is too old, skip the whole element
                    if elmnt[1]['date'] < oldest_date_allowed:
                        continue

                    # if the from_timestamp_data is too old, overwrite the date with the oldest possible date
                    if elmnt[0]['date'] < oldest_date_allowed:
                        tmp_element = elmnt.copy()
                        tmp_element[0]['date'] = oldest_date_allowed

                        new_data_array.append(tmp_element)
                        continue

                    # otherwise both 0 and 1 entries are recent, just add them
                    new_data_array.append(elmnt)
                else:
                    # append the last element which is the new dict data
                    new_data_array.append(self.app_obj.data[-1])
            self.app_obj.data = new_data_array.copy()

            # corner case where all the entries are too old and removed,
            # thus only the last dict entry remains, thus nothing to decimate
            # so redo the decimation algo to create the first list
            if isinstance(self.app_obj.data[0], dict):
                self.decimate_data()

            # decimate the data
            if isinstance(self.app_obj.data[-1], dict):
                # just a small sanity check, can be removed in the future
                if isinstance(self.app_obj.data[-2], dict):
                    raise Exception('The second last data entry is a dict !')

                self.max_gap_s = self.app_obj.input_combobox_cycle_time.get()
                # added 10sec to account for timeouts
                self.max_gap_s = int(eval(self.max_gap_s.split(' ')[1])) + 10

                # only if the max_gap rule is respected
                if (self.app_obj.data[-1]['date'] - self.app_obj.data[-2][1]['date']).total_seconds() < self.max_gap_s:

                    # check if the status is the same and merge the new dict in the last list pair
                    if self.app_obj.data[-1]['status'] == self.app_obj.data[-2][1]['status']:
                        self.app_obj.data[-2] = [self.app_obj.data[-2][0],
                                                 self.app_obj.data[-1]]
                        del self.app_obj.data[-1]
                    # otherwise create a new pair
                    else:
                        to_overwrite = [self.app_obj.data[-2][1], # use the last status in order to not create gaps
                                        self.app_obj.data[-1]]
                        self.app_obj.data[-1] = to_overwrite
                # otherwise just create a new entry pair at the last array place
                else:
                    to_overwrite = [self.app_obj.data[-1],
                                    self.app_obj.data[-1]]
                    self.app_obj.data[-1] = to_overwrite

    def refresh_action(self):
        # add the current status
        online_status = self.InternetAvailability_obj.check_online_status()
        self.app_obj.data.append({'date': datetime.now(),
                                  'status': online_status})

        self.decimate_data()

        # update the status label
        self.app_obj.label_current_status.configure(require_redraw=True,
                                                    **{'text': f"Current status is {'OFFLINE' if not online_status else 'ONLINE'}",
                                                       'text_color': 'red' if not online_status else 'green'})

        for axvspan in self.app_obj.axvspans:
            axvspan.remove()

        self.app_obj.axvspans = []
        for pair in self.app_obj.data:
            self.app_obj.axvspans.append(self.app_obj.ax1.axvspan(pair[0]['date'],
                                                                  pair[1]['date'],
                                                                  color = 'green' if pair[1]['status'] else 'red'))

        # trim the data to be shown
        datetime_now = datetime.now()
        history_s = self.app_obj.seconds_combobox_max_history_s()
        oldest_date_allowed = datetime.now() - timedelta(seconds=history_s)
        self.app_obj.ax1.axis(xmin=max([oldest_date_allowed, self.app_obj.data[0][0]['date']]),
                              xmax=datetime_now)

        self.app_obj.canvas.draw()

        # finally save the dict on the local storage
        self.IO_orchestrator.save_data(self.app_obj.data)

    def sleep_and_check_exit(self,
                             duration_s):
        for _ in range(duration_s):
            sleep(1)
            if self.to_exit.to_exit:
                self.app_obj.label_current_status.configure(require_redraw=True,
                                                            **{'text': f"EXITING...",
                                                               'text_color': 'orange'})
                sleep(2)
                self.app_obj.root.quit()
                sys.exit(0)

    def refresh_plot(self):

        # allow the GUI to load and then do an initial GUI update
        self.sleep_and_check_exit(5)
        self.refresh_action()

        while True:
            self.sleep_and_check_exit(self.app_obj.seconds_combobox_cycle_time())
            while self.app_obj.stop_updating:
                sleep(1)
            self.refresh_action()

if __name__ == '__main__':
    configure_logger(log_level='INFO')

    to_exit = handle_exit()

    root = CTk()
    root.geometry("1200x600")
    root.title(f'pyConMon {title}')
    root.protocol("WM_DELETE_WINDOW", (lambda : to_exit.exit()))
    app = App(root)

    Thread(target=(lambda : getattr(Interaction_Handler(app,
                                                        to_exit), 'refresh_plot'))()
           ).start()

    root.mainloop()