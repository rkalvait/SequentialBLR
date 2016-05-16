from urllib import urlopen
import json
import time
import numpy as np
import scipy as sp
import sys
import scipy.stats

import os

#import tensorflow as tf

import sys
import scipy as sp
import scipy.stats

#graph = tf.Graph()

debug = 0

def movingAverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

def runnable(arrayIn):
    countAll = 0
    countValid = 0
    for row in arrayIn:
        for datum in row:
            countAll += 1
            if int(datum) is not -1:
                countValid += 1

    return float(countValid)/countAll
    
def train(X, y):
    # This function is used for training our Bayesian model
    # Returns the regression parameters w_opt, and alpha, beta, S_N
    # needed for the predictive distribution

    Phi = X # the measurement matrix of the input variables x (i.e., features)
    t   = y # the vector of observations for the target variable
    (N, M) = np.shape(Phi)
    # Init values for  hyper-parameters alpha, beta
    alpha = 5*10**(-3)
    beta = 5
    max_iter = 100
    k = 0

    PhiT_Phi = np.dot(np.transpose(Phi), Phi)
    s = np.linalg.svd(PhiT_Phi, compute_uv=0) # Just get the vector of singular values s

    ab_old = np.array([alpha, beta])
    ab_new = np.zeros((1,2))
    tolerance = 10**-3
    while( k < max_iter and np.linalg.norm(ab_old-ab_new) > tolerance):
        k += 1
        try:

            S_N = np.linalg.inv(alpha*np.eye(M) + beta*PhiT_Phi)
        except np.linalg.LinAlgError as err:
            print  "******************************************************************************************************"
            print "                           ALERT: LinearAlgebra Error detected!"
            print "      CHECK if your measurement matrix is not leading to a singular alpha*np.eye(M) + beta*PhiT_Phi"
            print "                           GOODBYE and see you later. Exiting ..."
            print  "******************************************************************************************************"
            sys.exit(-1)

        m_N = beta * np.dot(S_N, np.dot(np.transpose(Phi), t))
        gamma = sum(beta*s[i]**2 /(alpha + beta*s[i]**2) for i in range(M))
        #
        # update alpha, beta
        #
        ab_old = np.array([alpha, beta])
        alpha = gamma /np.inner(m_N,m_N)
        one_over_beta = 1/(N-gamma) * sum( (t[n] - np.inner(m_N, Phi[n]))**2 for n in range(N))
        beta = 1/one_over_beta
        ab_new = np.array([alpha, beta])

    S_N = np.linalg.inv(alpha*np.eye(M) + beta*PhiT_Phi)
    m_N = beta * np.dot(S_N, np.dot(np.transpose(Phi), t))
    w_opt = m_N

    return (w_opt, alpha, beta, S_N)


def severityMetric(error, mu, sigma, w, Sn_1):
    # This function returns the values of the EWMA control chart. It returns the
    # Sn values, as described in the paper.

    if error < mu: # left-tailed
        p_value = sp.stats.norm.cdf(error, mu, sigma)
        Zt = sp.stats.norm.ppf(p_value) # inverse of cdf N(0,1)
    else: # right-tailed
        p_value = 1 - sp.stats.norm.cdf(error, mu, sigma)
        Zt = sp.stats.norm.ppf(1-p_value) # inverse of cdf N(0,1)


    if Zt > 10:
        Zt = 10
    elif Zt < -10:
        Zt = -10

    Sn = (1-w)*Sn_1 + w*Zt

    if debug:
        if np.abs(Zt) > 90:
            print "Error = %d, p-value=%.3f, Z-score=%.3f, Sn_1=%.2f, Sn=%.2f " % (error, p_value, Zt, Sn_1, Sn)
        elif np.abs(Zt) < 0.005:
            print "Error = %d, p-value=%.3f, Z-score=%.3f, Sn_1=%.2f, Sn=%.2f " % (error, p_value, Zt, Sn_1, Sn)

    return Sn, Zt
