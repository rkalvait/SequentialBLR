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
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D

data_file = "results.csv"


############################## GRAPHER CLASS ##############################

class Grapher:

    # Constructor
    def __init__(self):

        plt.ion() # Allows interactice session, animate the graph

        # Create figure and added main title
        fig = plt.figure()
        fig.suptitle("Sequential BLR: Prediction and Error", fontsize=18)

        self.graph_predict = fig.add_subplot(211) # Target versus prediction
        self.graph_error = fig.add_subplot(212) # Error (target - prediction)

        # Set titles and axis labels for both graphs
        self.graph_predict.set_title("Prediction vs. Target")
        self.graph_predict.set_xlabel("Time")
        self.graph_predict.set_ylabel("Power (Watts)")

        self.graph_error.set_title("Error (Prediction minus Target)")
        self.graph_error.set_xlabel("Time")
        self.graph_error.set_ylabel("Error (Watts)")

        plt.subplots_adjust(top = 0.87, hspace = 0.5)

        # Sets the x-axis to only show hours, minutes, and seconds of time
        self.graph_predict.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M:%S"))
        self.graph_error.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M:%S"))

        # Sets the x-axis to only show 6 tick marks
        self.graph_predict.xaxis.set_major_locator(LinearLocator(numticks=6))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=6))

        # Add lines and legend
        self.predict_line, = self.graph_predict.plot([], [], color='0.75', label='Prediction')
        self.target_line, = self.graph_predict.plot([], [], color='red', linestyle='--', label='Target')
        self.error_line, = self.graph_error.plot([], [], color='red', label='Error')

        self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        self.graph_error.legend(handles=[self.error_line])


    # Plot the data
    def graph_data(self, y_target, y_predict, y_time):

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
        #self.graph_error.set_ylim(-1000, 1000)

        # Set new data (automatically updates the graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)


############################## READ/WRITE FILE ##############################

# Reset the CSV and write the header
# Deletes all previous data in the file
def clear_csv():

    file = open(data_file, "wb")
    file.write('Target, Prediction, Time\n') # write the header first
    file.close()


# Append given data to the CSV file
def write_csv(y_target, y_predict, y_time):

    file = open(data_file, "ab")

    for i in xrange(len(y_target)):
        file.write(str(y_target[i]) + ',' + str(y_predict[i]) + ',' + str(y_time[i]) + '\n')

    file.close()


# Read the data in the CSV file and return results
def read_csv():

    file = open(data_file, "rb")

    file.next() # Throw out the header row

    y_target, y_predict, y_time = [], [], []

    for line in file:
        data = line.split(',')

        # Only grow list if CSV was written properly
        if len(data) == 3:
            y_target.append(float(data[0]))
            y_predict.append(float(data[1]))
            y_time.append(data[2])

    file.close()

    # Remove last row if timestamp was corrupted
    try:
        dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S\n")
    except:
        y_target = y_target[:-1]
        y_predict = y_predict[:-1]
        y_time = y_time[:-1]

    return y_target, y_predict, y_time


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


############################## STATISTICS ##############################

# Prediction Mean Squared Error
def print_stats(y_target, y_predict, smoothing_win=120):

    T = len(y_target)
    y_target = np.asarray(y_target)
    y_predict = np.asarray(y_predict)
    y_target_smoothed = movingAverage(y_target, smoothing_win)
    y_predict_smoothed = movingAverage(y_predict, smoothing_win)

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


############################## MAIN ##############################


# Driver for graphing at any time based on stored values
def main():

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Graph data from a file using matplotlib tools.')


    parser.add_argument('-p', '--pickle', action='store_true',
                        help='read from a pickle file instead of CSV')
    parser.add_argument('-n', '--nograph', action='store_true',
                        help='show only statistics, no graph')
    parser.add_argument('-r', '--realtime', nargs='?',metavar = 'TIME', const=5.0, type=float,
                        help='update the graph in real-time every TIME seconds (default 5)')
    parser.add_argument('-s', '--smooth', nargs='?', metavar='WINDOW', const=120.0, type=float,
                        help='smooth data with a smoothing window of WINDOW (default 120)')

    args = parser.parse_args()

    try:
        period = float(args.realtime)
    except:
        period = 0.0

    # Create grapher instance for graphing data
    if not args.nograph:
        grapher = Grapher()

    # Allign the timer
    goal_time = float(int(time.time() + 1.0))
    time.sleep(goal_time-time.time())

    while True:

        goal_time += period

        # Attempt to read the files
        if args.pickle:
            y_target, y_predict, y_time = read_pickle()
        else:
            y_target, y_predict, y_time = read_csv()

        # Make sure the files were written properly and are the same length
        assert len(y_target) == len(y_predict)
        assert len(y_target) == len(y_time)

        # Print statistics
        print "Statistics:"
        print_stats(y_target, y_predict)

        if args.nograph:
            return(0)

        # Smooth data if requested
        if args.smooth != None:
            y_target = movingAverage(y_target, args.smooth)
            y_predict = movingAverage(y_predict, args.smooth)

        print "Graphing at time", y_time[-1]
        grapher.graph_data(y_target, y_predict, y_time)

        # If not continuous, stop here
        if period == 0.0:
            print "Close figure to exit"
            plt.show(block=True)
            break

        # Catch error of sleeping for a negative time
        sleep_time = goal_time - time.time()
        if (sleep_time > 0):
            plt.pause(sleep_time)

if __name__ == "__main__":
    main()
