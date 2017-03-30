#!/usr/bin/python

# This module contains the funcitons related to the time

import time


def get_time_str(years=True, div='.'):
    """
    Get the current time, and return it as a string
    If years is True, the output string will include the year
    information
    return:
        A string discribe the current time, e.g.
        20160304.0234.32 (years=True)
        0304.0234.32 (years=False)
    """
    st_time = time.localtime()
    year = str(st_time.tm_year)
    month = '%02d' % st_time.tm_mon
    day = '%02d' % st_time.tm_mday
    hour = '%02d' % st_time.tm_hour
    mi = '%02d' % st_time.tm_min
    sec = '%02d' % st_time.tm_sec

    time_str = month + day + div + hour + mi + div + sec
    if years:
        return year + time_str
    else:
        return time_str


def sec2time(iItv):
    if type(iItv) == int or type(iItv) == float:
        ms = str(iItv - int(iItv))
        ms_parts = ms.split('.')
        ms_str = ms_parts[-1]
        if len(ms_str) > 4:
            ms_str = ms_str[:4]
        iItv = int(iItv)
        h = iItv / 3600
        sUp_h = iItv - 3600 * h
        m = sUp_h / 60
        sUp_m = sUp_h - 60 * m
        s = sUp_m
        hms = ":".join(map(str, (h, m, s)))
        return hms + '.' + ms_str
    else:
        return "[InModuleError]:itv2time(iItv) invalid argument type"
