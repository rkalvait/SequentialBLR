# DESCRIPTION
# Filename:     bp.py
# Author:       apadin
# Start Date:   5/18/2016

import pickle
import math
import time
import datetime

def func1(t):
    return math.sin(t / 10.0)
    
def func2(t):
    return math.cos(t / 10.0) + 2

y_target, y_predictions, y_time = [], [], []
    
t = 0

for t in range(200):

    y_target.append(func1(t))
    y_predictions.append(func2(t))
    y_time.append(datetime.datetime.now())
    
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
    
    print "Trying time:", t
    time.sleep(5)

    t = t + 1