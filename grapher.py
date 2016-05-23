# Grapher class for plotting target and prediction values
# Filename:     grapher.py
# Author(s):    apadin
# Start Date:   5/13/2016

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.lines import Line2D
import pickle
import time

class Grapher:

    # Constructor
    def __init__(self):

        plt.ion() # Allows interactice session, animate the graph

        # Create figure and added main title
        fig = plt.figure()
        fig.suptitle("Sequential BLR: Prediction and Error", fontsize=18)

        self.graph_predict = fig.add_subplot(211) # Target versus prediction
        self.graph_error = fig.add_subplot(212) # Error (target - prediction)

        # Set titles and axis labels for both graphs
        self.graph_predict.set_title("Prediction vs. Target")
        self.graph_predict.set_xlabel("Time")
        self.graph_predict.set_ylabel("Power (kW)")

        self.graph_error.set_title("Error (Prediction minus Target)")
        self.graph_error.set_xlabel("Time")
        self.graph_error.set_ylabel("Error (kW)")

        plt.subplots_adjust(top = 0.87, hspace = 0.5)

        # Sets the x-axis to only show hours, minutes, and seconds of time
        self.graph_predict.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
        self.graph_error.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))

        # Sets the x-axis to only show 6 tick marks
        self.graph_predict.xaxis.set_major_locator(LinearLocator(numticks=6))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=6))

        # Add lines and legend
        self.predict_line, = self.graph_predict.plot([], [], color='0.75', label='Prediction')
        self.target_line, = self.graph_predict.plot([], [], color='red', linestyle='--', label='Target')
        self.error_line, = self.graph_error.plot([], [], color='red', label='Error')

        self.graph_predict.legend(handles=[self.target_line, self.predict_line])
        self.graph_error.legend(handles=[self.error_line])


    # Plot the data
    def graph_data(self, y_predict, y_target, y_time):

        # Calculate the error vector
        y_error = []
        for i in xrange(len(y_target)):
            y_error.append(y_predict[i] - y_target[i])

        # Set x and y axis limits
        # Axes update every time to achieve "scrolling" effect
        xmin = min(y_time)
        xmax = max(y_time)

        ymin = min(min(y_target), min(y_predict))
        ymax = max(max(y_target), max(y_predict))

        emin = min(y_error)
        emax = max(y_error)

        self.graph_predict.set_xlim(xmin, xmax)
        self.graph_predict.set_ylim(ymin, ymax)

<<<<<<< HEAD
        self.graph_error.set_xlim(xmin, xmax)
        self.graph_error.set_ylim(emin, emax)
        self.graph_error.set_ylim(-30, 30)
=======
        self._graph_error.set_xlim(xmin, xmax)
        #self._graph_error.set_ylim(diffmin, diffmax)
        self._graph_error.set_ylim(-30, 30)
        
        # Draw the plot
        plt.draw()
>>>>>>> 8e0f40d93da53394eb3cd2051b99e6be10ea6f37

        # Set new data (automatically updates the graph
        self.predict_line.set_data(y_time, y_predict)
        self.target_line.set_data(y_time, y_target)
        self.error_line.set_data(y_time, y_error)


# Driver for graphing at any time based on stored values
def main():

    grapher = Grapher()

    goal_time = float(int(time.time() + 1.0))
    time.sleep(goal_time-time.time())

    while True:

        goal_time += 5.0

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

        print "Graphing at time", y_time[-1]
        grapher.graph_data(y_predict, y_target, y_time)

        # Catch error of sleeping for a negative time
        if (goal_time > time.time()):
<<<<<<< HEAD
            plt.pause(goal_time - time.time())

if __name__ == "__main__":
    main()
=======
            print goal_time
            print time.time()
            plt.pause(goal_time - time.time())            

if __name__ == "__main__":
    main()
        
        
>>>>>>> 8e0f40d93da53394eb3cd2051b99e6be10ea6f37
