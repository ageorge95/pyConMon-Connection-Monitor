import sys
sys.path.insert(0, 'CustomTkinter')

from logger import configure_logger
from IO import IO_handler
from InternetAvailability import InternetAvailability,\
    machine_and_port_to_ping
from CustomTkinter.customtkinter import CTk, CTkButton, CTkLabel, CTkComboBox
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

class App(IO_handler):
    def __init__(self,
                 root):
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

        self.label_server_used = CTkLabel(text=f"Using {address_to_be_used} to check the connectivity.")
        self.label_server_used.pack()

        self.label_current_status = CTkLabel(text="Current status is INITIALIZED",
                                             text_color='orange')
        self.label_current_status.pack()

        self.canvas = FigureCanvasTkAgg(self.fig,
                                        master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)


        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()
        self.toolbar.pack(side='left')

        self.button_stop_resume = CTkButton(text='STOP/ RESUME',
                                            command=self.stop_resume_action)
        self.button_stop_resume.pack(side='right')

        self.input_combobox_cycle_time = CTkComboBox(values=['Cycle 10 sec',
                                                             'Cycle 30 sec',
                                                             'Cycle 1*60 sec',
                                                             'Cycle 2*60 sec',
                                                             'Cycle 3*60 sec',
                                                             'Cycle 4*60 sec',
                                                             'Cycle 5*60 sec'])
        self.input_combobox_cycle_time.pack(side='right')
        self.seconds_combobox_cycle_time = lambda : int(eval(self.input_combobox_cycle_time.get().split(' ')[1]))

        self.input_combobox_max_history_h = CTkComboBox(values = ['History 1*24 h',
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
        self.label_current_status.config({'text': f"Current status is {'PAUSED' if self.stop_updating else 'RESUMED'}",
                                           'fg': 'orange'})
        self._log.info('STOP command received.')

class Interaction_Handler():
    def __init__(self,
                 app_obj: App):

        self.app_obj = app_obj

        self.InternetAvailability_obj = InternetAvailability(machine_and_port_to_ping=address_to_be_used)
        self.IO_orchestrator = IO_handler(server_used=address_to_be_used)

        # auto calculate the needed variables
        self.max_gap_s = self.app_obj.input_combobox_cycle_time.values[-1]
        self.max_gap_s = int(eval(self.max_gap_s.split(' ')[1]))

        self.max_history_s = self.app_obj.input_combobox_max_history_h.values[-1]
        self.max_history_s = 60 * 60 * int(eval(self.max_history_s.split(' ')[1]))

    def decimate_data(self):

        if len(self.app_obj.data) > 1:
            # bootstraping #1
            if type(self.app_obj.data[0]) != type(list()):
                self.app_obj.data.insert(0,
                                         [self.app_obj.data[0],
                                          self.app_obj.data[0]])

            # remove entries that are too old
            oldest_date_allowed = datetime.now() - timedelta(seconds=self.max_history_s)
            tmp_array = self.app_obj.data.copy()
            for index, elmnt in enumerate(self.app_obj.data):
                if type(elmnt) == type(list()):
                    if elmnt[-1]['date'] < oldest_date_allowed:
                        del tmp_array[index]
                    elif elmnt[0]['date'] < oldest_date_allowed:
                        tmp_array[index][0] = oldest_date_allowed
                    else:
                        break
                else:
                    break
            self.app_obj.data = tmp_array.copy()

            # bootstraping #2
            # this may never be needed, but just to be thorough
            if type(self.app_obj.data[0]) != type(list()):
                self.app_obj.data[0].insert(0,
                                            [self.app_obj.data[0],
                                             self.app_obj.data[0]])

            # loop through all the elements and decimate the data
            tmp_array = []
            for elmnt in self.app_obj.data:

                # if we find a list, it means that it was already checked in the past, so it is OK
                if type(elmnt) == type(list()):
                    tmp_array.append(elmnt)

                # if we find a dict, the value needs to be merged
                if type(elmnt) == type(dict()):
                    if (elmnt['date'] - tmp_array[-1][-1]['date']).total_seconds() < self.max_gap_s:

                        # check if the status is the same
                        if elmnt['status'] == tmp_array[-1][-1]['status']:
                            tmp_array[-1][-1] = elmnt
                        else:
                            tmp_array.append([elmnt,
                                              elmnt])
                    else:
                        tmp_array.append([elmnt,
                                          elmnt])
            self.app_obj.data = tmp_array.copy()

    def refresh_action(self):
        # add the current status
        online_status = self.InternetAvailability_obj.check_online_status()
        self.app_obj.data.append({'date': datetime.now(),
                                  'status': online_status})

        self.decimate_data()

        # update the status label
        self.app_obj.label_current_status.config({'text': f"Current status is {'OFFLINE' if not online_status else 'ONLINE'}",
                                                  'fg': 'red' if not online_status else 'green'})

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

    def refresh_plot(self):

        # allow the GUI to load and then do an initial GUI update
        sleep(5)
        self.refresh_action()

        while True:
            sleep(self.app_obj.seconds_combobox_cycle_time())
            while self.app_obj.stop_updating:
                sleep(1)
            self.refresh_action()

if __name__ == '__main__':
    configure_logger()

    root = CTk()
    root.geometry("1200x600")
    root.title(f'pyConMon {title}')
    app = App(root)

    Thread(target=(lambda app : getattr(Interaction_Handler(app), 'refresh_plot'))(app)
           ).start()

    root.mainloop()