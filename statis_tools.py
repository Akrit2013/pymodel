#!/usr/bin/python

# This is a tool box contains the tools which can analyze the given data
# distribution, and draw the distribution plot

import numpy as np
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
import random
from scipy.stats import norm
import glog as log
import pdb


def gmm1d(data_list, n=1, num=100):
    """
    Use the gaussian mix model to fit the data, and draw the data distribution
    Param:
        data_list: The list or np.array contains all 1-dim data
        n:      The component number of the gmm model
        num:    The number of points which used to display the curve
        """

    # Fit the gmm
    x_list, gauss_mixt = _gmm1d(data_list, n, num)

    # Plot the data
    fig, axis = plt.subplots(1, 1)

    for i in range(len(gauss_mixt)):
        axis.plot(x_list, gauss_mixt[i], label='Gaussian '+str(i))

    plt.show()


def gmms1d(data_lists, n=1, num=100):
    """
    This function is similar to gmm1d
    The differece is, the data_lists is composed by multiple data_list
    and each of them can be fit into a gmm
    In the end, all gmms will be displayed
    """
    # Find the max and min value of all data
    max_val = float('-inf')
    min_val = float('inf')
    for data_list in data_lists:
        if np.max(data_list) > max_val:
            max_val = np.max(data_list)
        if np.min(data_list) < min_val:
            min_val = np.min(data_list)
    start = min_val
    end = max_val
    # The list to store the returned gmm
    gauss_mixt_list = []
    # Iter the datalist
    for data_list in data_lists:
        x_list, gmm_mixt = _gmm1d(data_list, n, num, start, end)
        gauss_mixt_list.append(gmm_mixt)

    # Plot the data
    fig, axis = plt.subplots(1, 1)

    for gauss_mixt in gauss_mixt_list:
        color = [random.random(), random.random(), random.random()]
        for i in range(len(gauss_mixt)):
            axis.plot(x_list, gauss_mixt[i],
                      label='Gaussian '+str(i), color=color)

    plt.show()


def plot1d(data_list):
    """
    Plot the 1d data to show the data distribution.
    The x axis is the label number, and the y axis is the data
    """
    data_list = np.array(data_list).flatten()
    x_list = np.arange(data_list.shape[0])
    fig, axis = plt.subplots(1, 1)
    axis.plot(x_list, data_list)
    plt.show()


def _gmm1d(data_list, n=1, num=100, start=None, end=None):
    """
    The backend for fitting the 1d gmm model without display
    The return value is a list of a list
    which contains the points of each gaussian model
    Param:
        data_list: The list or np.array contains all 1-dim data
        n:      The component number of the gmm model
        num:    The number of points which used to display the curve
        start:  The start x label for drawing the gmm curve
        end:    The end x label for drawing the gmm curve
    """

    data_list = np.array(data_list)
    length = data_list.flatten().shape[0]
    # Init the gmm
    gmm = GaussianMixture(n_components=n)
    gmm.fit(np.reshape(data_list, (length, 1)))

    # Check if success
    if gmm.converged_:
        log.info('Fit \033[01;32mSUCCESSFUL\033[0m')
    else:
        log.warn('Fit \033[01;31mFAILED\033[0m')

    if start is None:
        start = data_list.min()
    if end is None:
        end = data_list.max()

    x_list = np.arange(start, end, (end - start) / float(num))

    gauss_mixt = \
        np.array([p * norm.pdf(x_list, mu, sd)
                 for mu, sd, p in zip(gmm.means_.flatten(),
                                      np.sqrt(gmm.covariances_.flatten()),
                                      gmm.weights_)])

    # Display the distribution info
    for mu, sd, p in zip(gmm.means_.flatten(),
                         np.sqrt(gmm.covariances_.flatten()),
                         gmm.weights_):
        log.info('Model Weight: \033[01;31m%f\033[0m, \
mean: \033[01;32m%f\033[0m, std: \033[01;33m%f\033[0m' % (p, mu, sd))

    return x_list, gauss_mixt
