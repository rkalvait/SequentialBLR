#!/usr/bin/env python

# Filename:         grapher2.py
# Contributors:     apadin
# Start Date:       2016-06-24

"""Updated version of grapher using PyQt4.

This program graphs CSV files with the following format:

Timestamp,Target,Prediction,Anomaly
<timestamp>, <target>, <prediction>, <anomaly>

ex)

Timestamp,Target,Prediction,Anomaly
1464763755,9530,9683,0
1464763815,8635,9150,1

- <timestamp> is an integer representing a UTC timestamp
- <target> and <prediction> are power values in Watts
- <anomaly> is a boolean value (1 or 0) indicating whether or not
    this target-prediction pair is an anomaly or not.
"""


#==================== LIBRARIES ====================#
import os
import sys
import csv
import time
import datetime as dt
import numpy as np
from collections import OrderedDict

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
class Settings(OrderedDict):
    """Class wrappper for reading and writing to settings file."""

    def __init__(self, settingsfile):
        super(Settings, self).__init__()
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
        self.graph_power.xaxis.set_major_locator(LinearLocator(numticks=5))
        self.graph_error.xaxis.set_major_locator(LinearLocator(numticks=5))

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
        'color' should be a string describing an _acceptable_ color value"""
        end = start + dt.timedelta(minutes=duration)
        span = self.graph_power.axvspan(xmin=start, xmax=end, color=color, alpha=0.15)
        self.fig.tight_layout()
        self.draw()

    def colorSpans(self, spans):
        """Add a series of vertical color spans to the graph.
        'spans' should be a list of tuples of the form: (start, duration, color)"""
        for span in spans:
            start = span[0]
            end = start + dt.timedelta(minutes=span[1])
            span = self.graph_power.axvspan(xmin=start, xmax=end, color=span[2], alpha=0.15)
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

    """Main application window, creates the main window and all widgets."""

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
        self.initTimer()

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
        self.edit_button.clicked.connect(self.changeSettings)
        layout.addRow(self.edit_button)

        self.reset_button = QtGui.QPushButton("Reset to Default", main_widget)
        self.reset_button.clicked.connect(self.resetSettings)
        layout.addRow(self.reset_button)

        self.pause_button = QtGui.QPushButton("Pause", main_widget)
        self.pause_button.clicked.connect(self.pauseTimer)
        self.paused = False
        layout.addRow(self.pause_button)
        
        self.update_button = QtGui.QPushButton("Update Now", main_widget)
        self.update_button.clicked.connect(lambda: self.loadFile(RESULTS_FILE))
        layout.addRow(self.update_button)
        
        self.update_countdown = QtGui.QLabel("Time until next update: %d seconds" % 0)
        layout.addRow(self.update_countdown)
        self.timeout = 0
        
        self.loadSettings()
        
        main_widget.setLayout(layout)
        return main_widget

    def settingsWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QFormLayout()

        update_label = QtGui.QLabel("Update rate (seconds):   ")
        self.update_edit = QtGui.QSpinBox(main_widget)
        self.update_edit.setRange(1, 600)
        layout.addRow(update_label, self.update_edit)

        past_label = QtGui.QLabel("Past results to show (hours):   ")
        self.past_edit = QtGui.QSpinBox(main_widget)
        self.past_edit.setRange(1, 24)
        layout.addRow(past_label, self.past_edit)

        self.smooth_box = QtGui.QCheckBox("Smooth data (window in minutes):    ", main_widget)
        self.smooth_box.stateChanged.connect(self.smoothToggled)
        self.smooth_edit = QtGui.QSpinBox(main_widget)
        self.smooth_edit.setRange(1, 120)
        self.smooth_edit.setDisabled(True)
        layout.addRow(self.smooth_box, self.smooth_edit)

        self.anomaly_box = QtGui.QCheckBox("Show anomalies (window in minutes):    ", main_widget)
        self.anomaly_box.stateChanged.connect(self.anomalyToggled)
        self.anomaly_edit = QtGui.QSpinBox(main_widget)
        self.anomaly_edit.setRange(1, 120)
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
            if len(columns) >= 4:
                self.anomalies = [float(t) for t in columns[3]]
            else:
                self.anomalies = []
                self.anomaly_box.setChecked(False)
                self.anomaly_box.setDisabled(True)
                self.anomaly_edit.setDisabled(True)
                self.anomaly_box.setText("Show anomalies (unavailable)")

                
            self.updateGraph()

    def loadSettings(self):
        self.settings = Settings(SETTINGS_FILE)
        self.update_edit.setValue(int(self.settings['update']))
        self.past_edit.setValue(int(self.settings['past']))
        self.smooth_box.setChecked(self.settings['smooth_check'] == 'True')
        self.smooth_edit.setValue(int(self.settings['smooth']))
        self.anomaly_box.setChecked(self.settings['anomaly_check'] == 'True')
        self.anomaly_edit.setValue(int(self.settings['anomaly']))
            
    def changeSettings(self):
        """Enables changes to options menu."""
        self.edit_button.setText("Save Changes and Update Graph")
        self.edit_button.clicked.disconnect()
        self.edit_button.clicked.connect(self.saveSettings)
        self.settings_widget.setEnabled(True)

    def saveSettings(self):
        """Save changes to options and disable options menu."""
        self.edit_button.setText("Change Settings")
        self.edit_button.clicked.disconnect()
        self.edit_button.clicked.connect(self.changeSettings)
        self.settings['update'] = str(self.update_edit.value())
        self.settings['past'] = str(self.past_edit.value())
        self.settings['anomaly'] = str(self.anomaly_edit.value())
        self.settings['smooth'] = str(self.smooth_edit.value())
        self.settings['anomaly_check'] = str(self.anomaly_box.isChecked())
        self.settings['smooth_check'] = str(self.smooth_box.isChecked())
        self.settings.save()
        self.settings_widget.setDisabled(True)
        self.updateGraph()

    # Reset the settings to default and draw the original graph
    def resetSettings(self):
        self.update_edit.setValue(5)
        self.past_edit.setValue(24)
        self.smooth_edit.setValue(1)
        self.anomaly_edit.setValue(1)
        self.smooth_box.setCheckState(QtCore.Qt.Unchecked)
        self.anomaly_box.setCheckState(QtCore.Qt.Unchecked)
        self.saveSettings()

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
        
        times = self.times
        targets = self.targets
        predictions = self.predictions
        
        # Step 1: Show only past X hours
        time_window = int(self.settings['past']) * 60     # Convert to minutes
        times = times[-time_window:]
        targets = targets[-time_window:]
        predictions = predictions[-time_window:]
        
        # Step 2: Smoothing
        if self.settings['smooth_check'] == 'True':
            smoothing_window = int(self.settings['smooth'])
            smoothing_window = min(smoothing_window, len(self.times))
            targets = movingAverage(targets, smoothing_window)
            predictions = movingAverage(predictions, smoothing_window)

        self.canvas.graphData(times, targets, predictions)
        
        # Step 3: Anomalies
        if self.settings['anomaly_check'] == 'True':
            self.showAnomalies()
        else:
            self.canvas.clearSpans()

    def showAnomalies(self):
        """Draw colored bars to show regions where anomalies happened."""
        #loading_window = LoadingWindow()
        self.options_widget.setDisabled(True)
        self.canvas.clearSpans() #Clear any existing spans

        start = 0
        dur = int(self.settings['anomaly'])
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

        self.canvas.colorSpans(spans)
        self.options_widget.setEnabled(True)
        #loading_window.close()

    def initTimer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateTimer)
        self.timer.start(1000)
        
    def updateTimer(self):
        """Start the timer which periodically updates the graph."""
        if not self.paused:
            if self.timeout == 0:
                self.loadFile(RESULTS_FILE)
                self.timeout = float(self.settings['update'])
            else:
                self.timeout -= 1
            self.update_countdown.setText("Time until next update: %d seconds" % (self.timeout))
            
    def pauseTimer(self):
        """Halt the graph updates until the pause button is pressed again."""
        if not self.paused:
            self.paused = True
            self.pause_button.setText("Continue")
        else:
            self.paused = False
            self.pause_button.setText("Pause")
            
            
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
