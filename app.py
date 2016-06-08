#!/usr/bin/python

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
from threading import Thread, Lock
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
from algoRunFunctions import movingAverage
from analyzer import analyze


####################  DEFINITIONS  ####################

settings_file = 'app/settings.txt'
icon_file = 'app/merit_icon.ppm'


####################  HELPER FUNCTIONS  ####################

# Wrapper function for consistent time formatting
def time2string(timestamp):
    return dt.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Give the window a title and icon, destroy cleanly when X is pressed
def initWindow(window, title=" "):
    window.wm_title(title)                              # Change title
    icon = PhotoImage(file = icon_file)                 # Change icon
    window.tk.call('wm', 'iconphoto', window._w, icon)

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

        # Global lock for multithreading
        # Shared data:
        # -- self.kill_flag
        # -- self.graphFrame and all children
        # -- self.settings
        self.lock = Lock()

        # There are two major frames: the left from contains the dashboard,
        # which displays information and options for the analysis, and the
        # right frame contains the target/prediction and error graphs.

        self.createDashFrame() # Contains the dashboard and settings
        self.createGraphFrame() # Frame which contains power and error graphs

        # Fill and expand allow the display to grow and shrink as the user
        # changes the application window size
        self.pack(fill='both', expand=True)


    ####################  DASHBOARD  ####################

    # Starting point for the Dashboard Frame
    def createDashFrame(self):

        self.dashFrame = Frame(self)
        self.dashFrame.pack(side='left', padx=10, pady=10, fill='both')
        Label(self.dashFrame, text="NextHome Dashboard", font=('bold')).grid(pady=10)

        # Timer and power
        self.curtime = int(time.time())
        self.curpower = 0.0
        self.timer = Label(self.dashFrame, text="Current time:\t")
        self.timer.grid(sticky=W)
        self.power = Label(self.dashFrame, text="Current usage:\t")
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
                                   text="Refresh Graph",
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
            self.power.configure(text=("Current power:\t%.3f kW" % self.curpower)) 

            # Update graph
            self.lock.acquire()
            updateRate = int(self.settings['updateRate'])
            self.lock.release()
            
            if (updateRate > 0 and
                (self.curtime % updateRate) == 0):
                self.graphFromFile()

        self.after(200, self.updateTime) # Repeat every x milliseconds


    ####################  SETTINGS  ####################

    # Read in settings from the settings file and put in a dictionary
    def getSettings(self):
        infile = open(settings_file, 'rb')

        self.lock.acquire()
        self.settings = OrderedDict()

        # Each setting is in the form "key=value"
        for line in infile:
            line = line.rstrip()
            if len(line) == 0: continue       # Ignore blank lines
            if line[0] == '#': continue       # Ignore comments
            key, value = line.split('=')
            self.settings[key] = value

        self.lock.release()
        infile.close()


    # Display settings in the Settings tab
    def showSettings(self):

        # First delete any existing widgets
        for wid in self.settingsFrame.winfo_children():
            wid.destroy()

        Label(self.settingsFrame, text="Settings", font=('bold')).grid(sticky=W)

        count = 1

        self.lock.acquire()

        # Add units to each setting
        for key in self.settings:
            Label(self.settingsFrame, text=(key + ":  ")).grid(row=count, column=0, sticky=W)

            if key == 'granularity':
                val_text = str(self.settings[key]) + " minute(s)"
            elif key == 'trainingWindow':
                val_text = str(self.settings[key]) + " hour(s)"
            elif key == 'forecastingInterval':
                val_text = str(self.settings[key]) + " hour(s)"
            elif key == 'updateRate':
                val_text = str(self.settings[key]) + " second(s)"
            elif key == 'smoothingWindow':
                val_text = str(self.settings[key]) + " minute(s)"
            else:
                val_text = str(self.settings[key])
                
            Label(self.settingsFrame, text=val_text).grid(row=count, column=1, sticky=W)
            count += 1
            
        self.lock.release()

    # Opens the settings window
    def settingsWindow(self):

        # Create a new window and initialize
        settings_window = Toplevel(self)
        settings_window.transient()
        initWindow(settings_window, title="Settings")
        Grid.columnconfigure(settings_window, 0, weight=1)

        # Disable main window and grey out the button
        settings_window.grab_set()
        self.settings_button.configure(fg='grey')

        # Make entry bars for all current settings
        entry_dict = {}
        count = 0

        self.lock.acquire()
        for key in self.settings:
            Label(settings_window, text=(key + ":  ")).grid(row=count, column=0, sticky=W)
            new_entry = Entry(settings_window)
            new_entry.grid(row=count, column=1, sticky=E)
            new_entry.insert(0, self.settings[key])
            entry_dict[key] = new_entry
            count += 1
        self.lock.release()

        def closeSettings():
            self.settings_button.configure(fg='black')
            settings_window.destroy()

        def saveAndClose(entry_dict):

            # Make sure the settings saved properly before exiting
            try:
                self.updateSettings(entry_dict)
                
            except AssertionError:
                self.settings_status.config(text="Invalid entry for %s: try again" % key, fg='red')
                self.settings_status.grid(columnspan=2)

            else:
                self.writeSettings(self.settings)
                self.showSettings()
                #self.settings_status.config(text="Changes saved!", fg='blue')
                #self.settings_status.grid(columnspan=2)
                closeSettings()
            
        # Save changes button
        Button(settings_window,
               text="Save and Close",
               command=lambda: saveAndClose(entry_dict)
               ).grid(columnspan=2, sticky=W+E)

        '''
        # Cancel button
        Button(settings_window,
               text="Cancel",
               fg='red',
               command=lambda: closeSettings()
               ).grid(row=count, column=1, sticky=W+E)
        '''

        # Display a warning if any inputs are incorrect (see "updateSettings")
        self.settings_status = Label(settings_window, text="")

        settings_window.protocol("WM_DELETE_WINDOW", closeSettings)


    # Update the current settings
    def updateSettings(self, entry_dict):

        # TODO: sanitize inputs better
        self.lock.acquire()
        for key in self.settings:
            value = entry_dict[key].get().strip()
            assert value != ''
            
            # Sanitize for each potential key
            if key != 'inputFile':
                assert(value.isdigit())
                if key != 'smoothingWindow':
                    assert(int(value) > 0)
                else:
                    assert(int(value) >= 0 and int(value) <= 1000)

            else: #elif key == 'inputFile':
                assert(not value[0].isdigit())

            self.settings[key] = value

        self.lock.release()


    # Write settings out to the settings file
    def writeSettings(self, settings):
        outfile = open(settings_file, 'rb')
        line_list = []

        self.lock.acquire()
        
        # Read in current file and make changes line-by-line
        for line in outfile:
            line = line.rstrip()
            if len(line) > 0 and line[0] != '#':
                key, value = line.split('=')
                if key in settings:
                    line = key + '=' + str(self.settings[key])
            line += '\n'
            line_list.append(line)

        self.lock.release()

        # Write changes to file
        outfile.close()
        outfile = open(settings_file, 'wb')
        for line in line_list:
            outfile.write(line)


    ####################  ALGORITHM  ####################

    # Start the algorithm
    def algoStart(self):

        # Kill flag tells the analyzer to top and exit cleanly
        self.lock.acquire()
        self.kill_flag = False
        self.lock.release()

        self.algo_thread = Thread(target=analyze, args=(self,))
        self.algo_thread.start()
        
        self.analysis_status.configure(text="Running analysis...")
        self.analysis_button.configure(text="Stop Analysis",
                                       bg='red',
                                       activebackground='red',
                                       command=self.algoStop)
        self.analysis_button.grid(sticky=W+E)
        self.analysis_status.grid()


    # Start the algorithm
    def algoStop(self):

        # Raise the kill flag and wait for the thread to notice
        self.lock.acquire()
        self.kill_flag = True
        self.lock.release()
        self.algo_thread.join()
        
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
        self.lock.acquire()
        
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
        x, y = [1, 2], [0, 0]
        self.target_line, = self.graph_predict.plot(x, y, color='red', linestyle='--')
        self.predict_line, = self.graph_predict.plot(x, y, color='0.75')
        self.error_line, = self.graph_error.plot(x, y, color='red')

        #self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        #self.graph_error.legend(handles=[self.error_line])
        self.graph_predict.legend([self.target_line, self.predict_line], ["Target", "Prediction"])
        self.graph_error.legend([self.error_line], ["Error"])

        # Tk canvas which is embedded into application
        self.canvas = FigureCanvasTkAgg(fig, master=self.graphFrame)
        self.canvas.get_tk_widget().pack(side='bottom', fill='both', expand=True)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.graphFrame)
        toolbar.update()
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=True)
        self.canvas.show()

        self.lock.release()


    # Get new data to graph
    def graphFromFile(self):

        self.graph_status.configure(text="Reading data from file...")
        self.graph_button.configure(state='disabled', fg='grey')

        self.lock.acquire()
        infile = self.settings['inputFile']
        self.lock.release()
        
        try:
            y_target, y_predict, y_time = grapher.read_csv(infile)
        except IOError as e:
            self.graph_status.configure(text="Error: file does exist")
            self.graph_button.configure(state='normal', fg='black')
            return

        self.curpower = float(y_target[-1])

        # Smooth data if requested
        self.lock.acquire()
        smoothingWin = int(self.settings['smoothingWindow'])
        self.lock.release()
        
        if smoothingWin > 0:
            y_target = movingAverage(y_target, smoothingWin)
            y_predict = movingAverage(y_predict, smoothingWin)

        # Graph results in a new thread
        self.graph_status.configure(text="Graphing data. Please wait...")
        graph_thread = Thread(target=self.graphData, args=(y_target, y_predict, y_time))
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

        self.lock.acquire()

        self.graph_predict.set_xlim(xmin, xmax)
        self.graph_predict.set_ylim(ymin, ymax)

        self.graph_error.set_xlim(xmin, xmax)
        self.graph_error.set_ylim(emin, emax)

        # Set new data (automatically updates the graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)

        labels = self.graph_predict.get_xticklabels()
        plt.setp(labels, rotation=10)
        labels = self.graph_error.get_xticklabels()
        plt.setp(labels, rotation=10)

        plt.tight_layout()
        self.canvas.show()

        self.lock.release()

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
    
