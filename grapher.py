import matplotlib.pyplot as plt

class Grapher:

    # Constructor
    def __init__(self):
        
        plt.ion() # allows interactice session, animate the graph

        fig = plt.figure()
        fig.suptitle("Prediction and Error", fontsize=16)
        
        self._graph_predict = fig.add_subplot(211) # Target versus prediction
        self._graph_error = fig.add_subplot(212) # Error (target - prediction)
        
        self._graph_predict.set_title("\nPrediction vs. Target (kWh)")
        self._graph_error.set_title("\nError (Target - Prediction, kWh)")
        
        
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
        plt.draw()
        