import mysql.connector
from urllib import urlopen
import json
import numpy as np
import datetime as dt
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

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

print "Starting algorithm run..."

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

config = {
    'user': usr,
    'password': pswd,
    'host': hst,
    'database': db,
    'raise_on_warnings': True
}
cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
print "Connection made to DB."

with open('/Users/dvorva/Documents/Research/getGraphiteData/sequentialBLR/smartDriver.json') as data_file:
    jsonDataFile = json.load(data_file)
print "Found JSON file."

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

granularityInSeconds = int(jsonDataFile["granularity"])*60

#X window init.
X =  np.zeros([matrixLength, len(columns)])
Xt =  [None]*matrixLength
y = [None]*matrixLength

print "Beginning analysis."

y_predictions = []
y_target = []
y_time = []
w_opt = []
a_opt = 0
b_opt = 0
rowCount = 1
initTraining = 0
notRunnableCount = 0
mu = 0; sigma = 1000
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
Sn_1 = 0
p_array = []

count123 = 1 #for debug
while startTime < endTime:

    #Some of the data seems bad on the 31st - too many NULLS
    if startTime > dt.datetime(2012, 5, 30) and startTime < dt.datetime(2012, 6, 1):
        startTime = dt.datetime(2012, 6, 1)

    if(rowCount % 250 == 0):
        print "trying time: %s " % startTime

    #Build the query:
    isFirst = 1
    qry = "SELECT "
    for column in columns:
        if isFirst == 0:
            qry += ", "
        else:
            isFirst = 0
        qry = qry + column

    qry = qry + " FROM SMART WHERE dataTime BETWEEN %s AND %s"

    #Execute the query:
    cursor.execute(qry , (startTime, startTime + dt.timedelta(0,granularityInSeconds)))

    #Get the average in the queried window: (should probably switch this to be done by qry)
    colSum = np.zeros(len(columns))
    colCount = np.zeros(len(columns))
    for row in cursor:
        i = 0
        for columnData in row:
            if columnData is not None:
                if shouldBeRounded[i] == 1 and columnData < 0:
                    columnData = 0
                colSum[i] += columnData
                colCount[i] += 1
            i += 1

    #Update X,Xt,y
    Xt[(rowCount-1) % matrixLength] = startTime
    for i in range(0, len(columns)):
        #We have new valid data! Also update lastData
        if colSum[i] > 0:
            if "motion" in columns[i]:
                X[(rowCount-1) % matrixLength][i] = colSum[i]
                lastData[i] = colSum[i]
            else:
                X[(rowCount-1) % matrixLength][i] = colSum[i] / colCount[i]
                lastData[i] = colSum[i] / colCount[i]

            lastDataTime[i] = startTime
        #No new data.
        else:
            #X[(rowCount-1) % matrixLength][i] = lastData[i]
            X[(rowCount-1) % matrixLength][i] = 0
            countNoData[i] += 1

    # Time to train:
    if(rowCount % forecastingInterval == 0 and rowCount >= matrixLength):
        data = X[(rowCount % matrixLength):,0:len(columns)-1]
        data = np.concatenate((data, X[0:(rowCount % matrixLength), 0:len(columns)-1]), axis=0)
        y = X[(rowCount % matrixLength):, len(columns)-1]
        y = np.concatenate((y, X[:(rowCount % matrixLength), len(columns)-1]), axis=0)
        if(initTraining or runnable(data) > 0.5):
            #'Unwrap' the data matrices
            #time = Xt[(rowCount % matrixLength):]
            #time += Xt[:(rowCount % matrixLength)]
            w_opt, a_opt, b_opt, S_N = train(data, y)
            initTraining = 1

        elif(runnable(data) < 0.5):
            notRunnableCount += 1
            if(notRunnableCount > 5):
                print "Data not runnable too many times! Exiting..."

    if(not initTraining):
        severityArray.append(0)

    #make prediction:
    if(initTraining):
        x_n = X[(rowCount-1) % matrixLength][:len(columns)-1]
        #y_time.append(Xt[(rowCount-1) % matrixLength])
        prediction = max(0, np.inner(w_opt,x_n))
        # if prediction > 25000:
        #     #retrain with old data
        #     print "Error, prediction skyrocketed (potentially) due to beta = 0 NAN/INF"
        #     print "Re-training on random set of old data, for this period"
        #
        #     #Create the new training matrix
        #     tempData = []
        #     tempActual = []
        #     for i in range(0, int(0.75*len(X))):
        #         randomRow = random.randint(0, len(X)-1)
        #         tempData.append(X[randomRow][0:len(columns)-1])
        #         tempActual.append(X[randomRow][len(columns)-1])
        #
        #     w_opt, a_opt, b_opt, S_N = train(tempData, tempActual)
        #     prediction = max(0, np.inner(w_opt,x_n))
        #     if prediction > 25000:
        #         print "Error persists after a new training."

        y_predictions.append(prediction)
        y_target.append(X[(rowCount-1) % matrixLength][len(columns)-1])
        error = (y_predictions[-1]-y_target[-1])
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_n),np.dot(S_N, x_n)))
        if sigma < 1: sigma = 1 # Catching pathogenic cases where variance (ie, sigma) gets really really small

        # Update severity metric
        mu = mu; sigma = sigma
        Sn, Zn = severityMetric(error, mu, sigma, w, Sn_1)
        severityArray.append(Sn)
        #Zscore_array[n] = Zn
        Sn_1 = Sn
        p = 1 - sp.stats.norm.cdf(error, mu, sigma)
        p_array.append(p)


    y_time.append(Xt[(rowCount-1) % matrixLength])
    #Increment and loop
    startTime += dt.timedelta(0,granularityInSeconds)
    rowCount += 1


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
p_array = p_array[~np.isnan(p_array)]
ax1.hist(p_array, numBins,color=GRAY, alpha=0.7)
ax1.set_ylabel("P-value distribution")
plt.savefig('./figures/pvalue_distribution_under_H0.pdf')

cursor.close()
cnx.close()
