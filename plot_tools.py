#!/usr/bin/python

# This model contains the funcitons which as used for plot some statistic image
# and other complex plot job.

import numpy as np
import random
import matplotlib.pyplot as plt
import tools
from scipy.stats import gaussian_kde


def plot_bar(input_dict, save_file_name=None, bar_wide=0.8):
    """ This function accept and input dict, The key is int or float
    type, and the val is int type.
    such as {1:23, 2:2, 41:43, 23:5}
    The key is considered as the X axis label
    and the corresponding value is considered as the Y axis
    A bar map will be ploted
    """
    plt.bar(input_dict.keys(), input_dict.values(), bar_wide)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def plot_list_bar(input_list, start_label=0, save_file_name=None,
                  bar_wide=0.8):
    """ Different from the plot_bar, this function accept the input as a list
    instead of the dict
    This function accept and input dict, The key is int or float
    type, and the val is int type.
    such as {1:23, 2:2, 41:43, 23:5}
    The key is considered as the X axis label
    and the corresponding value is considered as the Y axis
    A bar map will be ploted
    """
    keys = range(start_label, start_label+len(input_list))
    plt.bar(keys, input_list, bar_wide)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def plot_label_bar(data_list, label_list, save_file_name=None,
                   bar_wide=0.8):
    """
    This function is similar with the plot_list_bar, but instead
    of the number label, this function can disp the text label
    """
    if len(data_list) != len(label_list):
        print('\033[01;33mWARNING\033: The length of data_list and \
label_list not match. %d vs %d' % (len(data_list), len(label_list)))
    keys = range(0, len(data_list))
    plt.bar(keys, data_list, bar_wide, align='center')
    plt.xticks(keys, label_list)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def plot_label_bars(data_lists, label_list, std_lists=None,
                    legend_list=None, save_file_name=None, display_val=False,
                    group_width=0.75):
    """
    This function is an extension of the plot_label_bar function, it can
    plot multiple bar into one group, which is commonly used for comparision
    Params:
        data_lists:     A list of the data_list, note all data_list inside the
                        data_lists should be equal length
        label_list:     The label list
        std_lists:      This function can also display the standard variant of
                        the data, it has the same shape as data_lists
        legend_list:    Set if want to display the text legend
        save_file_name: Set if want to save the plotted bar
        display_val:    Set True if want to display the value on top of the bar
        group_width:    The width of the group, should be smaller than 1
    """
    # Calc the width of each bar
    group_size = len(data_lists)
    bar_width = group_width / group_size
    # The general x index
    ind = np.arange(len(label_list))
    fig, ax = plt.subplots()

    rect_list = []
    rect0_list = []
    # Iter the group
    for idx in range(len(data_lists)):
        if std_lists is not None:
            std = std_lists[idx]
        else:
            std = None
        data_list = data_lists[idx]
        color = [random.random(), random.random(), random.random()]
        rect = ax.bar(ind+idx*bar_width, data_list, bar_width,
                      color=color, yerr=std)
        rect_list.append(rect)
        rect0_list.append(rect[0])

    # Set the label
    ax.set_xticks(ind+group_width/2.0)
    ax.set_xticklabels(label_list)

    # Set legend
    if legend_list is not None:
        ax.legend(rect0_list, legend_list)

    # Mark the value of bar if needed
    if display_val:
        for rect in rect_list:
            _autolabel(rect, ax)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def normalize_image(img):
    """Since the matplotlib.pyplot only support the float image pixel between
    [0, 1], the uint8 image pixel between [0-255], the image must be normalized
    before display.
    This function will normalize the image to float [0-1].
    Return the normalized image
    """
    img = img.astype('float32')
    maxval = img.max()
    minval = img.min()
    diff = maxval - minval
    img = img - minval
    img = img / diff
    return img


def plot_line(input_dict, save_file_name=None, *inputs):
    """ This function draw a line figure according to the input_dict
    The format of input_dict is the same as the plot_bar used:
    The keys are X value, and the vals are Y value
    If the save_file_name is set, the plot image will be saved on disk
    """
    x = input_dict.keys()
    x.sort()
    y = tools.sorted_dict_values(input_dict)
    plt.plot(x, y, 'r')
    # Loop the remain inputs
    for cmp_dict in inputs:
        x = cmp_dict.keys()
        x.sort()
        y = tools.sorted_dict_values(cmp_dict)
        plt.plot(x, y)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def plot_scatter(points_list, save_file_name=None):
    """
    This function plot the points on a figure. The input points_list
    contains many [x, y] list. They will be ploted on a figure

    The format of the points_list is
    [[x1, y1], [x2, y2], ...]
    """
    # Change the points_list format
    x_list = []
    y_list = []
    for point in points_list:
        x_list.append(point[0])
        y_list.append(point[1])
    # Draw the points
    plt.scatter(x_list, y_list)
    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def plot_scatter2(points_list, save_file_name=None, color=False):
    """
    This function plot the points on a figure. The input points_list
    contains many [x, y] list. They will be ploted on a figure

    The format of the points_list is
    [[x1, y1], [x2, y2], ...]

    If color is True, the plot will be show in color according to the
    points' density

    Different from the plot_scatter, this function tend to deal with
    large mount of points
    """
    # Change the points_list format
    x_list = []
    y_list = []
    for point in points_list:
        x_list.append(point[0])
        y_list.append(point[1])

    if color:
        xy = np.vstack([x_list, y_list])
        z = gaussian_kde(xy)(xy)
        plt.scatter(x_list, y_list, c=z, marker='.', edgecolor='')
    else:
        # Draw the points
        plt.scatter(x_list, y_list, marker='.', edgecolor='')

    if save_file_name is not None:
        plt.savefig(save_file_name)
    plt.show()


def _autolabel(rects, ax):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')
