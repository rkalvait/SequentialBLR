#!/usr/bin/env python
# Filename:     datalog.py
# Authors:      apadin, yabskbd, mjmor, dvorva
# Start Date:   5/9/2016

"""
Driver for collecting data from ZWay server and saving it to given
location. This program also maintains a separate log file for providing
device information so that the data can be analyzed later

- Adrian Padin, 1/20/2017
"""

#==================== LIBRARIES ====================#
import sys
import time
import datetime as dt
#import pandas as pd
import csv
import zway


#==================== FUNCTIONS ====================#

def get_all_data(server):
    """
    Accepts a zway.Server object and returns data for all connected devices."""
    return [server.get_data(id) for id in server.device_IDs()]

def get_fname(prefix, server):
    """
    Return the name of the file to be appended to
    Also checks if a new file must be made (new file made every day)
    """
    fname = "{}_{}.csv".format(prefix, dt.date.today())
    try:
        fh = open(fname, 'rb')
    except IOError:
        header = server.device_IDs()
        header.insert(0, "timestamp")
        with open(fname, 'wb') as fh:
            csv.writer(fh).write(header)
    return fname

        
def main(argv):
    """Connect to server and start the logging process."""
    host = argv[1]
    port = argv[2]
    prefix = argv[3]
    server = zway.Server(host, port)
    
    # Timing procedure
    granularity = 60
    goal_time = time.time()
    #goal_time = int(goal_time) + granularity - (int(time.time()) % granularity)

    while(True):
        
        while goal_time > time.time():
            time.sleep(0.2)
        goal_time = goal_time + granularity
        print "sample at time", goal_time
        
        data = get_all_data(server)
        data.insert(0, goal_time)
        fname = get_fname(prefix, server)
        with open(fname, 'wb') as fh:
            csv.writer(fh).write(data)


if __name__ == '__main__':
    main(sys.argv)
    


