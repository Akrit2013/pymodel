#!/usr/bin/python

# This module contains the functions related to the io for general type

import matlab_tools
import image_tools
import glog as log
import os


def imread(file_name):
    """
    This function try to load a image from general type of files.
    Support file type:
        [img file]: jpg, png, bmp ...
        [mat file]: the matlab file contains an image
    """
    # Define the file type
    DEF_IMG_TYPES = ['.jpg', '.bmp', '.png', '.ppm']
    DEF_MAT_TYPES = ['.mat']
    # Get the file type
    parts = os.path.splitext(file_name)
    ext = parts[-1].lower()

    if ext in DEF_IMG_TYPES:
        im = image_tools.imread(file_name)
        return im
    elif ext in DEF_MAT_TYPES:
        im = matlab_tools.load_mat(file_name)
        return im
    else:
        log.error('\033[01;31mERROR\033[0m: Can not open this type \
of image: %s' % file_name)
        return None
