# GUI Interface for pi_seq_BLR
# Filename:     app.py
# Author:       Adrian Padin
# Start Date:   6/1/2016

from Tkinter import * # GUI Library

import time
import datetime as dt
import math
import numpy as np
import os
import sys
import threading as th
from collections import OrderedDict

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

import grapher
from get_data import get_power


####################  DEFINITIONS  ####################

settings_file = "settings.txt"


####################  HELPER FUNCTIONS  ####################

# Wrapper function for consistent time formatting
def time2string(timestamp):
    return dt.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Give the window a title and icon, destroy cleanly when X is pressed
def initWindow(window, title=" "):
    window.wm_title(title) # Change title
    icon_file = PhotoImage(file = "merit_icon.ppm") # Change icon
    window.tk.call( 'wm', 'iconphoto', window._w, icon_file )

    def quit_and_destroy(window):
        window.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", lambda: quit_and_destroy(window))


####################  APPLICATION  ####################

# Class that describes the application's attributes
class App(Frame):

    # Constructor
    def __init__(self, master=None):

        Frame.__init__(self, master)

        # There are two major frames: the left from contains the dashboard,
        # which displays information and options for the analysis, and the
        # right from is the prediction/error graph.

        self.createDashFrame() # Contains the dashboard, including time, power, and settings
        self.createGraphFrame() # Frame which contains power and error graphs

        # Fill and expand allow the display to grow and shrink as the user changes
        # the window size
        self.pack(fill='both', expand=True)


    ####################  DASHBOARD  ####################

    # Starting point for the Dashboard Frame
    def createDashFrame(self):

        self.dashFrame = Frame(self)
        self.dashFrame.pack(side='left', padx=10, pady=10, fill='both')
        Label(self.dashFrame, text="NextHome Dashboard", font=('bold')).grid(pady=10)

        # Timer and power
        self.curtime = int(time.time())
        self.timer = Label(self.dashFrame, text="Current time:\t")
        self.timer.grid(sticky=W)
        self.power = Label(self.dashFrame, text="Current usage:\t0.0 kW")
        self.power.grid(sticky=W)
        self.after(200, self.updateTime)

        Label(self.dashFrame, text="").grid() # Gap row

        # Settings display
        self.settingsFrame = Frame(self.dashFrame)
        self.settingsFrame.grid(sticky=W)
        self.getSettings()  # read settings from file
        self.showSettings() # display settings in settingsFrame

        Label(self.dashFrame, text="").grid() # Gap row

        # Settings button
        self.settings_button = Button(self.dashFrame,
                                      text="Change settings...",
                                      command=self.settingsWindow)
        self.settings_button.grid()

        Label(self.dashFrame, text="").grid()# Gap row
        Label(self.dashFrame, text="").grid()# Gap row
        Label(self.dashFrame, text="").grid()# Gap row

        # Graph from file
        self.graph_button = Button(self.dashFrame,
                                   text="Graph From File",
                                   command=self.graphFromFile)
        self.graph_button.grid(sticky=W+E)
        self.graph_status = Label(self.dashFrame, text="")
        self.graph_status.grid()

        Label(self.dashFrame, text="").grid()# Gap row

        # Start analysis
        self.analysis_button = Button(self.dashFrame,
                                      text="Start Analysis",
                                      bg='green',
                                      activebackground='green',
                                      command=self.algoStart)
        self.analysis_button.grid(sticky=W+E)
        self.analysis_status = Label(self.dashFrame, text="")


    # Keep track of and display the current time and power
    def updateTime(self):

        # Update time
        if self.curtime != int(time.time()):
            self.curtime = int(time.time())
            self.timer.configure(text=("Current time:\t" + time2string(time.time())))

        # Update power
        if self.

        self.after(200, self.updateTime) # Repeat every 200 milliseconds


    ####################  SETTINGS  ####################

    # Read in settings from the settings file and put in a dictionary
    def getSettings(self):
        infile = open(settings_file, 'rb')
        self.settings = OrderedDict()

        for line in infile:
            line = line.split()
            if len(line) == 0: continue       # Ignore blank lines
            if line[0] == '#': continue       # Ignore comments
            self.settings[line[0]] = line[-1]

        infile.close()


    # Display settings in the Settings tab
    def showSettings(self):

        # First delete any existing widgets
        for wid in self.settingsFrame.winfo_children():
            wid.destroy()

        Label(self.settingsFrame, text="Settings", font=('bold')).grid(sticky=W)
        for key in self.settings:
            Label(self.settingsFrame, text=(key + ":   " + self.settings[key])).grid(sticky=W)


    # Opens the settings window
    def settingsWindow(self):

        # Create a new window and initialize
        settings_window = Toplevel(self)
        initWindow(settings_window, title="Settings")
        Grid.columnconfigure(settings_window, 0, weight=1)

        # Disable main window and grey out the button
        settings_window.grab_set()
        self.settings_button.configure(fg='grey')

        # Make entry bars for all current settings
        entry_dict = {}
        count = 0
        for key in self.settings:
            Label(settings_window, text=(key + ":  ")).grid(row=count, column=0, sticky=W)
            new_entry = Entry(settings_window)
            new_entry.grid(row=count, column=1, sticky=E)
            new_entry.insert(0, self.settings[key])
            entry_dict[key] = new_entry
            count += 1

        # Save changes button
        Button(settings_window,
               text="Save changes",
               command=(lambda: self.updateSettings(entry_dict))
               ).grid(columnspan=2, sticky=W+E)

        # Display a warning if any inputs are incorrect (see "updateSettings")
        self.settings_status = Label(settings_window, text="")

        def closeSettings():
            self.settings_button.configure(fg='black')
            #settings_window.quit()
            settings_window.destroy()
            print ("closed settings window")

        settings_window.protocol("WM_DELETE_WINDOW", closeSettings)


    # Update the current settings
    def updateSettings(self, entry_dict):

        # TODO: sanitize inputs
        try:
            for key in self.settings:
                value = entry_dict[key].get().strip()
                assert value != ''
                self.settings[key] = entry_dict[key].get()
        except AssertionError:
            self.settings_status.config(text="Invalid entry for %s: try again" % key, fg='red')
            self.settings_status.grid(columnspan=2)
        else:
            self.writeSettings(self.settings)
            self.showSettings()
            self.settings_status.config(text="Changes saved", fg='green')
            self.settings_status.grid(columnspan=2)


    # Write settings out to the settings file
    def writeSettings(self, settings):
        outfile = open(settings_file, 'rb')
        line_list = []

        # Read in current file and make changes line-by-line
        for line in outfile:
            line_list.append(line)
            line = line.split()
            if len(line) > 0 and line[0] != '#':
                if line[0] in settings:
                    line = line[0] + ' : ' + str(settings[line[0]]) + '\n'
                    line_list[-1] = line

        # Write changes to file
        outfile.close()
        outfile = open("settings.txt", 'wb')
        for line in line_list:
            outfile.write(line)


    ####################  ALGORITHM  ####################

    # Start the algorithm
    def algoStart(self):
        self.analysis_status.configure(text="Running analysis...")
        self.analysis_button.configure(text="Stop Analysis",
                                       bg='red',
                                       activebackground='red',
                                       command=self.algoStop)
        self.analysis_button.grid(sticky=W+E)
        self.analysis_status.grid()

    # Start the algorithm
    def algoStop(self):
        self.analysis_status.configure(text="Analysis stopped.")
        self.analysis_button.configure(text="Start Analysis",
                                       bg='green',
                                       activebackground='green',
                                       command=self.algoStart)
        self.analysis_button.grid(sticky=W+E)
        self.analysis_status.grid()


    ####################  GRAPHS  ####################

    # Startin point for Graph Frame
    def createGraphFrame(self):

        self.graphFrame = Frame(self)
        self.graphFrame.pack(side='right', fill='both', expand=True)
        Grid.rowconfigure(self.graphFrame, 0, weight=1)
        Grid.columnconfigure(self.graphFrame, 0, weight=1)

        fig = plt.figure() # Create figure

        self.graph_predict = fig.add_subplot(211) # Target versus prediction
        self.graph_error = fig.add_subplot(212)   # Error (target - prediction)

        #self.graph_predict.set_title("Prediction vs. Target")
        #self.graph_predict.set_xlabel("Time")
        self.graph_predict.set_ylabel("Power (Watts)")

        #self.graph_error.set_title("Error")
        self.graph_error.set_xlabel("Time")
        self.graph_error.set_ylabel("Error (Watts)")

        # Sets the x-axis to only show hours, minutes, and seconds of time
        self.graph_predict.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M"))
        self.graph_error.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M"))

        # Sets the x-axis to only show 6 tick marks
        self.graph_predict.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=5))

        plt.subplots_adjust(hspace = 0.3)

        # Add lines and legend
        self.predict_line, = self.graph_predict.plot([1, 2], [0, 0], color='0.75', label='Prediction')
        self.target_line, = self.graph_predict.plot([1, 2], [0, 0], color='red', linestyle='--', label='Target')
        self.error_line, = self.graph_error.plot([1, 2], [0, 0], color='red', label='Error')

        self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        self.graph_error.legend(handles=[self.error_line])

        # Tk canvas which is embedded into application
        self.canvas = FigureCanvasTkAgg(fig, master=self.graphFrame)
        self.canvas.get_tk_widget().pack(side='bottom', fill='both', expand=True)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.graphFrame)
        toolbar.update()
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=True)
        self.canvas.show()


    # Get new data to graph
    def graphFromFile(self):

        self.graph_status.configure(text="Reading data from file...")
        self.graph_button.configure(state='disabled', fg='grey')

        try:
            y_target, y_predict, y_time = grapher.read_csv(self.datafile)
        except:
            self.graph_status.configure(text="Error: file does exist")
            self.graph_button.configure(state='normal', fg='black')
            return

        # Graph results in a new thread
        self.graph_status.configure(text="Graphing data. Please wait...")
        graph_thread = th.Thread(target=self.graphData, args=(y_target, y_predict, y_time))
        graph_thread.start()


    # Send given data to the graph
    def graphData(self, y_target, y_predict, y_time):

        # First check if y_time is list of datetime strings or UNIX timestamps
        if isinstance(y_time[0], str):
            y_time = [dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S\n") for t in y_time]
        elif isinstance(y_time[0], float):
            y_time = [dt.datetime.fromtimestamp(t) for t in y_time]

        # Calculate the error vector
        y_error = []
        for i in xrange(len(y_target)):
            y_error.append(y_predict[i] - y_target[i])

        # Set x and y axis limits
        # Axes update every time to achieve "scrolling" effect
        xmin = min(y_time)
        xmax = max(y_time)

        ymin = min(min(y_target), min(y_predict))
        ymax = max(max(y_target), max(y_predict))

        emin = min(y_error)
        emax = max(y_error)

        self.graph_predict.set_xlim(xmin, xmax)
        self.graph_predict.set_ylim(ymin+10, ymax)

        self.graph_error.set_xlim(xmin, xmax)
        self.graph_error.set_ylim(emin, emax)

        # Set new data (automatically updates the graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)

        #graph_predict.autofmt_xdate()
        #graph_error.autofmt_xdate()

        self.canvas.show()
        plt.tight_layout()

        self.graph_status.configure(text="Graphing complete.")
        self.graph_button.configure(state='normal', fg='black')


####################  MAIN EXECUTION  ####################

# Execute the application
root = Tk()
initWindow(root, title="NextHome Energy Analysis")

try:
    app = App(master=root)
    root.mainloop()
except KeyboardInterrupt:
    print "Exiting on keyboard interrrupt"
    root.quit()
    root.destroy()
    
