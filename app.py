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

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

import grapher


####################  HELPER FUNCTIONS  ####################

# Wrapper function for consistent time formatting
def time2string(timestamp):
    return dt.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Give the window a title and icon, and tell it to destroy when X is pressed
def initWindow(window, title=" "):
    window.wm_title(title) # Change title
    icon_file = PhotoImage(file = "merit_icon.ppm") # Change icon
    window.tk.call( 'wm', 'iconphoto', window._w, icon_file )
    window.protocol("WM_DELETE_WINDOW", window.destroy)


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
        
        # Gap row
        Label(self.dashFrame, text="").grid()

        # Settings display
        Label(self.dashFrame, text="Settings", font=('bold')).grid(sticky=W)
        self.datafile = "results.csv"
        self.update_rate = 60
        self.datafileLabel = Label(self.dashFrame, text="Data file:  \tresults.csv")
        self.datafileLabel.grid(sticky=W)
        self.update_rateLabel = Label(self.dashFrame, text="Update rate:\t60 seconds")
        self.update_rateLabel.grid(sticky=W)

        
        # Gap row
        Label(self.dashFrame, text="").grid()
        
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


    # Keep track of and display the current time
    def updateTime(self):
        if self.curtime != int(time.time()):
            self.curtime = int(time.time())
            self.timer.configure(text=("Current time:\t" + time2string(time.time())))
        self.after(200, self.updateTime) # Repeat every 200 milliseconds
        

    # Opens the settings window
    def settingsWindow(self):

        # Create the new window (using Toplevel)
        settings_window = Toplevel(self)
        initWindow(settings_window, title="Settings")
        Grid.columnconfigure(settings_window, 0, weight=1)
        
        # Disable main window and grey out the button
        settings_window.grab_set()
        self.settings_button.configure(fg='grey')

        # Entry bars for all current settings. Current settings include:
        # -- update_rate: how often to update graph with new data
        # -- datafile: file to read data from
        
        Label(settings_window, text="Data filename:").grid(row=1, column=0, sticky=W)
        file_input = Entry(settings_window)
        file_input.insert(0, self.datafile)
        file_input.grid(row=1, column=1)
        
        Label(settings_window, text="Update rate:").grid(row=0, column=0, sticky=W)
        update_input = Entry(settings_window)
        update_input.insert(0, self.update_rate)
        update_input.grid(row=0, column=1)

        # Save changes button
        Button(settings_window,
               text="Save changes",
               command=(lambda: self.updateSettings(update_input.get(),
                                                    file_input.get()))
               ).grid(row=2, columnspan=2, sticky=W+E)

        # Display a warning if any inputs are incorrect (see "updateSettings")
        self.settings_status = Label(settings_window, text="")

        def closeSettings():
            self.settings_button.configure(fg='black')
            settings_window.destroy()

        settings_window.protocol("WM_DELETE_WINDOW", closeSettings)

        
    # Update the current settings
    def updateSettings(self, update_rate, datafile):
            
        # Sanitize inputs
        try:
            self.datafile = datafile
            self.update_rate = int(update_rate)
        except:
            self.settings_status.config(text="Invalid entry: try again", fg='red')
            self.settings_status.grid(row=3, columnspan=2)
        else:
            self.update_rateLabel.configure(text="Update rate:\t%d seconds" % self.update_rate)
            self.datafileLabel.configure(text="Data file:  \t%s" % self.datafile)
            self.settings_status.config(text="Changes saved", fg='green')
            self.settings_status.grid(row=3, columnspan=2)


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
    
        self.graphFrame = Frame(self, bg='red')
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

        self.canvas.show()
        plt.tight_layout()
        
        self.graph_status.configure(text="Graphing complete.")
        self.graph_button.configure(state='normal', fg='black')


####################  MAIN EXECUTION  ####################
        
# Execute the application
root = Tk()
initWindow(root, title="NextHome Energy Analysis")
root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

try:
    app = App(master=root)
    root.mainloop()
except KeyboardInterrupt:
    print "Exiting on keyboard interrrupt"

    
