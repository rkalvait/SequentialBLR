#!/usr/bin/python -O

# Inject false anomalies into data
# Filename:     attack.py
# Author(s):    apadin
# Start Date:   6/22/2016

import csv
import time
import datetime as dt
from grapher import DATE_FORMAT

def main():

    infile = raw_input("Name of original file? ")
    outfile = raw_input("Name of new file? ")
    addition = raw_input("Amount of attack? ")
    start_time = raw_input("Start time? ")
    end_time = raw_input("End time? ")
    
    print "Working..."
    
    addition = float(addition)
    
    # Calculate timestamps for start and end
    try:
        start_time = int(start_time)
    except ValueError:
        start_time = dt.datetime.strptime(start_time, DATE_FORMAT)
        start_time = time.mktime(start_time.timetuple())

    try:
        end_time = int(end_time)
    except:
        end_time = dt.datetime.strptime(end_time, DATE_FORMAT)
        end_time = time.mktime(end_time.timetuple())
    
    # Open in and out files
    infile = open(infile, 'rb')
    outfile = open(outfile, 'wb')
    outfile.write(infile.next()) # copy the headers

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Search each line in the input file for timestamps between start and end
    for line in reader:
        
        try:
            timestamp = int(line[0])
        except ValueError:
            timestamp = dt.datetime.strftime(line[0], DATE_FORMAT).timestamp()

        if (timestamp >= start_time and timestamp <= end_time):
            print timestamp
            line[-1] = float(line[-1]) + addition
            
        # Write the data back
        writer.writerow(line)
        
    infile.close()
    outfile.close()
    
    print "Done."


if __name__ == '__main__':
    main()