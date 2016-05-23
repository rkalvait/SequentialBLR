# Run the algorithm using prepared data from a database
# Specifically designed to run Smart* Data
# Filename:     algoRun.py
# Author:       mjmor, dvorva, apadin
# Start Date:   ??? before 4/30/2016

print "Welcome to algoRun"

################################################################################

print "Preparing libraries..."

import mysql.connector
from urllib import urlopen
import json
import numpy as np
import datetime as dt
import time
from tf_functions import tf_train
from algoRunFunctions import movingAverage
from algoRunFunctions import train
from algoRunFunctions import runnable
from algoRunFunctions import severityMetric
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score
from datetime import date
import random
import scipy as sp
import scipy.stats
import pickle
import subprocess

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

################################################################################

print "Loading configuration settings..."

# Database settings
with open('config.txt') as f:
    for line in f:
        if line.startswith('HOST'):
            loc = line.find('=')
            hst = line[loc+1:].rstrip()
        elif line.startswith('DATABASE'):
            loc = line.find('=')
            db = line[loc+1:].rstrip()
        elif line.startswith('USER'):
            loc = line.find('=')
            usr = line[loc+1:].rstrip()
        elif line.startswith('PASSWORD'):
            loc = line.find('=')
            pswd = line[loc+1:].rstrip()

# Database config struct
config = {
    'user': usr,
    'password': pswd,
    'host': hst,
    'database': db,
    'raise_on_warnings': True
}

print "Connecting to database..."
cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()

# Algorithm settings
with open('smartDriver.json') as data_file:
    jsonDataFile = json.load(data_file)

# From JSON file:
# forecastingInterval: time between trainings, in hours
# windowSize: amount of data to train from, in hours
# granularity: time between data points, in minutes
intervalHours = int(jsonDataFile["forecastingInterval"])
windowHours = int(jsonDataFile["windowSize"])
granularityMinutes = int(jsonDataFile["granularity"])

# Number of rows in X and y data matrices
# e.g., 24 hour window * (60 minutes / 1 minute granularity) = 1440 rows
numRows = windowHours * (60 / granularityMinutes)

# Number of iterations between training
trainingInterval = intervalHours * (60 / granularityMinutes)

# List of sensor IDs
inputIDs = jsonDataFile["idSelection"]
inputIDs = inputIDs.split(',')
idArray = []

# Create a list of ID numbers, given input
for selection in inputIDs:

    # Interprets 1-3 to include 1,2,3
    if '-' not in selection:
        idArray.append(int(selection))
    else:
        bounds = selection.split('-')
        for index in range(int(bounds[0]), int(bounds[1])+1):
            idArray.append(index)

idArray = list(set(idArray))  # Remove duplicates
idArray.sort()                # Sort the list

# Fill columns with the corresponding column of data, given IDarray.
# Invariant: the ID in idArray at a given index should correspond
#            to the columnName at the same index in the column list.
startTimeList = []
endTimeList = []
columns = []
lastData = []      #Data point of last valid timestamp - init garbage
lastDataTime = []  #Timestamp of last valid timestamp - init very old [TODO]
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

# This will be the number of columns in the X_data array
numFeatures = len(columns)

#Add total energy consumption column:
columns.append(jsonDataFile["totalConsum"]);
lastData.append(-1)
shouldBeRounded.append(1)
lastDataTime.append(dt.datetime.min)

#Find latest start time, earliest end time.
startTime = dt.datetime.strptime(max(startTimeList), "%Y-%m-%d %H:%M:%S")
endTime = dt.datetime.strptime(min(endTimeList), "%Y-%m-%d %H:%M:%S")

if(int(jsonDataFile["specifyTime"])):
   startTime = dt.datetime.strptime(jsonDataFile["beginTime"], "%Y-%m-%d %H:%M:%S")
   endTime = dt.datetime.strptime(jsonDataFile["endTime"], "%Y-%m-%d %H:%M:%S")

granularityInSeconds = granularityMinutes*60

################################################################################

print "Beginning analysis..."

# Result vectors
y_predictions = []
y_target = []
y_time = []

# Training results
w_opt = []
a_opt = 0
b_opt = 0

# Other variables
initTraining = False
notRunnableCount = 0
mu = 0; sigma = 1000
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
Sn_1 = 0
p_array = []

# Data matrices
X_data =  np.zeros([numRows, numFeatures], np.float32)           # Sensor data
#X_data = np.concatenate((X_data, np.ones([numRows, 1], np.float32)), axis=1)  # Ones for intercept

y_data = [None]*numRows
X_time =  [None]*numRows

# Iteration number
rowCount = 0

while startTime < endTime:

    rowNumber = rowCount % numRows # curent row in data matrices

    # Skip May 31st - some of the data seems bad, too many NULLS
    if startTime > dt.datetime(2012, 5, 30) and startTime < dt.datetime(2012, 6, 1):
        startTime = dt.datetime(2012, 6, 1)

    # Debug
    if(rowCount % 240 == 0):
        print "trying time: %s " % startTime

    # Build the query:
    isFirst = True
    qry = "SELECT "
    for column in columns:
        if not isFirst:
            qry += ", "
        else:
            isFirst = False
        qry = qry + column

    qry = qry + " FROM SMART WHERE dataTime BETWEEN %s AND %s"

    # Execute the query:
    cursor.execute(qry , (startTime, startTime + dt.timedelta(0,granularityInSeconds)))

    # Get the average in the queried window:
    # TODO: should probably switch this to be done by qry
    colSum = np.zeros(len(columns))
    colCount = np.zeros(len(columns))
    for row in cursor:
        feature = 0
        for columnData in row:
            if columnData is not None:
                if shouldBeRounded[feature] == 1 and columnData < 0:
                    columnData = 0
                colSum[feature] += columnData
                colCount[feature] += 1
            feature += 1

    # Update X_data, y_data, X_time
    X_time[rowNumber] = startTime

    # X_data contains sensor data, i.e. columns[] from 1 to len(columns)-1
    # **Note that the last column of columns is power data, this will go into y_data
    for feature in range(numFeatures):
        
        # Data is valid: add to X_data and lastData
        if colSum[feature] > 0:
            if "motion" in columns[feature]:
                X_data[rowNumber][feature] = colSum[feature]
                lastData[feature] = colSum[feature]
            else:
                X_data[rowNumber][feature] = colSum[feature] / colCount[feature]
                lastData[feature] = colSum[feature] / colCount[feature]

            lastDataTime[feature] = startTime
            
        # No new data.
        else:
            #X[rowNumber][feature] = lastData[feature]
            X_data[rowNumber][feature] = 0
            countNoData[feature] += 1

    # Last column is power data
    if colCount[-1] > 0:
        y_data[rowNumber] = colSum[-1] / colCount[-1]
    else:
        y_data[rowNumber] = 0

    # Check if ready to train:
    if(rowCount % trainingInterval == 0 and rowCount >= numRows):

        # If data is runnable, train
        if(initTraining or runnable(X_data[:][:numFeatures]) > 0.5):

            # Uncomment for BLR train
            #w_opt, a_opt, b_opt, S_N = train(X_data, y_data)

            # Uncomment for TF train            
            w_opt, a_opt, b_opt, S_N = tf_train(X_data, y_data)
            
            initTraining = True     # From now on, always train and make predictions

        # If data is not runnable, make a note
        else:
            notRunnableCount += 1
            if(notRunnableCount > 5):
                print "Data not runnable too many times! Exiting..."

    # Make prediction:
    if initTraining:

        # Prediction is dot product of X_test and w_opt
        x_test = X_data[rowNumber][:]
        prediction = max(0, np.inner(w_opt,x_test))

        #debug
        if prediction > 11000:
            '''
            print "WARNING!!!!"
            print X_data
            print y_data
            print prediction
            print x_test
            print w_opt
            raw_input("press enter")
            '''
            print "!!!!!WARNING!!!!! Large prediction, ignoring!"
            prediction = y_predictions[-1]
            
            
        y_predictions.append(prediction)
        y_target.append(y_data[rowNumber])
        y_time.append(X_time[rowNumber])
        
        error = y_predictions[-1]-y_target[-1]
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_test),np.dot(S_N, x_test)))

        # Catching pathogenic cases where variance (ie, sigma) gets too small
        if sigma < 1:
            sigma = 1

        # Update severity metric
        mu = mu; sigma = sigma
        Sn, Zn = severityMetric(error, mu, sigma, w, Sn_1)
        severityArray.append(Sn)
        #Zscore_array[n] = Zn
        Sn_1 = Sn
        p = 1 - sp.stats.norm.cdf(error, mu, sigma)
        p_array.append(p)

    # No prediction made
    else:
        severityArray.append(0)

    #Increment and loop
    startTime += dt.timedelta(0,granularityInSeconds)
    rowCount += 1

    # If recently trained, write results for graphing
    if(rowCount % trainingInterval == 0 and initTraining):
        
        # Write the pickled data for graphing
        file = open("y_time.bak", "wb")
        pickle.dump(y_time, file)
        file.close()
        
        file = open("y_target.bak", "wb")
        pickle.dump(y_target, file)
        file.close()

        file = open("y_predict.bak", "wb")
        pickle.dump(y_predictions, file)
        file.close()

        #nf_command = "rsync -arvz y_time.bak y_target.bak y_predict.bak blueberry:"
        #p = subprocess.Popen(nf_command, bufsize=-1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


################################################################################

print "Analysis complete."
print "Graphing and statistics..."

# Hereafter is just result reporting and graphing
# Prediction accuracy
n_samples = rowCount-1
training = int(jsonDataFile["windowSize"])*(60 / int(jsonDataFile["granularity"])) #init prediction period.
T = n_samples-training #prediction length
smoothing_win = 120
y_target = np.asarray(y_target)
y_predictions = np.asarray(y_predictions)
y_target_smoothed = movingAverage(y_target, smoothing_win)
y_predictions_smoothed = movingAverage(y_predictions, smoothing_win)
rmse_smoothed = []
rmse = []
Re_mse = []
smse = []
co95 = []

# Prediction Mean Squared Error (smooth values)

PMSE_score_smoothed = np.linalg.norm(y_target_smoothed-y_predictions_smoothed)**2 / T
# Prediction Mean Squared Error (raw values)
PMSE_score = np.linalg.norm(y_target - y_predictions)**2 / T

confidence = 1.96 / np.sqrt(T) *  np.std(np.abs(y_target-y_predictions))
# Relative Squared Error
Re_MSE = np.linalg.norm(y_target-y_predictions)**2 / np.linalg.norm(y_target)**2
# Standardise Mean Squared Error
SMSE =  np.linalg.norm(y_target-y_predictions)**2 / T / np.var(y_target)

rmse_smoothed.append(np.sqrt(PMSE_score_smoothed))
rmse.append(np.sqrt(PMSE_score))
co95.append(confidence)
Re_mse.append(Re_MSE)
smse.append(SMSE)


print "No data counts:"
print countNoData

print "PMSE for smoothed: %d" % (PMSE_score_smoothed)
print "PMSE for nonsmoothed: %d" % (PMSE_score)
print "-------------------------------------------------------------------------------------------------"
print "%20s |%20s |%25s |%20s" % ("RMSE-score (smoothed)", "RMSE-score (raw)", "Relative MSE", "SMSE")
print "%20.2f  |%20.2f |%25.2f |%20.2f " % (np.mean(np.asarray(rmse_smoothed)), np.mean(np.asarray(rmse)), np.mean(np.asarray(Re_mse)), np.mean(np.asarray(smse)))
print "-------------------------------------------------------------------------------------------------"

OBSERVS_PER_HR = 60 / int(jsonDataFile["granularity"])
axescolor  = '#f6f6f6'  # the axes background color
distance = n_samples//5
tick_pos = [t for t in range(distance,n_samples,distance)]
tick_labels = [y_time[t] for t in tick_pos]
GRAY = '#666666'

plt.rc('axes', grid=False)
plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)
textsize = 9
left, width = 0.1, 0.8
rect1 = [left, 0.7, width, 0.2]
rect2 = [left, 0.1, width, 0.5]

fig = plt.figure(facecolor='white')
axescolor  = '#f6f6f6'  # the axes background color
ax1 = fig.add_axes(rect1, axisbg=axescolor)  #left, bottom, width, height
ax2 = fig.add_axes(rect2, axisbg=axescolor, sharex=ax1)
y_target[:training] = 0
ax1.plot((movingAverage(y_predictions, smoothing_win) - movingAverage(y_target, smoothing_win)),"r-", lw=2)
ax1.set_yticks([-500, 0, 500])
ax1.set_yticklabels([-.5, 0, .5])
ax1.set_ylim(-1000, 1000)
ax1.set_ylabel("Error (KW)")
ax2.plot(movingAverage(y_predictions, smoothing_win),color=GRAY, lw=2, label = 'Prediction')
ax2.plot(movingAverage(y_target, smoothing_win), "r--", label = 'Target')
ax2.set_yticks([2000, 4000, 6000])
ax2.set_yticklabels([2, 4, 6])
ax2.set_ylabel("Power (KW)")
ax2.set_xlim(0,len(y_target))
ax2.legend(loc='upper left')

# turn off upper axis tick labels, rotate the lower ones, etc
for ax in ax1, ax2:
    for label in ax.get_xticklabels():
        label.set_visible(False)

plt.savefig('./figures/blr_detection_umass2.pdf')

plt.rc('axes', grid=False)
plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
#plt.gca().xaxis.set_major_locator(mdates.DayLocator())
textsize = 9
left, width = 0.1, 0.8
rect1 = [left, 0.2, width, 0.9]
fig = plt.figure(facecolor='white')
axescolor  = '#f6f6f6'  # the axes background color
ax1 = fig.add_axes(rect1, axisbg=axescolor)  #left, bottom, width, height
p_array = np.asarray(p_array)
hist, bin_edges = np.histogram(p_array, density=True)
numBins = 200
#p_array = p_array[~np.isnan(p_array)]
#ax1.hist(p_array, numBins,color=GRAY, alpha=0.7)
ax1.set_ylabel("P-value distribution")
plt.savefig('./figures/pvalue_distribution_under_H0.pdf')

cursor.close()
cnx.close()
