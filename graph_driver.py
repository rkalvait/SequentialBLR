# Script to fetch pickled data and graph it
# using the Grapher class
# Filename:     graph_driver.py
# Author(s):    apadin
# Start Date:   5/16/2016

import pickle
import time
from grapher import Grapher

y_target_fname = "y_target.bak"
y_predict_fname = "y_predict.bak"
y_time_fname = "y_time.bak"

goal_time = float(int(time.time() + 1.0))
time.sleep(goal_time-time.time())

grapher = Grapher()

while True:

    goal_time += 10.0

    while True:
        try:
            file = open("y_time.bak", "rb")
            y_time = pickle.load(file)
            file.close()
        
            file = open("y_target.bak", "rb")
            y_target = pickle.load(file)
            file.close()

            file = open("y_predict.bak", "rb")
            y_predict = pickle.load(file)
            file.close()

            break

        except Exception:
            print ("File in use. Trying again.")

    assert len(y_target) == len(y_predict)
    assert len(y_target) == len(y_time)

    grapher.graph_data(y_time, y_target, y_predict)

    try:
        time.sleep(goal_time - time.time())
    except Exception:
        print "Sleep time negative. Skipping sleep"
