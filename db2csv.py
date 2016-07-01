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

from param import *
from database import Database

##############################  PARAMETERS  ##############################
outfilename = 'smart_env_Jul.csv'

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


# Return a list of ID numbers, given input string
# Interpret 1-3 to include 1,2,3
def getListIDs(inputIDs):
    inputIDs = inputIDs.split(',')
    id_list = []
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
    with open(SMART_DRIVER) as driver:
        jsonDataFile = json.load(driver)

    print ("\nRetreiving data from database...")
    database = Database(DB_CONFIG)

    granularity_in_seconds = int(jsonDataFile['granularity']) * 60

    # Get the list of feature numbers
    id_list = getListIDs(jsonDataFile["idSelection"])
    id_list = list(set(id_list)) # Remove duplicates
    id_list.sort()

    # Determine the range of times to pull data from.
    # If the user specified a timeframe, use that range.
    if(int(jsonDataFile["specifyTime"])):
       start_time = dt.datetime.strptime(jsonDataFile["beginTime"], DATE_FORMAT)
       end_time = dt.datetime.strptime(jsonDataFile["endTime"], DATE_FORMAT)

    # Otherwise, find the largest timeframe for which each feature has data.
    else:
        start_time, end_time = getStartEndTimes(id_list)

    print "Start, end: ", start_time, end_time
        
    # Get the list of column headers for the features.
    columns = []
    for id in id_list:
        columns.append(jsonDataFile['data'][id-1]['columnName'])        
    columns.append(jsonDataFile['totalConsum'])
    print "Number of columns:", len(columns)
 
    outfile = open(outfilename, 'wb')
    writer = csv.writer(outfile)

    last = np.zeros(len(columns))
    
    count = 0
    
    ##############################  DATA COLLECTION  ##############################
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
        
        new_data = np.asarray([max(0, data) for data in new_data])   # Remove 'nan' and negative
        #'''        
        if new_data[0] == 0:
            new_data[0] = last[0]
            new_data[1] = last[1]
        else:
            last = new_data
        #'''

        start_time = time.mktime(start_time.timetuple())
        new_data = np.insert(new_data, 0,  start_time)
        writer.writerow(new_data)

        start_time = stop_time  # Increment and loop

    outfile.close()
    print "See %s for results." % outfilename
    
    
# If run as main:
if __name__ == "__main__":
    main()
