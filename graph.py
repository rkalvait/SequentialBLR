import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

plt.ion()

max_data_points = 100

def f1(t):
    return np.sin(2*np.pi*t) * np.exp(-t/10.)

def f2(t):
    return np.cos(2*np.pi*t)

xdata, ydata1, ydata2, diff = [], [], [], []
fig = plt.figure()
g_y_vals = fig.add_subplot(211)
g_err = fig.
line, = graph.plot(xdata, ydata, 'r-')
xmin = 0
xmax = 10
ymin = -1
ymax = 1

for x in xrange(10000):

    t = x/20.0
    print "Time", t

    xdata.append(t)
    ydata1.append(f1(t))
    ydata1.append(f2(t))
    error.append(f1(t) - f2(t))
    
    # Set data
    if len(xdata) > max_data_points:
        xdata = xdata[-max_data_points:]
        ydata = ydata[-max_data_points:]

    line.set_data(xdata, ydata)

    # Set axes
    xmax = xdata[-1]
    xmin = xdata[0]
    
    graph.set_xlim(xmin, xmax+1)
    graph.set_ylim(ymin, ymax)

    # Draw the plot
    fig.canvas.draw()

    # Wait a second
    #time.sleep(0.00001)
