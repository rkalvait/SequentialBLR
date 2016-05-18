# Functions used for Tensorflow training model
# Filename:     tf_functions.py
# Author:       apadin
# Start Date:   5/13/2016

import numpy as np
import tensorflow as tf

graph = tf.Graph()

## Tensorflow Train ###
def tf_train(X_train, y_train):

    # In order to prevent memory leaks from re-making the graph every time,
    # must clear the operations from the graph on each run
    with graph.as_default():

        graph.__init__() # clear operations

        # First turn y_train into a [n, 1] matrix
        col_length = len(y_train)
        y_train = np.reshape(y_train, (col_length, 1))

        #X_train = np.concatenate((X_train, np.ones([col_length, 1], np.float32)), 1)
        print X_train[0]
        # If data values are too large, analysis will not converge
        # Divide both X and y by the same value so that W is not affected
        (X_rows, X_cols) = np.shape(X_train)
        divisor = min(X_train.max(), y_train.max())

        for (x, y), value in np.ndenumerate(X_train):
            X_train[x, y] /= divisor

        for (x, y), value in np.ndenumerate(y_train):
            y_train[x, y] /= divisor

        W = tf.Variable(tf.zeros([X_cols, 1]))      # Weight matrix

        # y = W*x
        y = tf.matmul(X_train, W)

        # Minimize the mean squared errors
        #loss = tf.reduce_mean(-tf.reduce_sum(y_train * tf.log(y)))
        loss = tf.reduce_mean(tf.square(y - y_train))
        train_step = tf.train.GradientDescentOptimizer(0.5).minimize(loss)

        # Initialize variables and session
        init = tf.initialize_all_variables()
        sess = tf.Session()
        sess.run(init)

        # Train the model
        for iter in xrange(200):
            sess.run(train_step)
            #print "Loss:", sess.run(W)
            #raw_input("press enter")

        print "Loss:", sess.run(loss)

        # Return the model parameters
        w_opt = np.transpose(sess.run(W))
        return w_opt, 1, 1, 1
