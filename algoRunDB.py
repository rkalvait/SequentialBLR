# Run the algorithm using prepared data from a database
# Specifically designed to run Smart* Data
# Filename:     algoRun.py
# Author:       mjmor, dvorva, apadin
# Start Date:   ??? before 4/30/2016

print "BLR Analysis: Database"

##############################  LIBRARIES  ##############################

import sys
import time
import datetime as dt
import numpy as np
import csv
import json
from urllib import urlopen

from algorithm import Algo, f1_scores
from grapher import DATE_FORMAT, writeResults, print_stats
from database import Database


##############################  PARAMETERS  ##############################
CONFIG_FILE = 'config.txt'
outfile = 'results.csv'

##############################  FUNCTIONS  ##############################

# Determine start and end times for all data
# Return result as datetime objects
def getStartEndTimes(id_list):

    # Get start and end times for each feature
    start_list = []
    end_list = []
    for id in id_list:
        start_list.append(jsonDataFile['data'][id-1]['startTime'])
        end_list.append(jsonDataFile['data'][id-1]['endTime'])

    # Find latest start time, earliest end time
    start_time = dt.datetime.strptime(max(start_list), DATE_FORMAT)
    end_time = dt.datetime.strptime(min(end_list), DATE_FORMAT)
    return start_time, end_time


# Return a list of ID numbers, given input
def getListIDs(inputIDs):

    inputIDs = inputIDs.split(',')
    id_list = []
    
    # Interpret 1-3 to include 1,2,3
    for selection in inputIDs:
        if '-' not in selection:
            id_list.append(int(selection))
        else:
            bounds = selection.split('-')
            for index in range(int(bounds[0]), int(bounds[1])+1):
                id_list.append(index)

    return id_list
    
    


##############################  MAIN  ##############################
def main():

    # Retreive settings from JSON settings file
    with open('smartDriver.json') as data_file:
        jsonDataFile = json.load(data_file)

    granularity = int(jsonDataFile['granularity'])
    training_window = int(jsonDataFile['windowSize'])
    forecasting_interval = int(jsonDataFile['forecastingInterval'])
    
    print ("\nStarting analysis on database with settings %d %d %d..." 
           % (granularity, training_window, forecasting_interval))
           
    granularity_in_seconds = granularity * 60
           
    # Initialize database
    database = Database(CONFIG_FILE)
           
    # Get the list of feature numbers
    id_list = getListIDs(jsonDataFile["idSelection"])

    id_list = list(set(id_list)) # Remove duplicates
    id_list.sort()

    # Determine the range of times to pull data from    
    # If the user specified a timeframe, use that
    if(int(jsonDataFile["specifyTime"])):
       start_time = dt.datetime.strptime(jsonDataFile["beginTime"], DATE_FORMAT)
       end_time = dt.datetime.strptime(jsonDataFile["endTime"], DATE_FORMAT)

    # Otherwise, find the largest timeframe for which each feature has data
    else:
        start_time, end_time = getStartEndTimes(id_list)

    print "Start, end: ", start_time, end_time
        
    # Get the list of column headers for the features
    columns = []
    for id in id_list:
        columns.append(jsonDataFile['data'][id-1]['columnName'])
        
    columns.append(jsonDataFile['totalConsum'])
   
    print "Columns:", len(columns)
 
    # Algorithm settings
    algo = Algo(granularity, training_window, forecasting_interval, len(columns)-1)
    
    y_predict = []
    y_target = []
    y_time = []
    
    count = 0
    
    # EWMA additions
    # alpha is adjustable on a scale of (0, 1]
    # The smaller value of alpha, the more averaging takes place
    # A value of 1.0 means no averaging happens
    last_avg = np.zeros(len(columns))
    alpha = 1.0
    
    detected = set()
    ground_truth = set()

    ##############################  ANALYSIS  ##############################
    print "Beginning analysis..."
    while start_time < end_time:

        # FOR SMART* ONLY
        # Some of the data seems bad on the 31st - too many NULLS
        if (start_time > dt.datetime(2012, 5, 30) and 
            start_time < dt.datetime(2012, 6, 1)):
            
            start_time = dt.datetime(2012, 6, 1)

        if(count % 240 == 0):
            print "trying time: %s " % start_time
            
        count += 1

        #Execute the query:
        stop_time = start_time + dt.timedelta(0, granularity_in_seconds)
        new_data = database.get_avg_data(start_time, stop_time, columns)
        
        new_data = np.asarray([max(0, data) for data in new_data]) # remove 'nan' and negative
	for data in new_data:
            if data < 0: print "NEGATIVE"

        # EWMA calculation
        avg_data = last_avg + alpha * (new_data - last_avg)
        last_avg = avg_data

        target = float(avg_data[-1])
        prediction = algo.run(avg_data) # Magic!
        
        if prediction != None:
            y_time.append(start_time)
            y_target.append(target)
            y_predict.append(float(prediction))
            
            if algo.checkSeverity(target, float(prediction)):
                detected.add(start_time)

        start_time = stop_time #Increment and loop


    ##############################  GRAPHING/STATS  ##############################

    # Save data for later graphing
    writeResults(outfile, y_time, y_target, y_predict)
    
    #f1_scores(detected, ground_truth)
    print_stats(y_target, y_predict)

    print "Ending analysis. See %s for results." % outfile
    
    
# If run as main:
if __name__ == "__main__":
    main()
