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

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import grapher

# For consistent time formatting
def time2string(timestamp):
    return dt.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Class that describes the application's attributes
class App(Frame):

    # Keep track of and display the current time
    def updateTime(self):
        if self.curtime != int(time.time()):
            self.curtime = int(time.time())
            self.timer.configure(text=("Current time:\t" + time2string(time.time())))
        self.after(200, self.updateTime) # Repeat every 200 milliseconds
        
    
    # Update the current settings
    def updateSettings(self, update_rate, datafile):
            
        # Sanitize inputs
        try:
            self.datafile = datafile
            self.update_rate = int(update_rate)
        except:
            self.settingsWarning.config(text="Invalid entry: try again", fg='red')
        else:
            self.settingsWarning.config(text="Changes saved", fg='green')
            self.update_rateLabel.configure(text="Update rate:\t%d seconds" % self.update_rate)
            self.datafileLabel.configure(text="Data file:  \t%s" % self.datafile)
            
        
    # Opens the settings window
    def changeSettings(self):
        settingsWindow = Toplevel(self)
        settingsWindow.wm_title("") # Change title
        settingsWindow.tk.call( 'wm', 'iconphoto', settingsWindow._w, icon_file )
        Grid.columnconfigure(settingsWindow, 0, weight=1)
        
        Label(settingsWindow, text="Update rate:").grid(row=0, column=0, sticky=W)
        update_input = Entry(settingsWindow)
        update_input.insert(0, self.update_rate)
        update_input.grid(row=0, column=1)
        
        Label(settingsWindow, text="Data filename:").grid(row=1, column=0, sticky=W)
        file_input = Entry(settingsWindow)
        file_input.insert(0, self.datafile)
        file_input.grid(row=1, column=1)
        
        Button(settingsWindow,
               text="Save changes",
               command=(lambda: self.updateSettings(update_input.get(), file_input.get()))
               ).grid(row=2, columnspan=2, sticky=W+E)
               
        self.settingsWarning = Label(settingsWindow, text="")
        self.settingsWarning.grid(row=3, columnspan=2)

                   
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
        self.graph_predict.set_ylim(ymin, ymax)

        self.graph_error.set_xlim(xmin, xmax)
        self.graph_error.set_ylim(emin, emax)

        # Set new data (automatically updates the graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)

        self.canvas.show()
        
    
    # Get new data to graph
    def refreshGraph(self):
    
        '''
        y_time = range(0, 30, 1)
        y_target = range(0, 30, 1)
        y_predict = range(0, 30, 1)
        y_predict.reverse()
        '''
        y_target, y_predict, y_time = grapher.read_csv()
        self.graphData(y_target, y_predict, y_time)
    
    ####################  WIDGET CREATION  ####################
    
    def createGraphFrame(self):
    
        self.graphFrame = Frame(self)
        self.graphFrame.pack(side='right', fill='both', expand=True)
        
        Grid.rowconfigure(self.graphFrame, 0, weight=1)
        Grid.columnconfigure(self.graphFrame, 0, weight=1)
        
        # Create figure and added main title
        fig = plt.figure()
        
        self.graph_predict = fig.add_subplot(211) # Target versus prediction
        self.graph_error = fig.add_subplot(212) # Error (target - prediction)

        # Add lines and legend
        self.predict_line, = self.graph_predict.plot([], [], color='0.75', label='Prediction')
        self.target_line, = self.graph_predict.plot([], [], color='red', linestyle='--', label='Target')
        self.error_line, = self.graph_error.plot([], [], color='red', label='Error')

        self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        self.graph_error.legend(handles=[self.error_line])

        #self.graph_predict.set_title("Prediction vs. Target")
        self.graph_predict.set_ylabel("Power (Watts)")

        #self.graph_error.set_title("Error")
        self.graph_error.set_xlabel("Time")
        self.graph_error.set_ylabel("Error (Watts)")

        plt.subplots_adjust(hspace = 0.3)

        self.canvas = FigureCanvasTkAgg(fig, master=self.graphFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().grid(sticky=N+S+W+E) #fill='both', expand=True)
        
        plt.tight_layout()
        
        Button(self.graphFrame, 
               text="Refresh Graph", 
               bg='green', 
               command=self.refreshGraph,
               height=1,
              ).grid(sticky=W+E) #fill='both', expand=True)
        

    def createDashFrame(self):
        
        self.dashFrame = Frame(self)
        self.dashFrame.pack(side='left', padx=10, pady=10, fill='both')
        Label(self.dashFrame, text="NextHome Dashboard", font=('bold')).grid(pady=10)
        
        # Timer and power
        self.curtime = int(time.time())
        self.timer = Label(self.dashFrame, text="Current time:\t")
        self.timer.grid(sticky=W)
        self.power = Label(self.dashFrame, text="Current usage:\t30.126 kW")
        self.power.grid(sticky=W)
        self.after(200, self.updateTime)
        
        # Gap row
        Label(self.dashFrame, text="").grid()

        # Settings
        Label(self.dashFrame, text="Settings", font=('bold')).grid(sticky=W)
        self.datafile = "results.csv"
        self.update_rate = 60
        self.update_rateLabel = Label(self.dashFrame, text="Update rate:\t60 seconds")
        self.update_rateLabel.grid(sticky=W)
        self.datafileLabel = Label(self.dashFrame, text="Data file:  \tresults.csv")
        self.datafileLabel.grid(sticky=W)
        
        # Gap row
        Label(self.dashFrame, text="").grid()
        
        # Settings button
        Button(self.dashFrame, text="Change settings", command=self.changeSettings).grid()
        
        
    ####################  CONSTRUCTOR  ####################

    def __init__(self, master=None):
    
        self.counter = 0
    
        Frame.__init__(self, master)
            
        # Frame which contains power and error graphs
        self.createGraphFrame()
        
        # Contains the dashboard, including time, power, and settings
        self.createDashFrame()
        
        self.pack(fill='both', expand=True)

        
# Execute the application
root = Tk()
root.wm_title("NextHome Energy Analysis")               # Change title
icon_file = PhotoImage(file = "merit_icon.ppm")         # Change icon
root.tk.call( 'wm', 'iconphoto', root._w, icon_file )

def close_window():
    root.destroy()
    sys.exit(0)

# Make sure if program exits with error that memory is cleaned properly
try:
    app = App(master=root)
    root.protocol("WM_DELETE_WINDOW", close_window)
    app.mainloop()
except KeyboardInterrupt:
    print "Exiting on keyboard interrrupt"
    close_window()
except Exception as e:
    print repr(e)
    close_window()
