import time
import numpy as np
import math
from grapher import Grapher
from matplotlib import pyplot as plt

import datetime as dt

def f1(t):
    return np.sin(2*np.pi*t) * np.exp(-t/10.)

def f2(t):
    return np.cos(2*np.pi*t)

max_data_points = 100
xdata, ydata1, ydata2 = [], [], []
grapher = Grapher()

cur_time = dt.datetime.today()

for x in xrange(10000):

    t = x/20.0
    print "Time", cur_time
    cur_time = cur_time + dt.timedelta(seconds=1)

    # Dummy data for testing
    xdata.append(cur_time)
    ydata1.append(f1(t))
    ydata2.append(f2(t))

    # (scrolling if necessary)
    if len(xdata) > max_data_points:
        xdata = xdata[-max_data_points:]
        ydata1 = ydata1[-max_data_points:]
        ydata2 = ydata2[-max_data_points:]

    grapher.graph_data(xdata, ydata1, ydata2)
        
    # Wait a second
    plt.pause(0.1)    
