#!/usr/bin/python
# vim:ts=4:sw=4:sts=4:tw=100
# -*- coding: utf-8 -*-
#
#if you have any questions, email/text me - Davis
import datetime as dt
import json
import logging
import numpy as np
import os 
import random
import scipy as sp
import scipy.stats
import sys
import time

from algoRunFunctions import train, severityMetric
from datetime import date
from get_data import get_data, get_power
from urllib import urlopen

print "Starting algorithm run..."
if len(sys.argv) != 4:
    print "Error: please run like: python pi_seq_BLR.py <granularity> <window size> <forecasting interval>"
    print "Where granularity is the frequency of data collection, in minutes"
    print "Where window size is the number of hours of remembered data"
    print """"Where forecasting interval is the number of hours between 
			trainings"""
    exit(1)

FORMAT='%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT='%m/%d/%Y %I:%M:%S %p'
logging.basicConfig(filename='/var/log/sequential_predictions.log', 
					level=logging.DEBUG, 
					format=FORMAT,
					datefmt=DATE_FORMAT)

# Training statistics:
w_opt = []
a_opt = 0
b_opt = 0
mu = 0; sigma = 1000
THRESHOLD = 100000 #TODO, set this
w, L = (.84, 3.719) # EWMA parameters. Other pairs can also be used, see paper
Sn_1 = 0
init_training = 0
alert_counter = 0


with open("/usr/local/sbin/SequentialBLR/sensors.json") as data_file:
    json_sensor_data = json.load(data_file)

num_sensors = len(json_sensor_data["sensors"])
martix_length = int(sys.argv[2])*60/int(sys.argv[1])
forecasting_interval = int(sys.argv[3])*60/int(sys.argv[1])
granularity_in_seconds = int(sys.argv[1])*60

#X window init.
X =  np.zeros([martix_length, num_sensors+1]) #sensors, energy reading
y = [None]*martix_length
#Not currently used, but eventually we should add the logic to not use old data
#(sensors that are off report the same data, etc) TODO
last_data = [0]*num_sensors #Last data
last_data_count = [0]*num_sensors #number of polls since change of data

row_count = 0
while True:
	
    if not row_count % 200:
	print row_count
	
    #get new data from pi
    new_data = get_data()

    #Execute the query to get new y value
    cursor.execute(qry)

    #get current energy reading
    X[(row_count) % martix_length][num_sensors] = get_power()
    #Update X - new_data[0] contains a timestamp we don't need
    for i in range(1, num_sensors):
        #We have new valid data! Also update last_data
        X[(row_count) % martix_length][i-1] = new_data[i]
        if new_data[i] == last_data[i-1]:
            last_data_count[i-1] += 1
        else:
            last_data[i-1] = new_data[i]
            last_data_count[i-1] = 0

    # Time to train:
    if( (row_count+1) % forecasting_interval == 0 and row_count >= martix_length):
        #unwrap the matrices
        data = X[(row_count % martix_length):,:num_sensors]
        data = np.concatenate((data, X[0:(row_count % martix_length), :num_sensors]), axis=0)
        y = X[(row_count % martix_length):, num_sensors]
        y = np.concatenate((y, X[:(row_count % martix_length), num_sensors]), axis=0)

        w_opt, a_opt, b_opt, S_N = train(data, y)
        init_training = 1

    #make prediction:
    if(init_training):
        x_n = X[(row_count) % martix_length][:num_sensors]
        prediction = max(0, np.inner(w_opt,x_n))
        target = X[(row_count) % martix_length][num_sensors]

        #log the new result
        logging.info(dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S") + " " + str(target) + " " + str(prediction))
	#print dt.datetime.now().strftime("%m/%d/%Y %H:%M:%S") + " " + str(target) + " " + str(prediction)

        #not currently used but will be necessary to flag user:
        error = (prediction-target)
        sigma = np.sqrt(1/b_opt + np.dot(np.transpose(x_n),np.dot(S_N, x_n)))
        if sigma < 1: sigma = 1 # Catching pathogenic cases where variance (ie, sigma) gets really really small

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
            alert_counter = 0
            logging.error("ANOMALY FOUND!")
	    #print "ERROR: ANOMALY"

        Sn_1 = Sn

    row_count += 1
    #A rough sleeping approximation. The delay of the above logic is dependent on the number
    #of sensors, and whether or not this iteration had to train. You could use a timer,
    #but that seems like unnecessary extra work. For our purpose, and if the user is using a granularity
    #of a minute or more, I think this error is negligible.
    time.sleep(granularity_in_seconds - 2)
