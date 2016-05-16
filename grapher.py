# Grapher class for plotting target and prediction values
# Filename:     grapher.py
# Author(s):    apadin
# Start Date:   5/13/2016

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D

class Grapher:

    # Constructor
    def __init__(self):
        
        plt.ion() # Allows interactice session, animate the graph

        # Create figure and added main title
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle("Sequential BLR: Prediction and Error", fontsize=18)
        
        self._graph_predict = fig.add_subplot(211) # Target versus prediction
        self._graph_error = fig.add_subplot(212) # Error (target - prediction)

        # Set titles and axis labels for both graphs
        self._graph_predict.set_title("Prediction vs. Target")
        self._graph_predict.set_xlabel("Time")
        self._graph_predict.set_ylabel("Power (kW)")
        
        self._graph_error.set_title("Error (Prediction minus Target)")
        self._graph_error.set_xlabel("Time")
        self._graph_error.set_ylabel("Error (kW)")

        plt.subplots_adjust(top = 0.87, hspace = 0.5)
        plt.draw()       

        # Sets the x-axis to only show hours, minutes, and seconds of time
        self._graph_predict.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        self._graph_error.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))

        # Sets the x-axis to only show 6 tick marks        
        self._graph_predict.xaxis.set_major_locator(LinearLocator(numticks=6))
        self._graph_error.xaxis.set_major_locator(LinearLocator(numticks=6))

        # Add legend
        predict_key = Line2D([], [], color='0.75', label='Prediction')
        target_key = Line2D([], [], color='red', linestyle='--', label='Target')
        error_key = Line2D([], [], color='red', label='Error')

        self._graph_predict.legend(handles=[target_key, predict_key])
        self._graph_error.legend(handles=[error_key])

        

    # Plot the data
    def graph_data(self, y_time, y_target, y_predict):

        # Calculate the difference vector
        diff = []
        for i in xrange(len(y_target)):
            diff.append(y_predict[i] - y_target[i])
    
        # Initialize lines
        line1, line2 = self._graph_predict.plot(y_time, y_predict, '0.75',
                                                y_time, y_target, 'r--')
                                                
        line3, = self._graph_error.plot(y_time, diff, 'r')

        # Set x and y axis limits
        # Axes update every time to reflect scope of data
        xmin = min(y_time)
        xmax = max(y_time)

        ymin = min(min(y_target), min(y_predict))
        ymax = max(max(y_target), max(y_predict))
    
        diffmin = min(diff)
        diffmax = max(diff)

        self._graph_predict.set_xlim(xmin, xmax)
        self._graph_predict.set_ylim(ymin, ymax)

        self._graph_error.set_xlim(xmin, xmax)
        self._graph_error.set_ylim(diffmin, diffmax)

        # Draw the plot
        plt.draw()
        
