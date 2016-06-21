#!/usr/bin/python -d

#############################################
########## NextEnergy BLR Analysis ##########
#############################################

# Filename:     pi_seq_BLR_AVG.py
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
from grapher import CSV, DATE_FORMAT
from algoRunFunctions import train, severityMetric
from get_data import get_data, get_power
from zwave_api import ZWave
import pickle 

############################################################

#if __name__ == "__main__":

print "Loading configuration settings..."


np.set_printoptions(precision=3, linewidth=200)


##### PARAMETERS #####
XLOG_FILENAME = "X_DATA.bak"
Xog_LOG_FILENAME = "Xog_DATA.bak"
RESULTS = 'results.csv'
SECS_PER_MIN = 60
MINS_PER_HOUR = 60
HOURS_PER_DAT = 24

# Logging analysis results
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
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
logged_Xog = np.zeros([1,1])
try:
    logged_Xdata = pickle.load(open(XLOG_FILENAME, "r"))
    logged_Xog = pickle.load(open(Xog_LOG_FILENAME,"r"))
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
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
sigma_w = np.sqrt(w/(2-w))
THRESHOLD = L * sigma_w
Sn_1 = 0
init_training = False
alert_counter = 0

# num_sensors           -> Number of sensors in ZWave network
# matrix_length         -> Number of rows in data matrix (X)
# forecasting_interval  -> Time between training sessions
# granularity           -> Time between sensor measurements

num_sensors = len(ZServer.get_data_keys())#+1 #for noise detection
matrix_length = int(sys.argv[2])*60/int(sys.argv[1])
forecasting_interval = int(sys.argv[3])*60/int(sys.argv[1])
granularity_in_seconds = int(sys.argv[1])*60

logging.info("Starting program with settings: %s %s %s" % (sys.argv[1], sys.argv[2], sys.argv[3]))

# X is the matrix containing the training data
Avg_over = 5
X = np.zeros([matrix_length, num_sensors+1]) #sensors, energy reading
X_og = np.zeros([Avg_over,num_sensors+1])
# Use the previous X matrix to save time, if available 
# Make sure logged_Xdata is the proper size
if np.shape(logged_Xdata) == (matrix_length, num_sensors+1) and np.shape(logged_Xog) == (Avg_over, num_sensors+1):
    print "sizes: logged, mat, num", np.shape(logged_Xdata), matrix_length, num_sensors+1
    X = logged_Xdata
    X_og = logged_Xog
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

csv = CSV(RESULTS)
csv.clear()

y_time = []
y_target = []
y_predict = []

# Prepare the timer
goal_time = time.time()
#goal_time = goal_time - (goal_time % 60)

while True:

    # Wake up periodically to check time
    while goal_time > time.time():
        time.sleep(0.1)

    # Record the time of the next iteration
    cur_time = goal_time
    goal_time += granularity_in_seconds

    #if __debug__:
    print "\nTrying time", dt.datetime.now().strftime(DATE_FORMAT)

    # Retrieve sensor data from ZServer
    try:
        new_data = get_data(ZServer)
    except Exception:
        print "KILLED"
        logging.error("ZServer Connection Lost. Ending analysis.")
        exit(1)
        logging.error("Exit(1) failed to end program.")
        print "exit failed"

    #get current energy reading
    cur_row = (row_count) % matrix_length
    og_row = row_count % Avg_over
    T_Power =  float(get_power(config_dict))
    X[cur_row][num_sensors] = T_Power
    X_og[og_row][num_sensors] = T_Power
    
    #Update X - new_data[0] contains a timestamp we don't need
    for i in range(1, num_sensors + 1):
        #We have new valid data! Also update last_data
        print "{}: {}".format(ZServer_devices[i-1], new_data[i], len(new_data), i, num_sensors)

        if row_count > 4:
           Avg_last_mat = X_og[0:,i-1]
           sum_last_5 = sum(Avg_last_mat)
           Avg_last_5 = (sum_last_5 + new_data[i])/6 #5 pervious points plus current point = 6
           X[cur_row][i-1] = Avg_last_5
        else:        
            X[cur_row][i-1] = new_data[i]
 
        X_og[og_row][i-1] = new_data[i]

        '''
        if new_data[i] == last_data[i-1]:
            last_data_count[i-1] += 1
        else:
            last_data[i-1] = new_data[i]
            last_data_count[i-1] = 0
        '''
    print "X_og: \n",X_og
    print "X: \n",X[cur_row]
    
    # Train the model
    if (row_count % forecasting_interval == 0 and
        (row_count >= matrix_length or init_training)):

        # Unwrap the matrices (put the most recent data on the bottom)
        data = X[cur_row:, :num_sensors]
        data = np.concatenate((data, X[:cur_row, :num_sensors]), axis=0)
        y = X[cur_row:, num_sensors]
        y = np.concatenate((y, X[:cur_row, num_sensors]), axis=0)

        # BLR train:
        w_opt, a_opt, b_opt, S_N = train(data, y)

        init_training = True

        # Log current training windows as pickle files
        with open(XLOG_FILENAME, 'w') as logfile:
            pickle.dump(X, logfile)
        with open(Xog_LOG_FILENAME, 'w') as logfile:
            pickle.dump(X_og, logfile)
        
    # Make a prediction
    if init_training:

        # Prediction is dot product of data and weights
        x_n = X[(row_count) % matrix_length][:num_sensors]
        print "w_opt,\n", w_opt
        actual_prediction = np.inner(w_opt, x_n)
	prediction = max(0, actual_prediction)
        target = X[(row_count) % matrix_length][num_sensors]

        #log the new result
        logging.info("Target: " + str(target) + ",  Prediction: " + str(prediction))

        # Not currently used but will be necessary to flag user:
        error = (prediction-target)
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_n),np.dot(S_N, x_n)))

	y_target.append(target)
	y_predict.append(prediction)
	y_time.append(cur_time)

	# Achieve scrolling effect by only writing most recent data
        if len(y_time) >= matrix_length:

            y_time = y_time[-matrix_length:]
            y_target = y_target[-matrix_length:]
            y_predict = y_predict[-matrix_length:]

            csv.clear()
            csv.append(y_time, y_target, y_predict)
        else:
            csv.append(y_time[-1:], y_target[-1:], y_predict[-1:])

	print "Target:", target, 
	print "Prediction:", prediction
        if (actual_prediction < 0):
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
            ##COMMENTED OUT ALERT_COUNTER
            logging.error("ANOMALY FOUND!")
            if __debug__:
                print "ERROR: ANOMALY"

        Sn_1 = Sn

    row_count += 1
