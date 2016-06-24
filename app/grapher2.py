#!/usr/bin/env python

# Update grapher which also shows green, yellow, and red sections
# Filename:     grapher2.py
# Author(s):    apadin
# Start Date:   2016-06-24

import os
import sys
import csv
import time
import datetime as dt
import numpy as np

from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import LinearLocator
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from PyQt4 import QtGui, QtCore

from algoRunFunctions import movingAverage

'''
if qt_compat.QT_API == qt_compat.QT_API_PYSIDE:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore
'''


##############################  QT CLASSES  ##############################

# Figure class used for graphing results
class ResultsGraph(FigureCanvas):

    # Constructor
    def __init__(self, parent=None, width=5, height=4, dpi=80):
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

    # Update the graph using the given data
    # 'times' should be datetime objects
    # 'target' should be float values in Watts
    # 'predict' should be float values in Watts
    def updateGraph(self, times, target, predict):
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
        
    # Add a horizontal color span to the target-prediction graph
    # 'start' should be a datetime (preferably in range)
    # 'duration' should be the width of the span
    # 'color' should be a string describing an _acceptable_ color value
    def colorSpan(self, start, duration, color):
        end = start + dt.timedelta(minutes=duration)
        self.graph_power.axvspan(xmin=start, xmax=end, color=color, alpha=0.2)
        self.fig.tight_layout()
        self.draw()
        

# Main application window - creates the widgets and the window
class MainResults(QtGui.QMainWindow):

    # Constructor
    def __init__(self):
        super(MainResults, self).__init__()
        self.setGeometry(50, 50, 800, 500)
        self.setWindowTitle('Graph Results')
        self.setWindowIcon(QtGui.QIcon('merit_icon.ppm'))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create top-level widget and immediate children
        self.statusBar()
        main_widget = QtGui.QWidget()
        graph_widget = self.createGraphWidget()
        settings_widget = self.createSettingsWidget()

        # Add children to layout and set focus to main widget
        layout = QtGui.QVBoxLayout()
        layout.addWidget(graph_widget)
        layout.addWidget(settings_widget)
        main_widget.setLayout(layout)
        main_widget.setFocus()
        self.setCentralWidget(main_widget)
        
        self.show()

    # Create an instance of the ResultsGraph widget
    def createGraphWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout()
        self.canvas = ResultsGraph(main_widget, width=5, height=4, dpi=80)
        toolbar = NavigationToolbar(self.canvas, main_widget)

        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        main_widget.setLayout(layout)
        return main_widget
        
    # Create the settings window below the grapher
    def createSettingsWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QGridLayout(main_widget)

        filename_label = QtGui.QLabel("Results file: ", main_widget)
        self.file_edit = QtGui.QLineEdit(main_widget)
        browse = QtGui.QPushButton('Browse...')
        browse.clicked.connect(self.browseFile)
        refresh = QtGui.QPushButton('Reset')
        refresh.clicked.connect(self.loadFile)
        smooth = QtGui.QPushButton('Smooth...')
        smooth.clicked.connect(self.smoothData)

        layout.addWidget(filename_label, 0, 0)
        layout.addWidget(self.file_edit, 0, 1)
        layout.addWidget(browse, 0, 2)
        layout.addWidget(refresh, 0, 3)
        layout.addWidget(smooth, 0, 4)
        main_widget.setLayout(layout)
        return main_widget

    # Search the file system for the desired input file
    def browseFile(self):
        filename = str(QtGui.QFileDialog.getOpenFileName())
        self.file_edit.setText(filename)
        if (filename != ''):
            self.loadFile()
        
    # Load data from the file given by filename
    def loadFile(self):
        filename = str(self.file_edit.text())
        if self.checkFilename(filename):
            try:
                file = open(filename, 'rb')
            except:
                filename = os.path.basename(filename)
                self.statusBar().showMessage(
                    "Error: file %s was not found" % filename)
            else:
                reader = csv.reader(file)
                headers = reader.next()
                time_index = headers.index("Time")
                target_index = headers.index("Target")
                predict_index = headers.index("Prediction")
                try:
                    anom_index = headers.index("Anomalies")
                except:
                    anom_index = -1
                
                self.times = []
                self.target = []
                self.predict = []
                self.anomalies = []
                for row in reader:
                    self.times.append(row[0])
                    self.target.append(float(row[1]))
                    self.predict.append(float(row[2]))
                    try:
                        self.anomalies.append(float(row[3]))
                    except IndexError:
                        pass
                        
                file.close()
                
                # Convert times from string or timestamp to datetime
                try:
                    self.times = [
                        dt.datetime.fromtimestamp(float(t)) for t in self.times]
                except ValueError:
                    self.times = [
                        dt.datetime.strptime(t, DATE_FORMAT) for t in self.times]
                    
                self.canvas.updateGraph(self.times, self.target, self.predict)
                self.statusBar().showMessage("Graphing complete.", 5000)
                
    # Return true if the given filename is valid, false otherwise
    def checkFilename(self, filename):
        if filename == '':
            self.statusBar().showMessage("Error: no file name given")
            return False
        elif filename[-4:] != '.csv':
            self.statusBar().showMessage("Error: file must be '.csv' format")
            return False
        return True
        
    # Open a dialog prompting the user for a smoothing value
    def smoothData(self):
        if getattr(x, "y", None) == None:
            self.statusBar().showMessage("Error: no file name given")
            return False
            
        smoothing_window, ok = QtGui.QInputDialog.getInt(
            None, #parent
            'Smooth Data', #title
            'Smoothing window (minutes)', #label
            value=120, #default
            min=5) #minimum

        if ok:
            self.canvas.updateGraph(
                self.times,
                movingAverage(self.target, smoothing_window),
                movingAverage(self.predict, smoothing_window))

                
##############################  MAIN  ##############################
def main():
    app = QtGui.QApplication(sys.argv)
    toplevel = MainResults()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
