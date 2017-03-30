#!/usr/bin/python

# This is a tool box contains the tools which can analyze the given data
# distribution, and draw the distribution plot

import numpy as np
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt
from scipy.stats import norm
import glog as log


def gmm1d(data_list, n=1, num=100):
    """
    Use the gaussian mix model to fit the data, and draw the data distribution
    Param:
        data_list: The list or np.array contains all 1-dim data
        n:      The component number of the gmm model
        num:    The number of points which used to display the curve
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

    x_list = np.arange(data_list.min(), data_list.max(),
                       (data_list.max() - data_list.min()) / float(num))
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

    # Plot the data
    fig, axis = plt.subplots(1, 1)

    for i in range(len(gauss_mixt)):
        axis.plot(x_list, gauss_mixt[i], label='Gaussian '+str(i))

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
