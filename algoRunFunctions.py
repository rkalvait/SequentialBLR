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


def tf_train(X_train, y_train):
    
    ##### TENSORFLOW ADDITIONS #####

    before_time = time.time()

    with graph.as_default():

        graph.__init__()

        # First turn y_train into a [n, 1] matrix
        y_train = np.reshape(y_train, (len(y_train), 1))

        # If data values are too large, analysis will not converge
        # Divide both X and y by the same value so that W is not affected
        (X_rows, X_cols) = np.shape(X_train)
        divisor = min(X_train.max(), y_train.max())

        for (x, y), value in np.ndenumerate(X_train):
            X_train[x, y] /= divisor

        for (x, y), value in np.ndenumerate(y_train):
            y_train[x, y] /= divisor

        W = tf.Variable(tf.zeros([X_cols, 1]))      # Weight matrix
        b = tf.Variable(tf.zeros([1]))

        # y = W*x
        y = tf.matmul(X_train, W)

        # Minimize the mean squared errors
        loss = tf.reduce_mean(tf.square(y - y_train))
        train_step = tf.train.GradientDescentOptimizer(0.5).minimize(loss)

        # Initialize variables and session
        init = tf.initialize_all_variables()
        sess = tf.Session()
        sess.run(init)

        # Train the model
        for iter in xrange(100):
            sess.run(train_step)

        # Return the model parameters
        print 'Training Loss:', sess.run(loss)

        w_opt = np.transpose(sess.run(W))

        print "Time elapsed: ", time.time() - before_time
        
        return w_opt
    

def train(X, y):
    # This function is used for training our Bayesian model
    # Returns the regression parameters w_opt, and alpha, beta, S_N
    # needed for the predictive distribution

    before_time = time.time()

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

    print "Time elapsed: ", time.time() - before_time

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
