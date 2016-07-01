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
from algo import Algo
from attacker import AttackDialog
from grapher import LoadingWindow, ResultsGraph, PowerGraph
from algoFunctions import f1_scores, print_stats, readResults, writeResults


#==================== GUI CLASSES ====================#

class MainWindow(QtGui.QMainWindow):

    """The main window of the application."""

    def __init__(self):
        """Initialize the main window and create all child widgets."""

        super(MainWindow, self).__init__()
        self.setGeometry(50, 50, 1200, 600)
        self.setWindowTitle('CSV Data Analysis')
        self.setWindowIcon(QtGui.QIcon(ICON_FILE))
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
        
        # Left-side is sidebar
        self.sidebarLayout = QtGui.QVBoxLayout()
        self.fileWidget = self.createFileWidget()
        self.attackWidget = self.createAttackWidget()
        self.attackWidget.setEnabled(False)
        self.algoWidget = self.createAlgoWidget()
        self.algoWidget.setEnabled(False)
        self.sidebarLayout.addWidget(self.fileWidget)
        self.sidebarLayout.addWidget(self.attackWidget)
        self.sidebarLayout.addWidget(self.algoWidget)
        self.sidebarLayout.addWidget(QtGui.QLabel(""), stretch=1)

        # Right-side is graph and toolbar
        #self.resultsGraph = ResultsGraph(parent=mainWidget)
        #self.resultsGraph.hide()
        self.graphWidget = QtGui.QWidget(mainWidget)
        self.powerGraph = PowerGraph(self.graphWidget)
        self.toolbar = NavigationToolbar(self.powerGraph, self.graphWidget)
        self.graphLayout = QtGui.QVBoxLayout()
        self.graphLayout.addWidget(self.powerGraph)
        self.graphLayout.addWidget(self.toolbar)

        # Add children to layout and set focus to main widget
        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addLayout(self.sidebarLayout)
        mainLayout.addLayout(self.graphLayout, stretch=1)
        mainWidget.setLayout(mainLayout)
        return mainWidget

    def createFileWidget(self):
        """Create the file browsing section"""

        mainWidget = QtGui.QWidget(self)
        title = QtGui.QLabel("Choose the input file: ")
        title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))

        self.inputEdit = QtGui.QLineEdit()
        self.inputEdit.setEnabled(False)
        self.attackEdit = QtGui.QLineEdit()
        self.resultsEdit = QtGui.QLineEdit()
        
        spacer = QtGui.QLabel("", )
        browse = QtGui.QPushButton('Browse...', )
        browse.clicked.connect(self.browseFile)
        save = QtGui.QPushButton('Save Attacks', )
        save.clicked.connect(self.saveAttackFile)
        
        layout = QtGui.QGridLayout()
        layout.addWidget(title, 0, 0, 1, -1)
        layout.addWidget(self.inputEdit, 1, 0)
        layout.addWidget(self.attackEdit, 2, 0)
        layout.addWidget(self.resultsEdit, 3, 0)
        layout.addWidget(browse, 1, 1)
        layout.addWidget(save, 2, 1)
        
        mainWidget.setLayout(layout)
        return mainWidget

    def createAttackWidget(self):
        """Create the attack section."""

        # TODO: Keep track of attacks so they can be removed later
        self.attackList = []

        mainWidget = QtGui.QWidget(self)
        title = QtGui.QLabel("Inject Attacks: ", mainWidget)
        title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        attackButton = QtGui.QPushButton("Add Attack...", mainWidget)
        attackButton.clicked.connect(self.addAttack)
        clearButton = QtGui.QPushButton("Clear All", mainWidget)
        clearButton.clicked.connect(self.clearAttacks)
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(attackButton)
        buttonLayout.addWidget(clearButton)
        
        self.attackLayout = QtGui.QVBoxLayout()
        self.attackLayout.addWidget(title)
        self.attackLayout.addLayout(buttonLayout)
        mainWidget.setLayout(self.attackLayout)
        return mainWidget

    def createAlgoWidget(self):
        """Create the analysis section."""

        mainWidget = QtGui.QWidget(self)
        title = QtGui.QLabel("Run Analysis: ", mainWidget)
        title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))

        #TODO: input validation
        self.emaEdit = QtGui.QDoubleSpinBox(mainWidget)
        self.emaEdit.setDecimals(3)
        self.emaEdit.setRange(0.001, 1)
        self.emaEdit.setSingleStep(0.01)
        self.emaEdit.setValue(1.0)

        self.severityButton1 = QtGui.QRadioButton("w=1.00, L=3.719", mainWidget)     
        self.severityButton2 = QtGui.QRadioButton("w=0.84, L=3.719", mainWidget)
        self.severityButton3 = QtGui.QRadioButton("w=0.53, L=3.714", mainWidget)
        self.severityButtonOther = QtGui.QRadioButton("Other", mainWidget)
        buttonLayout = QtGui.QVBoxLayout()
        buttonLayout.addWidget(self.severityButton1)
        buttonLayout.addWidget(self.severityButton2)
        buttonLayout.addWidget(self.severityButton3)
        buttonLayout.addWidget(self.severityButtonOther)
        buttonBox = QtGui.QWidget()
        buttonBox.setLayout(buttonLayout)
        
        self.severitySpinW = QtGui.QDoubleSpinBox(mainWidget)
        self.severitySpinL = QtGui.QDoubleSpinBox(mainWidget)
        self.severitySpinW.setDecimals(3)
        self.severitySpinL.setDecimals(3)
        self.severitySpinW.setRange(0, 1)
        self.severitySpinL.setRange(0, 10)
        self.severitySpinW.setSingleStep(0.01)
        self.severitySpinL.setSingleStep(0.01)
        self.severitySpinW.setEnabled(False)
        self.severitySpinL.setEnabled(False)
        
        def toggleSpinBoxes():
            if self.severityButtonOther.isChecked():
                self.severitySpinW.setEnabled(True)
                self.severitySpinL.setEnabled(True)
            else:
                self.severitySpinW.setEnabled(False)
                self.severitySpinL.setEnabled(False)
                if self.severityButton1.isChecked():
                    self.severitySpinW.setValue(1)
                    self.severitySpinL.setValue(3.719)
                elif self.severityButton2.isChecked():
                    self.severitySpinW.setValue(.84)
                    self.severitySpinL.setValue(3.719)
                elif self.severityButton3.isChecked():
                    self.severitySpinW.setValue(.53)
                    self.severitySpinL.setValue(3.714)

        self.severityButton1.toggled.connect(toggleSpinBoxes)
        self.severityButton2.toggled.connect(toggleSpinBoxes)
        self.severityButton3.toggled.connect(toggleSpinBoxes)
        self.severityButtonOther.toggled.connect(toggleSpinBoxes)
        self.severityButton1.toggle() #Default
        
        spinLayout = QtGui.QVBoxLayout()
        spinLayout.addWidget(QtGui.QLabel("w:    "))
        spinLayout.addWidget(self.severitySpinW)
        spinLayout.addWidget(QtGui.QLabel("L:    "))
        spinLayout.addWidget(self.severitySpinL)
        
        startButton = QtGui.QPushButton("Start Analysis", mainWidget)
        startButton.clicked.connect(self.startAnalysis)

        layout = QtGui.QFormLayout()
        layout.addRow(title)
        layout.addRow("EMA level (aka alpha): ", self.emaEdit)
        layout.addRow(QtGui.QLabel("Severity sensitivity parameters: "))
        layout.addRow(buttonBox, spinLayout)
        layout.addRow(startButton)
        mainWidget.setLayout(layout)
        return mainWidget
        

    #==================== HELPER FUNCTIONS ====================#

    def browseFile(self):
        """Choose a file using the file search dialog."""

        filename = str(QtGui.QFileDialog.getOpenFileName())
        if (filename != ''):
            self.checkInputFilename(filename) #Raises exception if not CSV file
            self.inputEdit.setText(filename)
            filename = filename.rstrip('.csv')
            self.attackEdit.setText(filename + '_attacked.csv')
            self.resultsEdit.setText(filename + '_results.csv')

            self.loadInputFile() #Load times and power into self.time, self.target
            self.powerGraph.graphData(self.time, self.target)
            self.statusBar().showMessage("Graphing complete.", 5000)
            self.attackWidget.setEnabled(True)
            self.algoWidget.setEnabled(True)

    def checkInputFilename(self, filename):
        """Return if the given filename is valid, raise exception otherwise"""

        if filename == '':
            self.warningDialog("No file specified.")
            raise ValueError("No file specified.")

        elif filename[-4:] != '.csv':
            self.warningDialog("File must have '.csv' extension.")
            raise ValueError("File must have '.csv' extension.")

    def loadInputFile(self):
        """Load power data from the input file."""

        csvfile = str(self.inputEdit.text())
        with open(csvfile, 'rb') as infile:
            reader = csv.reader(infile)
            reader.next()
            columns = zip(*reader)
        self.time = [dt.datetime.fromtimestamp(float(t)) for t in columns[0]]
        self.target = [float(p) for p in columns[-1]]
        self.newTarget = self.target[:]
        '''
        # Convert times from string or timestamp to datetime
        try:
            self.time = [dt.datetime.fromtimestamp(float(t)) for t in columns[0]]
        except ValueError:
            self.time = [dt.datetime.strptime(t, DATE_FORMAT) for t in columns[0]]
        '''

    def addAttack(self):
        """Open the attack dialog and get the attack parameters."""

        dialog = AttackDialog(self)
        if dialog.exec_():
            startdate, duration, intensity = dialog.get_info()
        else:
            return

        enddate = startdate + dt.timedelta(minutes=duration)
        if enddate < self.time[0] or startdate > self.time[-1]:
            self.warningDialog("Attack out of range.")
            return
        
        # TODO: Catch potential StopIteration errors
        start_id = next(id for id, val in enumerate(self.time) if val > startdate)
        end_id = next(id for id, val in enumerate(self.time) if val > enddate)
        while start_id < end_id:
            self.newTarget[start_id] += intensity
            start_id += 1
            
        class Attack(QtGui.QLabel):
            def __init__(self, parent, start, duration, intensity):
                super(Attack, self).__init__(parent)
                self.start = start
                self.end = start + dt.timedelta(minutes=duration)
                self.setText("At time %s, %.2f Watts for %d minutes"
                          % (start, intensity, duration))

        newAttack = Attack(self, startdate, duration, intensity)
        self.attackList.append(newAttack)
        self.attackLayout.addWidget(newAttack)

        self.powerGraph.graphData(self.time, self.newTarget)
        self.powerGraph.colorSpan(startdate, duration, 'green')
        self.statusBar().showMessage("Graphing complete.", 5000)
        self.algoWidget.setEnabled(False)
        #print time.mktime(startdate.timetuple())
        #print time.mktime(enddate.timetuple())
        
    def clearAttacks(self):
        """Open the attack dialog and get the attack parameters."""
        
        for attack in self.attackList:
            attack.deleteLater()
        self.attackList = []
        self.newTarget = self.target[:]
        self.powerGraph.clear()
        self.powerGraph.graphData(self.time, self.newTarget)
        self.algoWidget.setEnabled(True)

    def saveAttackFile(self):
        """Save the new data in the file given by attackFile."""

        inputFile = str(self.inputEdit.text())
        attackFile = str(self.attackEdit.text())
        self.checkInputFilename(attackFile)
        with open(inputFile, 'rb') as infile, open(attackFile, 'wb') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            writer.writerow(reader.next()) #Copy header row
            count = 0
            for line in reader:
                line[-1] = self.newTarget[count]
                writer.writerow(line)
                count += 1
        self.statusBar().showMessage("File %s saved" % attackFile, 5000)
        self.algoWidget.setEnabled(True)
                
    def warningDialog(self, message="Unknown error occurred."):
        warningMessage = QtGui.QMessageBox()
        warningMessage.setWindowTitle("Warning")
        warningMessage.setText(message)
        warningMessage.setIcon(QtGui.QMessageBox.Warning)
        warningMessage.exec_()

                
    #==================== ALGORITHM ====================#

    def startAnalysis(self):

        # Get parameters
        try:
            alpha = float(self.emaEdit.text())
            assert(alpha > 0.0 and alpha <= 1.0)
        except ValueError:
            self.warningDialog("EMA Level must be a number in range (0, 1].")
            return
        except AssertionError:
            self.warningDialog("EMA Level must be in range (0, 1].")
            return
        
        # TODO: Use attackEdit instead of inputEdit
        if len(self.attackList) > 0: 
            infile = str(self.attackEdit.text())
        else:
            infile = str(self.inputEdit.text())
        outfile = str(self.resultsEdit.text())
        granularity = 1
        trainingWin = 24
        forecastingInterval = 1

        print ("\nStarting analysis on %s with settings %d %d %d..." 
               % (infile, granularity, trainingWin, forecastingInterval))
               
        # Get list of features (first columns is time)
        infile = open(infile, 'rb')
        reader = csv.reader(infile)
        columns = reader.next()[1:]
        
        print "The following features were found:", columns

        print "alpha: ", alpha
        
        # Algorithm settings
        algo = Algo(granularity, trainingWin, forecastingInterval, len(columns)-1)
        algo.setSeverityParameters(w = self.severitySpinW.value(),
                                   L = self.severitySpinL.value())
            
        y_time = ['Timestamp']
        y_target = ['Target']
        y_predict = ['Prediction']
        anomalies = ['Anomaly']

        detected = set()
        ground_truth = set()
        
        first = True
        
        print "Beginning analysis..."
        loadingWin = LoadingWindow()
        self.mainWidget.setEnabled(False)
        count = 0
        for line in reader:

            # Read new data from file
            cur_time = float(line[0])
            new_data = np.asarray(line[1:], np.float)

            # EWMA calculation
            if first: 
                last_avg = new_data
                first = False
            avg_data = last_avg + alpha * (new_data - last_avg)
            last_avg = avg_data

            target = float(avg_data[-1])
            prediction = algo.run(avg_data) # Magic!
            
            if prediction != None:
                y_time.append(cur_time)
                y_target.append(target)
                y_predict.append(float(prediction))
                
                if algo.checkSeverity(target, float(prediction)):
                    detected.add(cur_time)
                    
                    anomalies.append(1)
                else:
                    anomalies.append(0)

            cur_datetime = dt.datetime.fromtimestamp(cur_time)
            for attack in self.attackList:
                if(cur_datetime >= attack.start and cur_datetime < attack.end):
                    ground_truth.add(cur_time)
                    break
                    
            if (count % 60) == 0:
                #print "Trying time: ", cur_time
                QtGui.QApplication.processEvents()
            count += 1
            
             
        # Close the input file and save results
        infile.close()
        writeResults(outfile, (y_time, y_target, y_predict, anomalies))
        self.mainWidget.setEnabled(True)
        loadingWin.close()
        
        f1_scores(detected, ground_truth)
        print_stats(y_target[1:], y_predict[1:]) #Remove header

        print "Ending analysis. See %s for results." % outfile

        
#==================== MAIN ====================#
def main():
    app = QtGui.QApplication(sys.argv)
    toplevel = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

