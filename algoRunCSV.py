#!/usr/bin/python -O

# Version of algoRun to analize CSV data
# Filename:     algoRunCSV.py
# Author(s):    apadin
# Start Date:   6/8/2016


##############################  LIBRARIES  ##############################
import datetime as dt
import time
import sys
import json
import numpy as np
import csv
import random

from algorithm import f1_scores
from algoRunFunctions import train, severityMetric, runnable
from grapher import Grapher, DATE_FORMAT, writeResults, print_stats

##############################  PARAMETERS  ##############################
<<<<<<< HEAD



=======
>>>>>>> 68ab7145fc322d650cc7727393ba59d11a22dcfb
##############################  INITIALIZE  ##############################


if __name__ == '__main__':

    # Get commandline arguments
    try:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        granularity = int(sys.argv[3])
        training_window = int(sys.argv[4])
        forecasting_interval = int(sys.argv[5])
    except:
        raise RuntimeError(
            "usage: %s <infile> <outfile> <granularity> <training_window> <forecasting_interval>"
            % sys.argv[0])

    print ("Starting analysis on %s with settings %d %d %d..." 
           % (infile, granularity, training_window, forecasting_interval))


    # Algorithm settings
    forecasting_interval = forecasting_interval * 60 # forecasting interval in hours
    matrix_length = forecasting_interval * training_window

    # Get list of features (first columns is time)
    infile = open(infile, 'r')
    columns = infile.next().split(',')[1:]

    print "The following features were found:", columns

    granularity_in_seconds = granularity * 60

    # Variables
    X =  np.zeros([matrix_length, len(columns)], np.float32)
    y_predictions = []
    y_target = []
    y_time = []
    w_opt = []
    a_opt = 0
    b_opt = 0
    mu = 0; sigma = 1000
<<<<<<< HEAD
    #w, L = (.84, 3.719) #(seems med sensitive) EWMA parameters. Other pairs can also be used, see paper
    #w, L = (0.53,3.714) #seems most  sensitive
    w, L = (1, 3.719) #Least sensitive
    sigma_w = np.sqrt(w/(2-w))
# Calculate variance of an fGN with self-similarity parameter H
#sigma_w, est_err = np.sqrt(quad(integrand, -np.inf, np.inf, args=(w, 1, .7)))
    alert_counter = 0
=======
    w, L = (.84, 3.719) #(seems med sensitive) EWMA parameters. Other pairs can also be used, see paper
    #w, L = (0.53,3.714) #seems most  sensitive
    #w, L = (1, 3.719) #Least sensitive
    sigma_w = np.sqrt(w/(2-w))
# Calculate variance of an fGN with self-similarity parameter H
#sigma_w, est_err = np.sqrt(quad(integrand, -np.inf, np.inf, args=(w, 1, .7)))

>>>>>>> 68ab7145fc322d650cc7727393ba59d11a22dcfb
    THRESHOLD = L * sigma_w
    print THRESHOLD
    Sn_1 = 0

    row_count = 0
    init_training = False

    #grapher = Grapher()
    
    anomalies = np.zeros(30)
    detected = set()
    ground_truth = set()
<<<<<<< HEAD
    
    # EWMA STUFF - REMOVE LATER
    last_avg = np.zeros(len(columns))
    alpha = 0.5
=======
>>>>>>> 68ab7145fc322d650cc7727393ba59d11a22dcfb


    ##############################  ANALYZE  ##############################
    print "Beginning analysis..."
    for line in infile:

        line = np.asarray([float(i) for i in line.split(',')])
        cur_time = line[0]
        cur_row = row_count % matrix_length
        X_data = line[1:]
<<<<<<< HEAD
        
        # EWMA STUFF - REMOVE LATER
        avg_data = last_avg + alpha * (X_data - last_avg)
        last_avg = avg_data
=======
>>>>>>> 68ab7145fc322d650cc7727393ba59d11a22dcfb
       
        if(cur_time >= 1465038505 and cur_time <= 1465042060):
            ground_truth.add(cur_time)
        #if(row_count % 240 == 0):
            #print "Trying time: %s " % dt.datetime.fromtimestamp(cur_time).strftime(DATE_FORMAT)

        # Update X
        #X[cur_row] = X_data
        X[cur_row] = avg_data

        # Time to train:
        if(row_count % forecasting_interval == 0 and row_count >= matrix_length):
            data = X[cur_row:, :-1]
            data = np.concatenate((data, X[:cur_row, :-1]), axis=0)
            y = X[cur_row:, -1]
            y = np.concatenate((y, X[:cur_row, -1]), axis=0)

            if (init_training or runnable(data) > 0.5):

                # For BLR train
                w_opt, a_opt, b_opt, S_N = train(data, y)
                
                # For TF train            
                #w_opt, a_opt, b_opt, S_N = tf_train(data, y)
                init_training = 1
            
            '''
            else:
                notRunnableCount += 1
                if(notRunnableCount > 5):
                    print "Data not runnable too many times! Exiting..."
            '''

        # Make a prediction
        if init_training:

            x_test = X[cur_row, :-1]
            prediction = max(0, np.inner(w_opt, x_test))
            target = X[cur_row, -1]

            y_time.append(cur_time)
            y_target.append(target)
            y_predictions.append(prediction)
            
            error = (prediction - target)
            sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_test),np.dot(S_N, x_test)))
            
            # Catching pathogenic cases where variance (ie, sigma) gets too small
            if sigma < 1:
                sigma = 1

            # Update severity metric
            mu = mu; sigma = sigma
            Sn, Zn = severityMetric(error, mu, sigma, w, Sn_1)

            #flag the user if necessary (error is greater than allowance)
            #two-in-a-row counter, much like branch prediction
            if np.abs(Sn) <= THRESHOLD:
                alert_counter = 0
                anomalies[row_count % 30] = 0
            elif np.abs(Sn) > THRESHOLD and alert_counter == 0:
                alert_counter = 1
                Sn = Sn_1
                anomalies[row_count % 30] = 0
            elif np.abs(Sn) > THRESHOLD and alert_counter == 1:
                Sn = 0
                anomalies[row_count % 30] = 1
                detected.add(cur_time)
                #print "ERROR: ANOMALY"
            
            Sn_1 = Sn

            A_SUM = anomalies.sum()
            if A_SUM > 200:
                print dt.datetime.fromtimestamp(cur_time).strftime(DATE_FORMAT)
		print A_SUM 
                #grapher.graph_anomalies(cur_time, cur_time - 29*60, anomalies.sum())
                #print anomalies.sum()
                            
            if (row_count % 30 == 0) and A_SUM > 5:
                print dt.datetime.fromtimestamp(cur_time).strftime(DATE_FORMAT)
		print A_SUM 
            '''
            if (row_count % forecasting_interval) == 0:
                
                #try:
                #    grapher.graph(y_time[-1440:], y_target[-1440:], y_predictions[-1440:])
                #except:
                
                grapher.graph(y_time, y_target, y_predictions)
                time.sleep(0.1)
            '''
        #Increment and loop
        row_count += 1

    # Close the input file
    infile.close()
        
    # Save data for later graphing
<<<<<<< HEAD
    writeResults(outfile, y_time, y_target, y_predictions)
    
    f1_scores(detected, ground_truth)
    print_stats(y_target, y_predictions)
    
    print "Ending analysis. See %s for results." % sys.argv[2]
    sys.exit(0)
    
    # grapher.close()
=======
    results = CSV(outfile)
    results.clear()
    results.append(y_time, y_target, y_predictions)
    
    TP = (detected & ground_truth)
    FP = float(len(detected - TP))
    FN = float(len(ground_truth-TP))

    TP = float(len(TP))
    print "TP:{}, FP:{}, FN:{}".format(TP,FP,FN)
    f1_scores = (2*TP)/((2*TP) + FP + FN)
    print "{}".format(f1_scores)
    print "Ending analysis. See %s for results." % sys.argv[2]
    sys.exit(0)
   # grapher.close()
>>>>>>> 68ab7145fc322d650cc7727393ba59d11a22dcfb
