import matplotlib.pyplot as plt
import matplotlib

class Grapher:

    # Constructor
    def __init__(self):
        
        #plt.ion() # Allows interactice session, animate the graph
        
        fig = plt.figure()
        fig.suptitle("Sequential BLR: Prediction and Error", fontsize=16)
        
        self._graph_predict = fig.add_subplot(211) # Target versus prediction
        self._graph_error = fig.add_subplot(212) # Error (target - prediction)
        
        self._graph_predict.set_title("Prediction vs. Target")
        self._graph_predict.set_xlabel("Time")
        self._graph_predict.set_ylabel("Power (kW)")
        
        self._graph_error.set_title("Error (Target - Prediction)")
        self._graph_error.set_xlabel("Time")
        self._graph_error.set_ylabel("Error (kW)")
        
        self._graph_predict.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))
        self._graph_error.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))
        
        self._graph_predict.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=6))
        self._graph_error.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=6))
        
    # Plot the data
    def graph_data(self, time, ydata1, ydata2):

        diff = []
        for i in xrange(len(ydata1)):
            diff.append(ydata1[i] - ydata2[i])
    
        # Initialize lines
        line1, line2 = self._graph_predict.plot(time, ydata1, 'r-',
                                                time, ydata2, 'b')

        line3, = self._graph_error.plot(time, diff, 'r')
    
        # Set data
        line1.set_data(time, ydata1)
        line2.set_data(time, ydata2)
        line3.set_data(time, diff)

        # Set axes - Changes to reflect scope of data
        xmin = min(time)
        xmax = max(time)

        ymin = min(min(ydata1), min(ydata2))
        ymax = max(max(ydata1), max(ydata2))
    
        diffmin = min(diff)
        diffmax = max(diff)

        self._graph_predict.set_xlim(xmin, xmax)
        self._graph_predict.set_ylim(ymin, ymax)

        self._graph_error.set_xlim(xmin, xmax)
        self._graph_error.set_ylim(diffmin, diffmax)

        # Draw the plot
        plt.subplots_adjust(top = 0.87, hspace = 0.5)
        plt.draw()
        