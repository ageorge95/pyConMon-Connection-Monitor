import sys
sys.path.insert(0, 'CustomTkinter')

from logger import configure_logger
from IO import IO_handler
from InternetAvailability import InternetAvailability,\
    trusted_website_to_ping_config
from CustomTkinter.customtkinter import CTk, CTkButton, CTkLabel, CTkComboBox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,\
    NavigationToolbar2Tk
import matplotlib.dates as md
import matplotlib.pyplot as plt
from time import sleep
from threading import Thread
from logging import getLogger
from datetime import datetime
from argparse import ArgumentParser

# Optional CLI interface
parser = ArgumentParser(description='Optional CLI interface for the connectivity monitor.')

parser.add_argument('-a',
                    '--address',
                    type=str,
                    help='The address to be used for the connectivity check',
                    default=trusted_website_to_ping_config)

args = parser.parse_args()
address_to_be_used = args.address

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
        self.ax1.tick_params(axis='x', labelrotation=45)

        self.line, = self.ax1.plot(list(self.data.keys()),
                                  list(self.data.values()),
                                  linewidth = 3,
                                  c = 'r')

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

        self.InternetAvailability_obj = InternetAvailability(trusted_website_to_ping=address_to_be_used)
        self.IO_orchestrator = IO_handler(server_used=address_to_be_used)

    def refresh_action(self):
        # add the current status
        online_status = self.InternetAvailability_obj.check_online_status()
        self.app_obj.data[datetime.now()] = online_status

        # update the status label
        self.app_obj.label_current_status.config({'text': f"Current status is {'OFFLINE' if not online_status else 'ONLINE'}",
                                                  'fg': 'red' if not online_status else 'green'})

        self.app_obj.line.set_data(list(self.app_obj.data.keys()),
                                            list(self.app_obj.data.values()))

        # trim the data to be shown
        datetime_now = datetime.now()
        max_history_s = self.app_obj.seconds_combobox_max_history_s()
        trimmed_dict = dict(filter(lambda _:(datetime_now - _[0]).total_seconds() < max_history_s, self.app_obj.data.items()))

        self.app_obj.ax1.axis(xmin=min(list(trimmed_dict.keys())),xmax=max(list(trimmed_dict.keys())),
                              ymin=min(list(trimmed_dict.values())), ymax=max(list(trimmed_dict.values())))

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
    app = App(root)

    Thread(target=(lambda app : getattr(Interaction_Handler(app), 'refresh_plot'))(app)
           ).start()

    root.mainloop()