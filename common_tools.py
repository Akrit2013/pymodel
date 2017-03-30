#!/usr/bin/python

# This toolbox contains the common tools should be used
# in general perpose

import decimal


def frange(x, y, jump):
    """
    A float version of the range
    Use decimal to avoid the value such as 0.999999
    """
    rst_list = []
    x = decimal.Decimal(str(x))
    while x < y:
        rst_list.append(float(x))
        x += decimal.Decimal(str(jump))
    return rst_list
