#!/usr/bin/env python

# Filename:         grapher2.py
# Contributors:     apadin
# Start Date:       2016-06-24

"""Updated version of grapher using PyQt4.

This program graphs files with the following format:

Timestamp,Target,Prediction,Anomaly
1464763755,9530,9683,0

- Timestamp is an integer representing a UTC timestamp
- Target and Prediction are power values in Watts
- Anomaly is a binary value (1 or 0) indicating whether or not
    this target-prediction pair is an anomaly or not.
"""


#==================== LIBRARIES ====================#
import os
import sys
import csv
import time
import datetime as dt
import numpy as np

from PyQt4 import QtGui, QtCore
#from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.figure import Figure

from param import *
from algoFunctions import movingAverage


#==================== HELPER CLASSES ====================#
class Settings(dict):
    """Class wrappper for reading and writing to settings file."""

    def __init__(self, settingsfile):
        """Initialize the dictionary and read in the settings from the settings file."""
        self.settingsfile = settingsfile
        self.read()

    def read(self):
        """Read in settings from the settings file and put in a dictionary."""
        with open(self.settingsfile, 'rb') as infile:
            # Each setting is in the form "key=value"
            for line in infile:
                line = line.rstrip()            # Remove whitespace
                if len(line) == 0: continue     # Ignore blank lines
                key, value = line.split('=')
                self[key] = value

    def save(self):
        """Write settings back to the settings file."""
        with open(self.settingsfile, 'wb') as outfile:
            for key in self:
                line = "%s=%s\n" % (str(key), str(self[key]))
                outfile.write(line)


#==================== GUI CLASSES ====================#
class ResultsGraph(FigureCanvas):

    """Figure class used for graphing results"""

    def __init__(self, parent=None, width=5, height=4, dpi=80):
        """Create and display an empty graph."""
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        # Create graphs and lines
        self.graph_power = self.fig.add_subplot(211)
        self.graph_error = self.fig.add_subplot(212)
        zero = dt.datetime.fromtimestamp(0)
        one = dt.datetime.fromtimestamp(1)
        x, y = [zero, one], [-1, -1]
        self.predict_line, = self.graph_power.plot(x, y, color='0.8')
        self.target_line, = self.graph_power.plot(x, y, color='r', linestyle='--')
        self.error_line, = self.graph_error.plot(x, y, color='r')
        self.color_spans = []

        # Change settings of graph
        self.graph_power.set_ylabel("Power (kW)")
        self.graph_error.set_ylabel("Error (kW)")
        self.graph_power.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M:%S"))
        self.graph_error.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M:%S"))
        self.graph_power.xaxis.set_major_locator(LinearLocator(numticks=7))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=7))

        # Rotate dates slightly
        plt.setp(self.graph_power.get_xticklabels(), rotation=10)
        plt.setp(self.graph_error.get_xticklabels(), rotation=10)

        # Let graph expand with window
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
        self.updateGeometry()
        self.fig.tight_layout()
        self.draw()

    def graphData(self, times, target, predict):
        """ Update the graph using the given data
        'times' should be datetime objects
        'target' should be float values in Watts
        'predict' should be float values in Watts
        """

        assert(len(times) == len(target))
        assert(len(times) == len(predict))

        # Convert to kW and generate error line
        target = [i/1000.0 for i in target]
        predict = [i/1000.0 for i in predict]
        error = [predict[i] - target[i] for i in xrange(len(times))]

        # Determine new bounds of graph
        xmin = min(times)
        xmax = max(times)
        ymin = 0
        ymax = max(max(target), max(predict)) * 1.1
        emin = min(error)
        emax = max(error)
        self.graph_power.set_xlim(xmin, xmax)
        self.graph_power.set_ylim(ymin, ymax)
        self.graph_error.set_xlim(xmin, xmax)
        self.graph_error.set_ylim(emin, emax)

        # Set data to lines and re-draw graph
        self.predict_line.set_data(times, predict)
        self.target_line.set_data(times, target)
        self.error_line.set_data(times, error)
        self.fig.tight_layout()
        self.draw()

    def colorSpan(self, start, duration, color):
        """Add a vertical color span to the target-prediction graph
        'start' should be a datetime (preferably in range)
        'duration' should be the width of the span in minutes
        'color' should be a string describing an _acceptable_ color value
        """

        end = start + dt.timedelta(minutes=duration)
        span = self.graph_power.axvspan(xmin=start, xmax=end, color=color, alpha=0.2)
        self.fig.tight_layout()
        self.draw()

    def colorSpans(self, spans):
        """Add a series of vertical color spans to the graph.
        'spans' should be a list of tuples of the form: (start, duration, color)"""
        for span in spans:
            start = span[0]
            end = start + dt.timedelta(minutes=span[1])
            span = self.graph_power.axvspan(xmin=start, xmax=end, color=span[2], alpha=0.2)
            self.color_spans.append(span)
        self.fig.tight_layout()
        self.draw()

    def clearSpans(self):
        """Remove all vertical color spans."""
        for span in self.color_spans:
            span.remove()
        self.color_spans = []
        self.fig.tight_layout()
        self.draw()


class ResultsWindow(QtGui.QMainWindow):

    """Main application window, creates the widgets and the window"""

    # Constructor
    def __init__(self):
        super(ResultsWindow, self).__init__()
        self.setGeometry(50, 50, 1200, 800)
        self.setWindowTitle('Results Grapher')
        self.setWindowIcon(QtGui.QIcon(ICON_FILE))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create top-level widget and immediate children
        self.statusBar()
        main_widget = QtGui.QWidget()
        self.graph_widget = self.graphWidget()
        self.options_widget = self.optionsWidget()

        # Add children to layout and set focus to main widget
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.options_widget)
        layout.addWidget(self.graph_widget, stretch=1)
        main_widget.setLayout(layout)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)
        self.show()

        # Load the data and graph it
        self.loadFile(RESULTS_FILE)

    #==================== WIDGET FUNCTIONS ====================#
    # These functions create all the widgets, sub-widgets, etc. of the program.
    # Each function creates a new widget instance, adds all necessary layouts
    # and sub-widgets, and then returns its widget to the widget above.

    # Create an instance of the ResultsGraph widget
    def graphWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout()
        self.canvas = ResultsGraph(main_widget, width=5, height=4, dpi=80)
        toolbar = NavigationToolbar(self.canvas, main_widget)

        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        main_widget.setLayout(layout)
        return main_widget

    # Creates the options panel to toggle smoothing and anomalies
    def optionsWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QFormLayout()

        options_label = QtGui.QLabel("Settings:", main_widget)
        options_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addRow(options_label)

        self.settings_widget = self.settingsWidget()
        self.settings_widget.setDisabled(True)
        layout.addRow(self.settings_widget)

        self.edit_button = QtGui.QPushButton("Edit Settings", main_widget)
        self.edit_button.clicked.connect(self.editOptions)
        layout.addRow(self.edit_button)

        reset_button = QtGui.QPushButton("Reset to Default", main_widget)
        reset_button.clicked.connect(self.resetOptions)
        layout.addRow(reset_button)

        update_button = QtGui.QPushButton("Load New Data", main_widget)
        update_button.clicked.connect(lambda: self.loadFile(RESULTS_FILE))
        layout.addRow(update_button)

        main_widget.setLayout(layout)
        return main_widget

    def settingsWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QFormLayout()
        self.settings = Settings(SETTINGS_FILE)

        update_label = QtGui.QLabel("Update rate (minutes):   ")
        self.update_edit = QtGui.QSpinBox(main_widget)
        self.update_edit.setRange(1, 100)
        print self.update_edit.maximum()
        print self.update_edit.minimum()
        self.update_edit.setValue(int(self.settings['update']))
        layout.addRow(update_label, self.update_edit)

        past_label = QtGui.QLabel("Past results to show (hours):   ")
        self.past_edit = QtGui.QSpinBox(main_widget)
        self.past_edit.setRange(1, 100)
        self.past_edit.setValue(int(self.settings['past']))
        layout.addRow(past_label, self.past_edit)

        self.smooth_box = QtGui.QCheckBox("Smooth data (window in minutes):    ", main_widget)
        self.smooth_box.stateChanged.connect(self.smoothToggled)
        self.smooth_edit = QtGui.QSpinBox(main_widget)
        self.smooth_edit.setRange(1, 100)
        self.smooth_edit.setValue(int(self.settings['smooth']))
        self.smooth_edit.setDisabled(True)
        layout.addRow(self.smooth_box, self.smooth_edit)

        self.anomaly_box = QtGui.QCheckBox("Show anomalies (window in minutes):    ", main_widget)
        self.anomaly_box.stateChanged.connect(self.anomalyToggled)
        self.anomaly_edit = QtGui.QSpinBox(main_widget)
        self.anomaly_edit.setRange(1, 100)
        self.anomaly_edit.setValue(int(self.settings['anomaly']))
        self.anomaly_edit.setDisabled(True)
        layout.addRow(self.anomaly_box, self.anomaly_edit)

        main_widget.setLayout(layout)
        return main_widget

    #==================== HELPER FUNCTIONS ====================#
    # These functions do the actual work of the program.
    # Most are called in response to an event triggered by the main window, while
    # others are helper functions which perform a simple task.

    def loadFile(self, filename):
        """Load in the data from the results file."""
        try:
            file = open(filename, 'rb')
        except IOError as error:
            #raise RuntimeError('Bad results filename')
            #print "Error: bad results filename"
            print repr(error)
            sys.exit(1)
        else:
            reader = csv.reader(file)
            headers = reader.next()
            columns = zip(*reader)
            file.close()

            # Convert times from string or timestamp to datetime
            try:
                self.times = [
                    dt.datetime.fromtimestamp(float(t)) for t in columns[0]]
            except ValueError:
                self.times = [
                    dt.datetime.strptime(t, DATE_FORMAT) for t in columns[0]]

            self.targets = [float(t) for t in columns[1]]
            self.predictions = [float(t) for t in columns[2]]
            if len(headers) >= 4:
                self.anomalies = [float(t) for t in columns[3]]

            self.updateGraph()

    def editOptions(self):
        """Enables changes to options menu."""
        self.edit_button.setText("Save Changes and Update Graph")
        self.edit_button.clicked.disconnect()
        self.edit_button.clicked.connect(self.saveOptions)
        self.settings_widget.setEnabled(True)

    def saveOptions(self):
        """Save changes to options and disable options menu."""
        self.edit_button.setText("Change Settings")
        self.edit_button.clicked.disconnect()
        self.edit_button.clicked.connect(self.editOptions)
        self.settings['update'] = self.update_edit.value()
        self.settings['past'] = self.past_edit.value()
        self.settings['anomaly'] = self.anomaly_edit.value()
        self.settings['smooth'] = self.smooth_edit.value()
        self.settings.save()
        self.settings_widget.setDisabled(True)

        print "options saved"
        self.updateGraph()

    # Reset the settings to default and draw the original graph
    def resetOptions(self):
        self.update_edit.setValue(5)
        self.past_edit.setValue(24)
        self.smooth_edit.setValue(1)
        self.anomaly_edit.setValue(1)
        self.smooth_box.setCheckState(QtCore.Qt.Unchecked)
        self.anomaly_box.setCheckState(QtCore.Qt.Unchecked)
        self.saveOptions()

    def smoothToggled(self, state):
        """Enable or disable data smoothing based on 'state'."""
        if state == QtCore.Qt.Checked:
            self.smooth_edit.setEnabled(True)
        else:
            self.smooth_edit.setDisabled(True)

    def anomalyToggled(self, state):
        """Enable or disable anomaly bars based on 'state'."""
        if state == QtCore.Qt.Checked:
            self.anomaly_edit.setEnabled(True)
        else:
            self.anomaly_edit.setDisabled(True)

    def updateGraph(self):
        """Graph the pre-loaded data and add any desired features."""
        if self.smooth_box.isChecked():
            smoothing_window = min(self.smooth_edit.value(), len(self.times))
            self.canvas.graphData(
                self.times,
                movingAverage(self.targets, smoothing_window),
                movingAverage(self.predictions, smoothing_window))
        else:
            self.canvas.graphData(self.times, self.targets, self.predictions)

        if self.anomaly_box.isChecked():
            self.showAnomalies()
        else:
            self.canvas.clearSpans()

    def showAnomalies(self):
        """Draw colored bars to show regions where anomalies happened."""
        loading_window = LoadingWindow()
        self.options_widget.setDisabled(True)
        self.canvas.clearSpans() #Clear any existing spans

        start = 0
        dur = self.anomaly_edit.value()
        level1 = 0
        level2 = dur / 3.0
        level3 = level2 * 2
        spans = []  # List of color spans

        while start < len(self.anomalies):
            #Count number of anomalies and choose a corresponding color
            start_time = self.times[start]
            count = sum(self.anomalies[start:(start + dur)])
            if count > 0:
                if count > level3:
                    spans.append((start_time, dur, 'red'))
                elif count > level2:
                    spans.append((start_time, dur, 'orange'))
                else:
                    spans.append((start_time, dur, 'green'))
            start += dur

        print "number of spans: ", len(spans)
        self.canvas.colorSpans(spans)
        self.options_widget.setEnabled(True)
        loading_window.close()


class LoadingWindow(QtGui.QDialog):

    """Create a "loading window" which has an infinitely running progress bar"""

    def __init__(self):
        super(LoadingWindow, self).__init__(None, QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' ')
        self.setWindowIcon(QtGui.QIcon(ICON_FILE))
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Calculating. Please wait...", self))
        progress = QtGui.QProgressBar(self)
        progress.setMinimum(0)
        progress.setMaximum(0)
        layout.addWidget(progress, stretch=1)
        self.setLayout(layout)
        self.show()


#==================== MAIN ====================#
def main(argv):
    app = QtGui.QApplication(sys.argv)
    toplevel = ResultsWindow()
    sys.exit(app.exec_())


#==================== DRIVER ====================#
if __name__ == '__main__':
    main(sys.argv)
