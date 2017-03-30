#!/usr/bin/python

# This script contains some self-made tool functions

import sys
import numpy as np
import termios
import collections
import os


def get_char():
    """This function return a char from the terminal WITHOUT echo the
    input.
    """
    # Flush the stdin first
    termios.tcflush(sys.stdin, termios.TCIFLUSH)
    # Flush the stdout
    sys.stdout.flush()
    # Get the std input descriptor
    fd = sys.stdin.fileno()

    # Get the std terminal setting
    old_ttyinfo = termios.tcgetattr(fd)

    # Re config the terminal
    new_ttyinfo = old_ttyinfo[:]

    # Use no-std mode
    new_ttyinfo[3] &= ~termios.ICANON
    # Turn off the echo
    new_ttyinfo[3] &= ~termios.ECHO

    # Set the new setting to the terminal
    termios.tcsetattr(fd, termios.TCSANOW, new_ttyinfo)
    # Read char from terminal
    ch = os.read(fd, 7)

    # Set back the original setting
    termios.tcsetattr(fd, termios.TCSANOW, old_ttyinfo)

    return ch


def sorted_dict_values(adict):
    """This function is very useful, it sort the dict's values according
    to the keys of the dict (small to large).
    The sorted value list will be returned
    It is very useful when use plt.plot a figure from a dict
    """
    keys = adict.keys()
    keys.sort()
    return map(adict.get, keys)


def sort_lists(base_list, target_list):
    """
    Sort the base_list first (small to large), and then sort the target_list
    according to the sorted order of the base_list
    The return value will be sorted base_list, target_list
    """
    if len(base_list) != len(target_list):
        print('\033[01;31mERROR\033[0m: The length of base_list and target_list \
must be the same. %d vs %d' % (len(base_list), len(target_list)))
        return

    # Merge the lists into a dict
    tmpdict = dict(zip(base_list, target_list))
    # Sort the base_list
    base_list.sort()
    # Get the sorted target_list
    target_list = map(tmpdict.get, base_list)
    return base_list, target_list


class colors:
    BLACK = '\033[0;30m'
    DARK_GRAY = '\033[1;30m'
    LIGHT_GRAY = '\033[0;37m'
    BOLD_GRAY = '\033[01;37m'
    BLUE = '\033[0;34m'
    LIGHT_BLUE = '\033[1;34m'
    BOLD_BLUE = '\033[01;34m'
    GREEN = '\033[0;32m'
    LIGHT_GREEN = '\033[1;32m'
    BOLD_GREEN = '\033[01;32m'
    CYAN = '\033[0;36m'
    LIGHT_CYAN = '\033[1;36m'
    BOLD_CYAN = '\033[01;36m'
    RED = '\033[0;31m'
    LIGHT_RED = '\033[1;31m'
    BOLD_RED = '\033[01;31m'
    PURPLE = '\033[0;35m'
    LIGHT_PURPLE = '\033[1;35m'
    BOLD_PURPLE = '\033[01;35m'
    BROWN = '\033[0;33m'
    YELLOW = '\033[1;33m'
    BOLD_YELLOW = '\033[01;33m'
    WHITE = '\033[1;37m'
    DEFAULT_COLOR = '\033[00m'
    ENDC = '\033[0m'


def get_pure_name(full_name):
    """This function get the pure name from a full file name.
    which is, the path name and the ext name will be ignored.
    For Example: if the input is /home/nile/something.jpg
    The return value is the 'something'
    """
    return os.path.splitext(os.path.split(full_name)[-1])[0]


def get_most_frequent_ele(a_list):
    """Return the most frequent appear value in the given list
    """
    rst = collections.Counter(a_list)
    keys = rst.keys()
    freqs = rst.values()
    max_val = max(freqs)
    idx = freqs.index(max_val)
    return keys[idx]


def merge_list(*arglist):
    """
    Merge all the list into one and return, and the elements
    will not be repeated
    """
    rst_list = []
    for sublist in arglist:
        for ele in sublist:
            if ele in rst_list:
                continue
            rst_list.append(ele)

    return rst_list


def rgb2gray(rgb):
    """
    Convert the rgb image gray, the type will be np.uint8
    """
    rgb = np.array(rgb)
    gray = np.dot(rgb[..., :3], [0.299, 0.587, 0.144])
    gray = gray.round()
    return gray.astype(np.uint8)
