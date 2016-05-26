#!/usr/bin/python -O

#############################################
########## NextEnergy BLR Analysis ##########
#############################################

# Filename:     pi_seq_BLR.py
# Author(s):    dvorva, apadin, yabskbd
# Start Date:   5/9/2016
version_number = 1.0

print "\n\n##### NextEnergy Electricity Usage Analysis #####"
print "Version: ", version_number, "\n"

if __debug__:
    print "Running in debug mode...\n"
else:
    print "Starting program...\n"

# Checking command-line input
import sys
if len(sys.argv) != 4:
    print """Error: usage: python""", sys.argv[0], """ <granularity>
            <window size> <forecasting interval>"""
    print "Where granularity is the frequency of data collection, in minutes"
    print "Where window size is the amount of remembered data, in hours"
    print "Where forecasting interval is the time between trainings, in hours"
    exit(1)


############################################################

print "Initializing libraries..."

import datetime as dt
import json
import logging
import time
import numpy as np
import grapher
from algoRunFunctions import train, severityMetric
from get_data import get_data, get_power
from zwave_api import ZWave


############################################################

#if __name__ == "__main__":

print "Loading configuration settings..."

##### PARAMETERS #####
XLOG_FILENAME = "X_data.bak"
SECS_PER_MIN = 60
MINS_PER_HOUR = 60
HOURS_PER_DAT = 24

# Logging analysis results
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
logging.basicConfig(filename='/var/log/sequential_predictions.log',
                    level=logging.DEBUG,
                    format=FORMAT,
                    datefmt=DATE_FORMAT)

# Set up ZWave server here using zwave_api and config file
with open("./config/config.json") as config_fh:
    config_dict = json.load(config_fh)
with open("./config/sensors.json") as device_fh:
    device_dict = json.load(device_fh)
ZServer = ZWave(config_dict["z_way_server"]["host"],
                config_dict["z_way_server"]["port"],
                device_dict)
ZServer_devices = ZServer.list_devices()
print ZServer_devices
# Load the previous training window
logged_Xdata = np.zeros([1, 1])
try:
    logged_Xdata = pickle.load(open(XLOG_FILENAME, "r"))
    print "Training backup file found..."
except IOError:
    print "***WARNING: No training backup found.***"


############################################################

## VARIABLE INITIALIZATION ##

# Training statistics:
w_opt = []
a_opt = 0
b_opt = 0
mu = 0
sigma = 1000
THRESHOLD = 100000 #TODO, set this
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
Sn_1 = 0
init_training = False
alert_counter = 0

# num_sensors           -> Number of sensors in ZWave network
# matrix_length         -> Number of rows in data matrix (X)
# forecasting_interval  -> Time between training sessions
# granularity           -> Time between sensor measurements

num_sensors = len(ZServer.get_data_keys())
matrix_length = int(sys.argv[2])*60/int(sys.argv[1])
forecasting_interval = int(sys.argv[3])*60/int(sys.argv[1])
granularity_in_seconds = int(sys.argv[1])*60

# X is the matrix containing the training data
X = np.zeros([matrix_length, num_sensors+1]) #sensors, energy reading

# Use the previous X matrix to save time, if available 
# Make sure logged_Xdata is the proper size
if np.shape(logged_Xdata) == (matrix_length, num_sensors+1):
    print "sizes: logged, mat, num", np.shape(logged_Xdata), matrix_length, num_sensors+1
    X = logged_Xdata
    init_training = True
else:
    print "Unable to use training backup. Continuing analysis without backup..."

y = [None]*matrix_length

# Keep track of number of times the same data has been repeated
# TODO: Add logic to not use data if it is repeated too many times
#       This is caused by sensors that have been turned off but report the same data
last_data = [0]*num_sensors         # Last data
last_data_count = [0]*num_sensors   # Number of polls since change of data
last_data_threshold = 10            # Max number of polls to tolerate

############################################################

print "Starting analysis..."

row_count = 0

# Allign time to the second
goal_time = float(int(time.time() + 1.0))
time.sleep(goal_time-time.time())

y_time = []
y_target = []
y_predict = []

while True:

    # Record the time of the next iteration
    goal_time += granularity_in_seconds
    #if __debug__:
    print "\nTrying time", dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    if (not row_count % 200) and __debug__:
        print "Row count: %s" % row_count

    #get new data from pi
    # TODO: Add try catch block here around get_data in case connection to
    # server fails then log failure to log file above
    new_data = get_data(ZServer)

    #get current energy reading
    X[row_count % matrix_length][num_sensors] = get_power(config_dict)

    #Update X - new_data[0] contains a timestamp we don't need
    for i in range(1, num_sensors + 1):
        #We have new valid data! Also update last_data
        print "{}: {}".format(ZServer_devices[i-1], new_data[i], len(new_data), i, num_sensors)
        X[(row_count) % matrix_length][i-1] = new_data[i]
        if new_data[i] == last_data[i-1]:
            last_data_count[i-1] += 1
        else:
            last_data[i-1] = new_data[i]
            last_data_count[i-1] = 0

    # Time to train:
    if (row_count % forecasting_interval == 0
            and (row_count >= matrix_length or init_training)):
        #unwrap the matrices
        data = X[(row_count % matrix_length):,:num_sensors]
        data = np.concatenate((data, X[0:(row_count % matrix_length), :num_sensors]), axis=0)
        y = X[(row_count % matrix_length):, num_sensors]
        y = np.concatenate((y, X[:(row_count % matrix_length), num_sensors]), axis=0)

        w_opt, a_opt, b_opt, S_N = train(data, y)
        init_training = 1
        pickle.dump(X, open(XLOG_FILENAME, "w"))

    #make prediction:
    if init_training:
        x_n = X[(row_count) % matrix_length][:num_sensors]
        print "w_opt, x_n",w_opt,x_n
        actual_prediction = np.inner(w_opt, x_n)
	prediction = max(0, actual_prediction)
        target = X[(row_count) % matrix_length][num_sensors]

        #log the new result
        logging.info((dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                      + " " + str(target) + " " + str(prediction)))

        if __debug__:
            print (dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                   + " " + str(target) + " " + str(prediction))

        #eot currently used but will be necessary to flag user:
        error = (prediction-target)
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_n),np.dot(S_N, x_n)))

	y_target.append(target)
	y_predict.append(prediction)
	y_time.append(goal_time)
	
	print "Time:", dt.datetime.fromtimestamp(goal_time).strftime('%Y-%m-%d %H:%M:%S')
	print "Target:", target, 
	print "Prediction:", prediction
	print "Actual Predict:", actual_prediction

        # Catching pathogenic cases where variance (ie, sigma)
        # gets really really small
        if sigma < 1:
            sigma = 1

        # Update severity metric
        mu = mu; sigma = sigma
        Sn, Zn = severityMetric(error, mu, sigma, w, Sn_1)

        #flag the user if necessary (error is greater than allowance)
        #two-in-a-row counter, much like branch prediction
        if np.abs(Sn) <= THRESHOLD:
            alert_counter = 0
        elif np.abs(Sn) > THRESHOLD and alert_counter == 0:
            alert_counter = 1
            Sn = Sn_1
        elif np.abs(Sn) > THRESHOLD and alert_counter == 1:
            Sn = 0
            alert_counter = 0
            logging.error("ANOMALY FOUND!")
            if __debug__:
                print "ERROR: ANOMALY"

        Sn_1 = Sn

    row_count += 1

    # If trained, write results for graphing
    if(init_training):
        
        grapher.write_csv(y_target, y_predict, y_time)
    
    # Sleeping approximation (takes approx. 0.01 seconds to run)
    try:
        time.sleep(goal_time - time.time() - 0.01)
    except ValueError:
        if __debug___:
            print "**WARNING: Skipping sleeping due to timing issues.***"

