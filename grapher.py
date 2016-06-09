#!/usr/bin/python

# Grapher class for plotting target and prediction values
# Filename:     grapher.py
# Author(s):    apadin
# Start Date:   5/13/2016

import argparse
import pickle
import time
import datetime as dt
import numpy as np
from algoRunFunctions import movingAverage
from threading import Thread

from Tkinter import * # GUI Library
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


##############################  DEFINITIONS  ##############################
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_FILE = 'results.csv'
icon_file = 'app/merit_icon.ppm'


##############################  HELPER FUNCTIONS  ##############################

# Wrapper function for consistent time formatting
def time2string(timestamp):
    return dt.datetime.fromtimestamp(timestamp).strftime(DATE_FORMAT)

# Give the window a title and icon, destroy cleanly when X is pressed
def initWindow(window, title=" "):
    window.wm_title(title)                              # Change title
    icon = PhotoImage(file = icon_file)                 # Change icon
    window.tk.call('wm', 'iconphoto', window._w, icon)

    def quit_and_destroy(window):
        window.quit()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", lambda: quit_and_destroy(window))
    

##############################  GRAPHER CLASS  ##############################
class Grapher(Frame):

    # Constructor
    def __init__(self, master=None):

        Frame.__init__(self, master)
        Grid.rowconfigure(self, 0, weight=1)
        Grid.columnconfigure(self, 0, weight=1)

        # Create figure and add subplots
        fig = plt.figure()
        self.graph_predict = fig.add_subplot(211) # Target versus prediction
        self.graph_error = fig.add_subplot(212) # Error (target - prediction)

        # Set titles and axis labels for both graphs
        #fig.suptitle("Sequential BLR: Prediction and Error", fontsize=18)
        
        #self.graph_predict.set_title("Prediction vs. Target")
        self.graph_predict.set_xlabel("Time")
        self.graph_predict.set_ylabel("Power (Watts)")

        #self.graph_error.set_title("Error (Prediction minus Target)")
        self.graph_error.set_xlabel("Time")
        self.graph_error.set_ylabel("Error (Watts)")

        # Sets the x-axis to only show hours, minutes, and seconds of time
        self.graph_predict.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M:%S"))
        self.graph_error.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M:%S"))

        # Sets the x-axis to only show 6 tick marks
        self.graph_predict.xaxis.set_major_locator(LinearLocator(numticks=6))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=6))
        
        # Spacing between subplots (changes depending on labels
        plt.subplots_adjust(hspace = 0.3)
        #plt.subplots_adjust(top = 0.87, hspace = 0.5)

        # Add lines and legend
        x, y = [1, 2], [0, 0]
        self.predict_line, = self.graph_predict.plot(x, y, color='0.75')
        self.target_line, = self.graph_predict.plot(x, y, color='red', linestyle='--')
        self.error_line, = self.graph_error.plot(x, y, color='red')

        #self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        #self.graph_error.legend(handles=[self.error_line])
        self.graph_predict.legend([self.target_line, self.predict_line], ["Target", "Prediction"])
        self.graph_error.legend([self.error_line], ["Error"])

        labels = self.graph_predict.get_xticklabels()
        plt.setp(labels, rotation=10)
        labels = self.graph_error.get_xticklabels()
        plt.setp(labels, rotation=10)

        # Tk canvas which is embedded into application
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(side='bottom', fill='both', expand=True)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=True)
        #self.canvas.show()

        
    # Plot the data
    def graph(self, y_time, y_target, y_predict):

        # Time could be datetime string or UNIX timestamp
        if isinstance(y_time[0], str):
            y_time = [dt.datetime.strptime(t, DATE_FORMAT) for t in y_time]
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
        #self.graph_error.set_ylim(-1000, 1000)

        # Set new data and graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)

        labels = self.graph_predict.get_xticklabels()
        plt.setp(labels, rotation=10)
        labels = self.graph_error.get_xticklabels()
        plt.setp(labels, rotation=10)

        plt.tight_layout()
        self.canvas.show()


##############################  CSV CLASS  ##############################
class CSV:

    # Constructor
    def __init__(self, datafile = DEFAULT_FILE):
        
        self.datafile = datafile
        
    # Reset the CSV and write the header
    # Deletes all previous data in the file
    def clear(self):
        
        file = open(self.datafile, 'wb')
        file.write('Time,Target,Prediction\n') # write the header first
        file.close()


    # Append given data to the CSV file
    def append(self, y_time, y_target, y_predict):
        
        file = open(self.datafile, 'ab')

        assert(len(y_time) == len(y_target))
        assert(len(y_time) == len(y_predict))

        # y_time should be a list of UNIX timestamps
        y_time = [time2string(t) for t in y_time]
        y_target = [str(t) for t in y_target]
        y_predict = [str(t) for t in y_predict]

        for i in xrange(len(y_time)):
            file.write(y_time[0] + y_target[0] + y_predict[0] + '\n')
        file.close()


    # Read the data in the CSV file and return results
    # Target and prediction are floats, time contains strings
    def read(self):

        file = open(self.datafile, "rb")
        file.next() # Throw out the header row

        y_time, y_target, y_predict = [], [], []

        for line in file:
            line = line.rstrip() #Remove newline
            data = line.split(',')

            # Only grow list if CSV was written properly
            if len(data) == 3:
                y_time.append(data[0])
                y_target.append(float(data[1]))
                y_predict.append(float(data[2]))

        file.close()

        # Remove last row if timestamp was corrupted
        try:
            dt.datetime.strptime(t, DATE_FORMAT)
        except:
            y_time = y_time[:-1]
            y_target = y_target[:-1]
            y_predict = y_predict[:-1]
    
        return y_time, y_target, y_predict

'''
# Store the given data in pickle files
def write_pickle(y_target, y_predict, y_time):

    file = open("y_target.bak", "wb")
    pickle.dump(y_target, file)
    file.close()

    file = open("y_predict.bak", "wb")
    pickle.dump(y_predict, file)
    file.close()

    file = open("y_time.bak", "wb")
    pickle.dump(y_time, file)
    file.close()


# Read the given data in pickle files
def read_pickle():

    file = open("y_target.bak", "rb")
    y_target = pickle.load(file)
    file.close()

    file = open("y_predict.bak", "rb")
    y_predict = pickle.load(file)
    file.close()

    file = open("y_time.bak", "rb")
    y_time = pickle.load(file)
    file.close()

    return y_target, y_predict, y_time
'''

##############################  STATISTICS  ##############################

# Prediction Mean Squared Error
def print_stats(y_target, y_predict, smoothing_win=120):

    T = len(y_target)
    y_target = np.asarray(y_target)
    y_predict = np.asarray(y_predict)

    try:
        y_target_smoothed = movingAverage(y_target, smoothing_win)
        y_predict_smoothed = movingAverage(y_predict, smoothing_win)
    except ValueError as e:
        print repr(e)
        print "Error: Smoothing window cannot be larger than number of data points"
        y_target_smoothed = movingAverage(y_target, 1)
        y_predict_smoothed = movingAverage(y_predict, 1)

    # Prediction Mean Squared Error (smooth values)
    PMSE_score_smoothed = np.linalg.norm(y_target_smoothed-y_predict_smoothed)**2 / T
    # Prediction Mean Squared Error (raw values)
    PMSE_score = np.linalg.norm(y_target - y_predict)**2 / T
    # Relative Squared Error
    Re_MSE = np.linalg.norm(y_target-y_predict)**2 / np.linalg.norm(y_target)**2
    # Standardise Mean Squared Error
    SMSE =  np.linalg.norm(y_target-y_predict)**2 / T / np.var(y_target)

    print "---------------------------------------------------------------------------"
    print "%20s |%20s |%15s |%10s "  % ("RMSE-score (smoothed)", "RMSE-score (raw)", "Relative MSE", "SMSE")
    print "%20.2f  |%20.2f |%15.2f |%10.2f " % (np.sqrt(PMSE_score_smoothed), np.sqrt(PMSE_score), Re_MSE, SMSE)
    print "---------------------------------------------------------------------------"


##############################  MAIN  ##############################


# Driver for graphing at any time based on stored values
def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Graph data from a file using matplotlib tools.')

    ''' # Pickle format not currently supported
    parser.add_argument('-p', '--pickle', action='store_true',
                        help='read from a pickle file instead of CSV')
    '''
    
    parser.add_argument('-n', '--nograph', action='store_true',
                        help='show only statistics, no graph')
    parser.add_argument('-r', '--realtime', nargs='?',metavar = 'TIME', const=5000, type=int,
                        help='update the graph in real-time every TIME milliseconds (default 5)')
    parser.add_argument('-s', '--smooth', nargs='?', metavar='WINDOW', const=120, type=int,
                        help='smooth data with a smoothing window of WINDOW (default 120)')
    parser.add_argument('-f', '--file', metavar='FILE', type=str,
                        help='specify which file to read data from')
                        
    args = parser.parse_args()


    # Get the filename if -f was set
    if args.file != None:
        infile = args.file
    else:
        infile = "results.csv"

    # Create CSV instance
    csv = CSV(infile)

    # If -n set, show statistics and then exit cleanly
    if args.nograph:

        print "Statistics:"
        t_time, y_target, y_predict = csv.read()
        print_stats(y_target, y_predict)
        exit(0)

    # Otherwise, create the graph
    root = Tk()
    initWindow(root, title="Sequential BLR Results")
    grapher = Grapher(master=root)
    grapher.pack(fill='both', expand=True)
    
    # Function to periodically (or once) update the graph
    def updateGraph(grapher, csv, smooth, period):

        # Attempt to read the files
        y_time, y_target, y_predict = csv.read()

        print "Statistics:"
        print_stats(y_target, y_predict)

        # Smooth data if requested
        if smooth > 0:
            y_target = movingAverage(y_target, args.smooth)
            y_predict = movingAverage(y_predict, args.smooth)

        print "Graphing at time", y_time[-1]
        grapher.graph(y_time, y_target, y_predict)

        # If running realtime, reschedule another update
        if period > 0.0:
            grapher.after(period, lambda: updateGraph(grapher, csv, smooth, period))
        else:
            print "\nClose window to exit"

    # Get the period if -r was set
    try:
        period = args.realtime
    except:
        period = 0

    # Smooth data if requested
    if args.smooth != None:
        smooth = args.smooth
    else:
        smooth = 0

    # Open the graph window
    try:
        updateGraph(grapher, csv, smooth, period)
        root.mainloop()
    except KeyboardInterrupt:
        print "Exiting on keyboard interrrupt"
        root.quit()
        root.destroy()

# If run as main:
if __name__ == "__main__":
    main()
