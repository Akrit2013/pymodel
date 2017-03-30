#!/usr/bin/python

# This toolbox contains the Tools related to log
import glog as log


def log_info(log_str):
    """
    Similar with glog.info, but use color info in front
    """
    color_str = '\033[01;32mINFO\033[0m: '
    log.info(color_str + log_str)


def log_warn(log_str):
    """
    Similar with glog.warn, but use color info in front
    """
    color_str = '\033[01;33mWARNING\033[0m: '
    log.info(color_str + log_str)


def log_err(log_str):
    """
    Similar with glog.error, but use color info in front
    """
    color_str = '\033[01;31mERROR\033[0m: '
    log.info(color_str + log_str)
