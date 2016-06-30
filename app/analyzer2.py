#!/usr/bin/env python

"""Visual tool for analyzing data and creating results graphs
# Filename:     analyzer2.py
# Author(s):    apadin
# Start Date:   2016-06-29

"""


#==================== LIBRARIES ====================#

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

from param import *
from results import readResults, writeResults
from attacker import MyCanvas as PowerGraph
from attacker import AttackDialog


#==================== GUI CLASSES ====================#

class MainWindow(QtGui.QMainWindow):

    """The main window of the application."""

    def __init__(self):
        """Initialize the main window and create all child widgets."""

        super(MainWindow, self).__init__()
        self.setGeometry(50, 50, 1200, 800)
        self.setWindowTitle('Results Grapher')
        self.setWindowIcon(QtGui.QIcon(icon_file))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Widget creation
        self.statusBar()
        self.mainWidget = self.createWidgets()
        self.mainWidget.setFocus()
        self.setCentralWidget(self.mainWidget)
        self.show()

        
    #==================== WIDGETS ====================#

    def createWidgets(self):
        """Create the main widget and all children."""

        mainWidget = QtGui.QWidget(self)
        #self.resultsGraph = ResultsGraph(parent=mainWidget)
        #self.resultsGraph.hide()
        self.powerGraph = PowerGraph(self)
        fileLayout = self.createFileLayout()
        attackLayout = self.createAttackLayout()
        algoLayout = self.createAlgoLayout()

        # Add children to layout and set focus to main widget
        layout = QtGui.QGridLayout()
        layout.addWidget(self.powerGraph, 0, 0, 1, 2)
        layout.addLayout(fileLayout, 1, 0, 1, 1)
        layout.addLayout(attackLayout, 2, 0, 1, 1)
        layout.addLayout(algoLayout, 1, 1, 1, 2)
        mainWidget.setLayout(layout)
        return mainWidget
        
    def createFileLayout(self):
        """Create the file browsing section"""

         layout = QtGui.QGridLayout()

        #title = QtGui.QLabel("Choose a file to graph: ", self)
        #title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        inputLabel = QtGui.QLabel("Input file: ", self)
        attackLabel = QtGui.QLabel("New file (with attacks): ", self)
        resultsLabel = QtGui.QLabel("Results file: ", self)
        self.inputEdit = QtGui.QLineEdit(self)
        self.inputEdit.setEnabled(False)
        self.attackEdit = QtGui.QLineEdit(self)
        self.resultsEdit = QtGui.QLineEdit(self)
        browse = QtGui.QPushButton('Browse...')
        browse.clicked.connect(parent.browseFile)
        save = QtGui.QPushButton('Save')
        save.clicked.connect(self.saveAttackFile)

        #layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(inputLabel, 1, 0)
        layout.addWidget(attackLabel, 2, 0)
        layout.addWidget(resultsLabel, 3, 0)
        layout.addWidget(self.inputEdit, 1, 1)
        layout.addWidget(self.attackEdit, 2, 1)
        layout.addWidget(self.resultsEdit, 3, 1)
        layout.addWidget(browse, 1, 2)
        layout.addWidget(save, 2, 2)
        return layout
        
        
        
        
        
        
        
        
        
        
        
        
        

    def browseFile(self):
        """Choose a file using the file search dialog."""

        filename = str(QtGui.QFileDialog.getOpenFileName())
        if (filename != ''):
            self.checkInputFilename(filename) #Raises exception if not CSV file
            self.fileWidget.inputEdit.setText(filename)
            filename = filename.rstrip('.csv')
            self.fileWidget.attackEdit.setText(filename + '_attacked.csv')
            self.fileWidget.resultsEdit.setText(filename + '_results.csv')

            self.loadInputFile() #Load times and power into self.time, self.target
            self.powerGraph.setEnabled(True)
            self.attackWidget.setEnabled(True)
            self.algoWidget.setEnabled(True)
            self.powerGraph.graphData(self.time, self.target)
            self.statusBar().showMessage("Graphing complete.", 5000)

    def checkInputFilename(self, filename):
        """Return if the given filename is valid, raise exception otherwise"""

        if filename == '':
            warningMessage = QtGui.QMessageBox()
            warningMessage.setWindowTitle("Warning")
            warningMessage.setText("No file specified.")
            warningMessage.setIcon(QtGui.QMessageBox.Warning)
            warningMessage.exec_()
            raise ValueError("No file specified.")

        elif filename[-4:] != '.csv':
            warningMessage = QtGui.QMessageBox()
            warningMessage.setWindowTitle("Warning")
            warningMessage.setText("File must have '.csv' extension.")
            warningMessage.exec_()
            warningMessage.setIcon(QtGui.QMessageBox.Warning)
            raise ValueError("File must have '.csv' extension.")

    def loadInputFile(self):
        """Load power data from the input file."""

        csvfile = str(self.fileWidget.inputEdit.text())
        with open(csvfile, 'rb') as infile:
            reader = csv.reader(infile)
            reader.next()
            columns = zip(*reader)

        # Convert times from string or timestamp to datetime
        try:
            self.time = [dt.datetime.fromtimestamp(float(t)) for t in columns[0]]
        except ValueError:
            self.time = [dt.datetime.strptime(t, DATE_FORMAT) for t in columns[0]]

        self.target = [float(p) for p in columns[-1]]
        self.newTarget = self.target[:]

    def addAttack(self):
        """Open the attack dialog and get the attack parameters."""

        dialog = AttackDialog(self)
        if dialog.exec_():
            startdate, duration, intensity = dialog.get_info()
        else:
            return

        enddate = startdate + dt.timedelta(minutes=duration)
        if enddate < self.time[0] or startdate > self.time[-1]:
            warningMessage = QtGui.QMessageBox()
            warningMessage.setWindowTitle("Warning")
            warningMessage.setText("Attack out of range.")
            warningMessage.setIcon(QtGui.QMessageBox.Warning)
            warningMessage.exec_()
            return
            
        print time.mktime(startdate.timetuple())
        print time.mktime(enddate.timetuple())

        # TODO: Catch potential StopIteration errors
        start_id = next(id for id, val in enumerate(self.time) if val > startdate)
        end_id = next(id for id, val in enumerate(self.time) if val > enddate)
        while start_id < end_id:
            self.newTarget[start_id] += intensity
            start_id += 1
                
        self.attackWidget.addAttackEntry(startdate, duration, intensity)
        self.powerGraph.graphData(self.time, self.newTarget)
        self.powerGraph.colorSpan(startdate, duration, 'red')
        self.statusBar().showMessage("Graphing complete.", 5000)
        
        
class FileWidget(QtGui.QWidget):

    """Widget to handle browsing the file system and saving files."""

    def __init__(self, parent):
        """Create the main widget and all children."""

        super(FileWidget, self).__init__(parent=parent)
        layout = QtGui.QGridLayout()

        #title = QtGui.QLabel("Choose a file to graph: ", self)
        #title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        inputLabel = QtGui.QLabel("Input file: ", self)
        attackLabel = QtGui.QLabel("New file (with attacks): ", self)
        resultsLabel = QtGui.QLabel("Results file: ", self)
        self.inputEdit = QtGui.QLineEdit(self)
        self.inputEdit.setEnabled(False)
        self.attackEdit = QtGui.QLineEdit(self)
        self.resultsEdit = QtGui.QLineEdit(self)
        browse = QtGui.QPushButton('Browse...')
        browse.clicked.connect(parent.browseFile)
        save = QtGui.QPushButton('Save')
        save.clicked.connect(self.saveAttackFile)

        #layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(inputLabel, 1, 0)
        layout.addWidget(attackLabel, 2, 0)
        layout.addWidget(resultsLabel, 3, 0)
        layout.addWidget(self.inputEdit, 1, 1)
        layout.addWidget(self.attackEdit, 2, 1)
        layout.addWidget(self.resultsEdit, 3, 1)
        layout.addWidget(browse, 1, 2)
        layout.addWidget(save, 2, 2)
        self.setLayout(layout)

    def saveAttackFile(self):
        print "saving attack file"


class AttackWidget(QtGui.QWidget):

    """Widget to handle browsing the file system and saving files."""

    def __init__(self, parent):
        """Create the main widget and all children."""

        super(AttackWidget, self).__init__(parent=parent)
        self.layout = QtGui.QVBoxLayout()
        
        title = QtGui.QLabel("Inject Attacks: ", self)
        title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.attackButton = QtGui.QPushButton("Add Attack...", self)
        self.attackButton.clicked.connect(parent.addAttack)
        self.layout.addWidget(title)
        self.layout.addWidget(self.attackButton)
        self.setLayout(self.layout)

        self.attackList = []
        
    def addAttackEntry(self, start, duration, intensity):
        entryLabel = QtGui.QLabel(
            "Start date: %s, Duration: %d minutes, Intensity: %.3f Watts" % (start, duration, intensity),
            self)
        self.attackList.append(entryLabel)
        self.layout.addWidget(entryLabel)

        
class AlgoWidget(QtGui.QWidget):

    """Widget to handle starting the algorithm and changing settings."""

    def __init__(self, parent):
        """Create the main widget and all children."""

        super(AlgoWidget, self).__init__(parent=parent)
        self.layout = QtGui.QFormLayout()
        
        title = QtGui.QLabel("Run Analysis: ", self)
        title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))   
        
        #TODO: input validation
        emaEdit = QtGui.QLineEdit("1.0", self)
        severityLayout = QtGui.QVBoxLayout()
        severityLayout.addWidget(QtGui.QRadioButton("w=0.53, L=3.714", self)) # Most sensitive
        severityLayout.addWidget(QtGui.QRadioButton("w=0.84, L=3.719", self)) # Medium sensitive
        severityLayout.addWidget(QtGui.QRadioButton("w=1.00, L=3.719", self)) # Least sensitive
        startButton = QtGui.QPushButton("Start Analysis", self)
    
        self.layout.addRow(title)
        self.layout.addRow("EMA level (value in range (0, 1]: ", emaEdit)
        self.layout.addRow("Severity sensitivity parameters: ", severityLayout)
        self.layout.addRow(startButton)
        self.setLayout(self.layout)
        
        
        
        
        
        
        

#==================== MAIN ====================#
def main():
    app = QtGui.QApplication(sys.argv)
    toplevel = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

