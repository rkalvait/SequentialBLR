#!/usr/bin/python -O

# Version of algoRun to analize CSV data
# Filename:     algoRunCSV.py
# Author(s):    apadin
# Start Date:   6/8/2016

print "BLR Analysis: CSV"

##############################  LIBRARIES  ##############################
import sys
import time
import datetime as dt
import numpy as np
import csv

from algorithm import Algo, f1_scores
from grapher import DATE_FORMAT, writeResults, print_stats


##############################  PARAMETERS  ##############################


##############################  MAIN  ##############################
def main():

    # Get commandline arguments
    try:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        granularity = int(sys.argv[3])
        training_window = int(sys.argv[4])
        forecasting_interval = int(sys.argv[5])
    except:
        raise RuntimeError(
            """usage: %s <infile> <outfile>
                <granularity> <training_window> <forecasting_interval>"""
            % sys.argv[0])

    print ("\nStarting analysis on %s with settings %d %d %d..." 
           % (infile, granularity, training_window, forecasting_interval))
           
    # Get list of features (first columns is time)
    infile = open(infile, 'rb')
    reader = csv.reader(infile)
    columns = reader.next()[1:]
    
    #print "The following features were found:", columns

    # Algorithm settings
    algo = Algo(granularity, training_window, forecasting_interval, len(columns)-1)
    
    y_time = ['Time']
    y_target = ['Target']
    y_predict = ['Prediction']
    anomalies = ['Anomaly']
    
    count = 0
    
    # EWMA additions
    # alpha is adjustable on a scale of (0, 1]
    # The smaller value of alpha, the more averaging takes place
    # A value of 1.0 means no averaging happens
    last_avg = np.zeros(len(columns))
    alpha = 1
    print "Alpha: %.3f" % alpha
    
    detected = set()
    ground_truth = set()
    
    ##############################  ANALYSIS  ##############################
    print "Beginning analysis..."
    for line in reader:

        # Read new data from file
        cur_time = float(line[0])
        new_data = np.asarray(line[1:], np.float)

        #if (count % 240) == 0:
        #    current_time = dt.datetime.fromtimestamp(cur_time)
        #    print "Trying time %s" % current_time.strftime(DATE_FORMAT)
            
        count += 1
        
        # EWMA calculation
        avg_data = last_avg + alpha * (new_data - last_avg)
        last_avg = avg_data

        target = float(avg_data[-1])
        prediction = algo.run(avg_data) # Magic!
        
        if prediction != None:
            y_time.append(cur_time)
            y_target.append(target)
            y_predict.append(float(prediction))
            
            if algo.checkSeverity(target, float(prediction)):
                detected.add(cur_time)
                anomalies.append(1)
            else:
                anomalies.append(0)
                
        if(cur_time >= 1465038505 and cur_time <= 1465042060):
            ground_truth.add(cur_time)
         

    ##############################  GRAPHING/STATS  ##############################
         
    # Close the input file
    infile.close()
        
    # Save data for later graphing
    writeResults(outfile, (y_time, y_target, y_predict, anomalies))
    
    f1_scores(detected, ground_truth)
    print_stats(y_target[1:], y_predict[1:]) #Remove header

    print "Ending analysis. See %s for results." % sys.argv[2]
    
    
# If run as main:
if __name__ == "__main__":
    main()