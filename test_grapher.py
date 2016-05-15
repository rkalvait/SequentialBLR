import time
import numpy as np
from grapher import Grapher
from matplotlib import pyplot as plt

def f1(t):
    return np.sin(2*np.pi*t) * np.exp(-t/10.)

def f2(t):
    return np.cos(2*np.pi*t)

max_data_points = 100
xdata, ydata1, ydata2 = [], [], []
grapher = Grapher()

for x in xrange(10000):

    t = x/20.0
    print "Time", t

    # Dummy data for testing
    xdata.append(t)
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
