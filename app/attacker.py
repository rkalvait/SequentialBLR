#!/usr/bin/env python

# Visual tool for adding attacks into any data set
# Filename:     attacker.py
# Author(s):    apadin
# Start Date:   2016-06-22

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


##############################  QT CLASSES  ##############################

# Figure class used for graphing
class MyCanvas(FigureCanvas):

    # Constructor
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MyCanvas, self).__init__(self.fig)
        
        self.setParent(parent)

        self.graph = self.fig.add_subplot(111)
        self.clear()

        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)

        FigureCanvas.updateGeometry(self)
        self.fig.tight_layout()
        self.draw()

    # Update the graph using the given data
    # 'times' should be datetime objects
    # 'power' should be in Watts
    def updateGraph(self, times, power):
        power = [i/1000.0 for i in power]
        xmin = min(times)
        xmax = max(times)
        ymin = 0
        ymax = max(power) * 1.1

        #self.graph.plot(times, power, 'r')
        self.power_line.set_data(times, power)
        self.graph.set_xlim(xmin, xmax)
        self.graph.set_ylim(ymin, ymax)

        self.fig.tight_layout()
        self.draw()
        
    # Add a horizontal color span to the graph
    # 'start' should be a datetime (preferably in range)
    # 'duration' should be the width of the span
    # 'color' should be a string describing an acceptable color value
    def colorSpan(self, start, duration, color):
        end = start + dt.timedelta(minutes=duration)
        self.graph.axvspan(xmin=start, xmax=end, color=color, alpha=0.2)
        self.draw()

    # Clear current graph, including line and 
    def clear(self):
        self.graph.cla()
        zero = dt.datetime.fromtimestamp(0)
        one = dt.datetime.fromtimestamp(1)
        x, y = [zero, one], [-1, -1]
        self.graph.set_xlim(zero, one)
        self.graph.set_ylim(0, 1)
        self.power_line, = self.graph.plot(x, y, color='red')
        self.graph.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M:%S"))
        self.graph.xaxis.set_major_locator(LinearLocator(numticks=6))
        plt.setp(self.graph.get_xticklabels(), rotation=10)
        self.graph.set_ylabel("Power (kW)")
        self.fig.tight_layout()
        self.draw()
        

# Main application window - creates the widgets and the window
class MainWindow(QtGui.QMainWindow):

    # Constructor
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(50, 50, 800, 500)
        self.setWindowTitle('Attacker')
        self.setWindowIcon(QtGui.QIcon('merit_icon.png'))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.statusBar()
        self.old_filename = ''
        self.new_filename = ''

        # Create top-level widget and immediate children
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

    # Create an instance of the MyCanvas widget
    def createGraphWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout()

        self.canvas = MyCanvas(main_widget, width=5, height=4, dpi=80)
        toolbar = NavigationToolbar(self.canvas, main_widget)
        #update = QtGui.QPushButton("Update Graph", main_widget)
        #update.clicked.connect(self.getData)

        layout.addWidget(self.canvas)
        layout.addWidget(toolbar)
        #layout.addWidget(update)
        main_widget.setLayout(layout)
        return main_widget
        
    # Create the settings window below the grapher
    def createSettingsWidget(self):
        main_widget = QtGui.QWidget(self)
        layout = QtGui.QGridLayout(main_widget)

        self.label_old = QtGui.QLabel("Original File", main_widget)
        self.edit_old  = QtGui.QLineEdit(main_widget)
        self.label_new = QtGui.QLabel("New File", main_widget)
        self.edit_new  = QtGui.QLineEdit(main_widget)

        browse_button = QtGui.QPushButton("Browse...")
        browse_button.clicked.connect(self.browseFile)
        load_button = QtGui.QPushButton("Reset")
        load_button.clicked.connect(self.loadFile)
        save_button = QtGui.QPushButton("Save")
        save_button.clicked.connect(self.saveFile)
        attack_button = QtGui.QPushButton("Attack!")
        attack_button.clicked.connect(self.startAttack)
        
        self.edit_old.editingFinished.connect(self.oldFilename)
        self.edit_new.editingFinished.connect(self.newFilename)

        layout.addWidget(self.label_old, 0, 0)
        layout.addWidget(self.label_new, 1, 0)
        layout.addWidget(self.edit_old,  0, 1)
        layout.addWidget(self.edit_new,  1, 1)
        layout.addWidget(browse_button,  0, 2)
        layout.addWidget(save_button,    1, 2)
        layout.addWidget(load_button,    0, 3)
        layout.addWidget(attack_button,  1, 3)

        main_widget.setLayout(layout)
        return main_widget

    # Search the file system for the desired input file
    def browseFile(self):
        self.old_filename = str(QtGui.QFileDialog.getOpenFileName())
        if self.old_filename != '':
            self.new_filename = self.old_filename.rstrip('.csv')
            self.new_filename += '_attacked.csv'
            self.edit_old.setText(self.old_filename)
            self.edit_new.setText(self.new_filename)
            self.loadFile()
        
    # Load original data from the file given by old_filename
    # Always grabs the first and last columns in the file
    def loadFile(self):
        if self.checkFilename(self.old_filename):
            self.canvas.clear()
            try:
                file = open(self.old_filename, 'rb')
            except:
                filename = os.path.basename(self.old_filename)
                self.statusBar().showMessage(
                    "Error: file %s was not found" % filename)
            else:
                reader = csv.reader(file)
                reader.next() #Ignore header row
                timestamps = []
                self.old_power = []
                for line in reader:
                    timestamps.append(float(line[0]))
                    self.old_power.append(float(line[-1]))
                file.close()
                
                # Time could be datetime string or UNIX timestamp
                try:
                    self.times = [dt.datetime.fromtimestamp(float(t)) for t in timestamps]
                except ValueError:
                    self.times = [dt.datetime.strptime(t, DATE_FORMAT) for t in timestamps]
                    
                self.canvas.updateGraph(self.times, self.old_power)
                self.new_power = [item for item in self.old_power]
                self.statusBar().showMessage(
                    "Graphing complete.", 5000)
                
    # Save the new data in the file given by new_filename
    def saveFile(self):
        if self.checkFilename(self.new_filename):
            with open(self.new_filename, 'wb') as outfile, open(self.old_filename, 'rb') as infile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)
                writer.writerow(reader.next()) #Copy header row
                count = 0
                for line in reader:
                    line[-1] = self.new_power[count]
                    writer.writerow(line)
                    count += 1
            self.statusBar().showMessage(
                "File %s saved" % self.new_filename, 5000)

    # Save the filename from the respective line editor
    def oldFilename(self): self.old_filename = self.edit_old.text()
    def newFilename(self): self.new_filename = self.edit_new.text()

    # Return true if the given filename is valid, false otherwise
    def checkFilename(self, filename):
        if filename == '':
            self.statusBar().showMessage(
                "Error: no file name given")
            return False
        elif filename[-4:] != '.csv':
            self.statusBar().showMessage(
                "Error: file must be '.csv' format")
            return False
        return True

    # Open the attack dialog and get the inputs
    # Add the attack and re graph
    def startAttack(self):
        if self.checkFilename(self.old_filename):
            dialog = AttackDialog(self)
            if dialog.exec_():
                startdate, duration, intensity = dialog.get_info()
            else:
                return
            self.addAttack(startdate, duration, intensity)
            self.canvas.updateGraph(self.times, self.new_power)
            self.canvas.colorSpan(startdate, duration, 'red')
            self.statusBar().showMessage(
                "Graphing complete.", 5000)
        else:
            pass
            
    # This is where the magic happens
    # Add an attack to new_power
    def addAttack(self, startdate, duration, intensity):
        enddate = startdate + dt.timedelta(minutes=duration)

        # Verify that the times are usable
        if (startdate > self.times[-1] or
                enddate < self.times[0]):
            self.statusBar().showMessage(
                "Error: attack out of range", 5000)
            raise ValueError("Attack out of range")
            
        for index in xrange(len(self.times)):
            if self.times[index] > enddate:
                return
            if self.times[index] > startdate:
                self.new_power[index] += intensity

                
# Dialog window for adding a new attack
class AttackDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(AttackDialog, self).__init__(parent)
        self.setWindowTitle('Add Attack')
        layout = QtGui.QVBoxLayout()
        
        form_widget = QtGui.QWidget(self)
        form_layout = QtGui.QFormLayout()

        self.date_input = QtGui.QDateTimeEdit(form_widget)
        self.duration_input = QtGui.QLineEdit(form_widget)
        self.intensity_input = QtGui.QLineEdit(form_widget)
        
        form_layout.addRow(QtGui.QLabel("Start date: ", form_widget),
                           self.date_input)
        form_layout.addRow(QtGui.QLabel("Duration (minutes): ", form_widget),
                           self.duration_input)
        form_layout.addRow(QtGui.QLabel("Intensity (Watts): ", form_widget),
                           self.intensity_input)
                           
        form_widget.setLayout(form_layout)
        
        button_widget = QtGui.QWidget(self)
        accept_button = QtGui.QPushButton("Ok", button_widget)
        accept_button.clicked.connect(self.set_info)
        reject_button = QtGui.QPushButton("Cancel", button_widget)
        reject_button.clicked.connect(self.reject)
        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(reject_button)
        button_widget.setLayout(button_layout)
        
        layout.addWidget(form_widget)
        layout.addWidget(button_widget)
        self.setLayout(layout)
        
    def get_info(self):
        return (self.startdate, self.duration, self.intensity)
                
    def set_info(self):
        self.startdate = self.date_input.dateTime().toPyDateTime()
        
        try:
            self.duration = int(self.duration_input.text())
        except Exception:
            print "NOPE"; return

        try:
            self.intensity = int(self.intensity_input.text())
        except Exception:
            print "NOPE"; return            
            
        self.accept()


##############################  MAIN  ##############################
def main():
    app = QtGui.QApplication(sys.argv)
    toplevel = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
