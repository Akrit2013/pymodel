#!/usr/bin/python

# This module contains the tools related to the display color

import glog as log


class color:
    """
    This class can give the string to certain ANSI color
    """
    def __init__(self, bold=False):
        self._color_table_bold = {
            'black': '\033[1;30m',
            'white': '\033[1;37m',
            'blue': '\033[1;34m',
            'green': '\033[1;32m',
            'cyan': '\033[1;36m',
            'red': '\033[1;31m',
            'purple': '\033[1;35m',
            'yellow': '\033[1;33m',
            'default': '\033[0m'}

        self._color_table_light = {
            'black': '\033[30m',
            'white': '\033[37m',
            'blue': '\033[34m',
            'green': '\033[32m',
            'cyan': '\033[36m',
            'red': '\033[31m',
            'purple': '\033[35m',
            'yellow': '\033[33m',
            'default': '\033[0m'}

        if bold is False:
            self._c_tab = self._color_table_light
        else:
            self._c_tab = self._color_table_bold

    def set_color(self, val_str, col_str):
        """
        Set the target string to a certain color.
        1st param is the string, and the 2nd param is the color name
        """
        if col_str.lower() not in self._c_tab:
            log.warning('\033[01;33mWARNING\033[0m: %s is not supported color \
name. Supported color: %s' % (col_str, str(self._c_tab.keys())))
            return val_str
        if type(val_str) is not str:
            val_str = str(val_str)

        return self._c_tab[col_str] + val_str + self._c_tab['default']

    def list_color(self):
        """
        List all the color supported
        """
        print str(self._c_tab.keys())

    def set_bold(self, is_bold=True):
        if is_bold is False:
            self._c_tab = self._color_table_light
        else:
            self._c_tab = self._color_table_bold

    def green(self, val_str):
        """
        Set the given str color to green and return
        """
        return self.set_color(val_str, 'green')

    def red(self, val_str):
        """
        Set the given str color to red and return
        """
        return self.set_color(val_str, 'red')

    def yellow(self, val_str):
        """
        Set the given str color to yellow and return
        """
        return self.set_color(val_str, 'yellow')
