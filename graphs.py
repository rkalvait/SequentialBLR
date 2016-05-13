# Graphing and analysis functions for use in plotting BLR Results
# Filename:     graphs.py
# Author:       apadin
# Start Date:   5/13/2016

############################################################

import numpy as np
import scipy as sp
import scipy.stats

from algoRunFunctions import movingAverage
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

############################################################


def MSE_results(n_samples, training_size, y_target, y_predictions)):

    prediction_length = n_samples - training_size
    smoothing_win = 120

    y_target = np.asarray(y_target)
    y_predictions = np.asarray(y_predictions)


    
print "PMSE for smoothed: %d" % (PMSE_score_smoothed)
print "PMSE for nonsmoothed: %d" % (PMSE_score)
print "-------------------------------------------------------------------------------------------------"
print "%20s |%20s |%25s |%20s" % ("RMSE-score (smoothed)", "RMSE-score (raw)", "Relative MSE", "SMSE")
print "%20.2f  |%20.2f |%25.2f |%20.2f " % (np.mean(np.asarray(rmse_smoothed)), np.mean(np.asarray(rmse)), np.mean(np.asarray(Re_mse)), np.mean(np.asarray(smse)))
print "-------------------------------------------------------------------------------------------------"
