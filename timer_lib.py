#!/usr/bin/python

# This module provide a simple timer class
# It can mark the time interval and convert the time interval
# to multi format

import time
import glog as log
import time_tools


class timer:
    """
    This class is used to do a simple counter job
    It can count the time interval and output the readable string
    """
    def __init__(self, start=False):
        """
        IF the start set to True, the timer will start without
        calling the start funciton
        """
        if start:
            self._start = time.time()
        else:
            self._start = None

        self._end = None
        self._interval = None

    def start(self):
        """
        Start the timer
        """
        self._start = time.time()
        self._interval = None

    def stop(self):
        """
        Stop the timer
        """
        if self._start is None:
            log.error('\033[01;31mERROR\033[0m: The timer is not running.')
            return
        self._end = time.time()
        self._interval = self._end - self._start
        self._start = None

    def to_str(self):
        """
        Return the interval time in readable string
        HH:MM:SS.ms
        """
        if self._interval is None:
            log.error('\033[01;31mERROR\033[0m: The timer is STILL running.')
            return None
        return time_tools.sec2time(self._interval)

    def interval(self):
        """
        Return the interval value in seconds
        """
        if self._interval is None:
            log.error('\033[01;31mERROR\033[0m: The timer is STILL running.')
            return None
        return self._interval

    def elapse(self):
        """
        Return the current time elapse in seconds
        """
        if self._start is None:
            log.error('\033[01;31mERROR\033[0m: The timer is not running.')
            return
        return time.time() - self._start
