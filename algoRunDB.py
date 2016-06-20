# Run the algorithm using prepared data from a database
# Specifically designed to run Smart* Data
# Filename:     algoRun.py
# Author:       mjmor, dvorva, apadin
# Start Date:   ??? before 4/30/2016

print "Welcome to algoRun"

################################################################################

print "Preparing libraries..."

import time
import datetime as dt
import random

import grapher
from database import Database

import json
from urllib import urlopen

import numpy as np
import scipy as sp
import scipy.stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

from tf_functions import tf_train

from algoRunFunctions import movingAverage
from algoRunFunctions import train
from algoRunFunctions import runnable
from algoRunFunctions import severityMetric

from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score

import mysql.connector

################################################################################

print "Loading configuration settings..."

y_predictions = []
y_target = []
y_time = []
w_opt = []
a_opt = 0
b_opt = 0
rowCount = 0
initTraining = False
notRunnableCount = 0
mu = 0; sigma = 1000
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
Sn_1 = 0
p_array = []

# Initialize database
database = Database()

print "Reading configuration files..."
with open('smartDriver.json') as data_file:
    jsonDataFile = json.load(data_file)

#Period: length of forecasting window, in hours
#Granularity: time between data, in minutes
matrixLength = int(jsonDataFile["windowSize"])*60/int(jsonDataFile["granularity"])
forecastingInterval = int(jsonDataFile["forecastingInterval"])*60/int(jsonDataFile["granularity"])

inputIDs = jsonDataFile["idSelection"]
inputIDs = inputIDs.split(',')
idArray = []
#Create a list of ID numbers, given input.
#interprets 1-3 to include 1,2,3.
for selection in inputIDs:
    if '-' not in selection:
        idArray.append(int(selection))
    else:
        bounds = selection.split('-')
        for index in range(int(bounds[0]), int(bounds[1])+1):
            idArray.append(index)

#Remove duplicates:
idArray = list(set(idArray))

#Sort the list.
idArray.sort()

#Fill columns with the corresponding column, given IDarray.
#Invariant: the ID in idArray at a given index should correspond
#           to the columnName at the same index in the column list.
startTimeList = []
endTimeList = []
columns = []
lastData = [] #Data point of last valid timestamp - init garbage
lastDataTime = [] #Timestamp of last valid timestamp - init very old [TODO]
shouldBeRounded = []
countNoData = [] #fordebug
severityArray = []
for sensorID in idArray:
    if "circuit" in jsonDataFile["data"][sensorID-1]["columnName"]:
        shouldBeRounded.append(1)
    else:
        shouldBeRounded.append(0)
    columns.append(jsonDataFile["data"][sensorID-1]["columnName"])
    startTimeList.append(jsonDataFile["data"][sensorID-1]["startTime"])
    endTimeList.append(jsonDataFile["data"][sensorID-1]["endTime"])
    lastDataTime.append(dt.datetime.min)
    lastData.append(-1)
    countNoData.append(0) #fordebug

countNoData.append(0) #fordebug


# Add total energy consumption column:
columns.append(jsonDataFile["totalConsum"]);
lastData.append(-1)
shouldBeRounded.append(1)
lastDataTime.append(dt.datetime.min)

# Find latest start time, earliest end time.
startTime = dt.datetime.strptime(max(startTimeList), "%Y-%m-%d %H:%M:%S")
endTime = dt.datetime.strptime(min(endTimeList), "%Y-%m-%d %H:%M:%S")

if(int(jsonDataFile["specifyTime"])):
   startTime = dt.datetime.strptime(jsonDataFile["beginTime"], "%Y-%m-%d %H:%M:%S")
   endTime = dt.datetime.strptime(jsonDataFile["endTime"], "%Y-%m-%d %H:%M:%S")

granularityInSeconds = int(jsonDataFile["granularity"])*60

# Input data matrix
X =  np.zeros([matrixLength, len(columns)], np.float32)
X[:, -1] = np.ones([matrixLength], np.float32)
X = np.concatenate((X, np.zeros([matrixLength, 1], np.float32)), axis=1)

grapher.clear_csv()

################################################################################

print "Beginning analysis..."

while startTime < endTime:

    currentRow = (rowCount % matrixLength)

    #Some of the data seems bad on the 31st - too many NULLS
    if startTime > dt.datetime(2012, 5, 30) and startTime < dt.datetime(2012, 6, 1):
        startTime = dt.datetime(2012, 6, 1)

    if(rowCount % 240 == 0):
        print "trying time: %s " % startTime

    #Execute the query:
    next_data = database.get_avg_data(startTime, startTime + dt.timedelta(0, granularityInSeconds), columns)
    next_data = [max(0, data) for data in next_data] # remove 'nan' and negative

    #X[currentRow, :-1] = next_data[:-1] #Sensor data
    X[currentRow, :-2] = next_data[:-1] #Sensor data
    X[currentRow, -1] = next_data[-1] #Power data

    # Time to train:
    if(rowCount % forecastingInterval == 0 and rowCount >= matrixLength):
        data = X[(currentRow+1):, :-1]
        data = np.concatenate((data, X[:(currentRow+1), :-1]), axis=0)
        y = X[(currentRow+1):, -1]
        y = np.concatenate((y, X[:(currentRow+1), -1]), axis=0)

        if(initTraining or runnable(data) > 0.5):

            # For BLR
            w_opt, a_opt, b_opt, S_N = train(data, y)

            # For TF train            
            #w_opt, a_opt, b_opt, S_N = tf_train(data, y)

            #print w_opt

            initTraining = 1

        else:
            notRunnableCount += 1
            if(notRunnableCount > 5):
                print "Data not runnable too many times! Exiting..."

    # If enough data has been gathered, make a prediction
    if(initTraining):
        x_n = X[currentRow, :-1]
        prediction = max(0, np.inner(w_opt,x_n))

        if prediction > 12000:
            print "WARNING: IMPOSSIBLE PREDICTION. Correcting now..."
            prediction = y_predictions[-1]

        y_predictions.append(prediction)
        y_target.append(X[currentRow, -1])
        y_time.append(startTime)

        error = y_predictions[-1] - y_target[-1]
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_n),np.dot(S_N, x_n)))

        # Catching pathogenic cases where variance (ie, sigma) gets too small
        sigma = max(sigma, 1.0)

        # Update severity metric
        mu = mu; sigma = sigma
        Sn, Zn = severityMetric(error, mu, sigma, w, Sn_1)
        severityArray.append(Sn)
        #Zscore_array[n] = Zn
        Sn_1 = Sn
        p = 1 - sp.stats.norm.cdf(error, mu, sigma)
        p_array.append(p)

    # If not, no prediction is made
    else:
        severityArray.append(0)

    #Increment and loop
    startTime += dt.timedelta(0,granularityInSeconds)
    rowCount += 1

    # Save the data for later graphing
    if(rowCount % forecastingInterval == 0 and initTraining):        
        grapher.write_csv(y_target[-forecastingInterval:],
                          y_predictions[-forecastingInterval:],
                          y_time[-forecastingInterval:])


################################################################################

print "Analysis complete."

grapher.print_stats(y_target, y_predictions, 120)
