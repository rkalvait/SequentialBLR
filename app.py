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

from grapher import Grapher, CSV, initWindow, time2string
from algoRunFunctions import movingAverage
from analyzer import analyze


####################  DEFINITIONS  ####################
settings_file = 'app/settings.txt'


####################  APPLICATION  ####################

# Class that describes the application's attributes
class App(Frame):

    # Constructor
    def __init__(self, master=None):

        Frame.__init__(self, master)

        # Global lock for multithreading
        # Shared data:
        # -- self.kill_flag
        # -- self.settings
        self.lock = Lock()

        # There are two major frames: the left from contains the dashboard,
        # which displays information and options for the analysis, and the
        # right frame contains the target/prediction and error graphs.

        self.graphFrame = Grapher(master=self)
        self.graphFrame.pack(side='right', fill='both', expand=True)
        
        self.createDashFrame() # Contains the dashboard and settings


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

        # Update the graph
        self.graph_button = Button(self.dashFrame,
                                   text="Refresh Graph",
                                   command=self.updateGraph)
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
            updateRate = int(self.settings['updateRate'])
            
            if (updateRate > 0 and
                (self.curtime % updateRate) == 0):
                self.updateGraph()

        self.after(200, self.updateTime) # Repeat every x milliseconds


    ####################  SETTINGS  ####################

    # Read in settings from the settings file and put in a dictionary
    def getSettings(self):
        infile = open(settings_file, 'rb')

        self.settings = OrderedDict()

        # Each setting is in the form "key=value"
        for line in infile:
            line = line.rstrip()
            if len(line) == 0: continue       # Ignore blank lines
            if line[0] == '#': continue       # Ignore comments
            key, value = line.split('=')
            self.settings[key] = value

        infile.close()


    # Display settings in the Settings tab
    def showSettings(self):

        # First delete any existing widgets
        for wid in self.settingsFrame.winfo_children():
            wid.destroy()

        Label(self.settingsFrame, text="Settings", font=('bold')).grid(sticky=W)

        # Add units to each setting
        count = 1
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

        for key in self.settings:
            Label(settings_window, text=(key + ":  ")).grid(row=count, column=0, sticky=W)
            new_entry = Entry(settings_window)
            new_entry.grid(row=count, column=1, sticky=E)
            new_entry.insert(0, self.settings[key])
            entry_dict[key] = new_entry
            count += 1

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
               ).grid(columnspan=1, sticky=W+E)

        # Cancel button
        Button(settings_window,
               text="Cancel",
               fg='red',
               command=lambda: closeSettings()
               ).grid(row=count, column=1, sticky=W+E)

        # Display a warning if any inputs are incorrect (see "updateSettings")
        self.settings_status = Label(settings_window, text="")

        settings_window.protocol("WM_DELETE_WINDOW", closeSettings)


    # Update the current settings
    def updateSettings(self, entry_dict):

        # TODO: sanitize inputs better
        for key in self.settings:
            value = entry_dict[key].get().strip()
            assert value != ''
            
            # Sanitize for each potential key
            if key != 'inputFile':
                assert(value.isdigit())
                if key != 'smoothingWindow' and key != 'updateRate':
                    assert(int(value) > 0)
                else:
                    assert(int(value) >= 0 and int(value) <= 1000)

            else: #elif key == 'inputFile':
                assert(not value[0].isdigit())

            self.settings[key] = value


    # Write settings out to the settings file
    def writeSettings(self, settings):
        outfile = open(settings_file, 'rb')
        line_list = []
        
        # Read in current file and make changes line-by-line
        for line in outfile:
            line = line.rstrip()
            if len(line) > 0 and line[0] != '#':
                key, value = line.split('=')
                if key in settings:
                    line = key + '=' + str(self.settings[key])
            line += '\n'
            line_list.append(line)

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

        granularity = int(self.settings['granularity'])
        window = int(self.settings['trainingWindow'])
        interval = int(self.settings['forecastingInterval'])

        self.algo_thread = Thread(target=analyze, args=(self, granularity, window, interval))
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


    ####################  GRAPHING  ####################

    # Starts the thread which reads the file and updates the graph
    def updateGraph(self):

        self.graph_button.configure(state='disabled', fg='grey')
        self.graph_status.configure(text="Reading data from file...")

        infile = self.settings['inputFile']
        smoothingWin = int(self.settings['smoothingWindow'])

        '''
        results = [None, None, None]
        Thread(target=self.getDataFromFile).start()
        '''
        
        try:
            y_time, y_target, y_predict = CSV(infile).read()
        except IOError as e:
            self.graph_status.configure(text="Error: file does exist")
            self.graph_button.configure(state='normal', fg='black')
            return

        self.curpower = float(y_target[-1])

        # Smooth data if requested
        if smoothingWin > 0:
            y_target = movingAverage(y_target, smoothingWin)
            y_predict = movingAverage(y_predict, smoothingWin)

        # Graph results
        self.graph_status.configure(text="Graphing data. Please wait...")
        self.graphFrame.graph(y_time, y_target, y_predict)

        self.graph_status.configure(text="Graphing complete.")
        self.graph_button.configure(state='normal', fg='black')

    '''
    # Get new data to graph
    def getDataFromFile(self, results):
    '''


####################  MAIN EXECUTION  ####################

# Execute the application
root = Tk()
initWindow(root, title="NextHome Energy Analysis")

try:
    app = App(master=root)
    app.pack(fill='both', expand=True)
    root.mainloop()
except KeyboardInterrupt:
    print "Exiting on keyboard interrrupt"
    root.quit()
    root.destroy()
    
