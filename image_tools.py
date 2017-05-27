#!/usr/bin/python

# This module contains the basic functions relatived to image
# processing

import numpy as np
import scipy.misc as scm
from scipy.ndimage.interpolation import zoom
import matplotlib.pyplot as plt
import glog as log
from PIL import Image


def imread(im_file):
    """
    Read the target image and return the np.array
    """
    im = Image.open(im_file)
    return np.array(im)


def imresize(im, h_size_or_rate, w_size=None, nearest=False):
    """
    This funciton is a wrapper of many kinds of image resize functions
    It can resize the image with different channels [1 or 3]
    also can resize the image with different Dtype
    =============================
    Param:
        h_size_or_rate: the new height or the resized rate
        w_size: the new width
        nearest: If True, the resize will use the nearest method instead
        of the interpolation to zoom the image.
    =============================
    If the ndim or channels is NOT supported, return None
    """
    im = np.array(im)
    ndim = im.ndim
    org_h = im.shape[0]
    org_w = im.shape[1]
    # Calc the resize rate and resized shape
    if w_size is None:
        # The h_size_or_rate indicate the resize rate
        rz_h_rate = h_size_or_rate
        rz_w_rate = h_size_or_rate
        rz_h = int(rz_h_rate*org_h)
        rz_w = int(rz_w_rate*org_w)
    else:
        # The h_size_or_rate indicate the height
        rz_h = int(h_size_or_rate)
        rz_w = int(w_size)
        rz_h_rate = float(rz_h) / org_h
        rz_w_rate = float(rz_w) / org_w

    if im.dtype == np.uint8 and (ndim == 2 or ndim == 3):
        if nearest is True:
            im = scm.imresize(im, [rz_h, rz_w], 'nearest')
        else:
            im = scm.imresize(im, [rz_h, rz_w])
        return im

    if ndim == 1:
        return None
    elif ndim == 2:
        # Consider a gray image
        # Must use zoom instead of imresize
        if nearest is True:
            im = zoom(im, (rz_h_rate, rz_w_rate), order=0)
        else:
            im = zoom(im, (rz_h_rate, rz_w_rate))
        return im
    elif ndim == 3:
        if nearest is True:
            im = zoom(im, (rz_h_rate, rz_w_rate, 1), order=0)
        else:
            im = zoom(im, (rz_h_rate, rz_w_rate, 1))
        return im

    return None


def imshow(im):
    """
    This function is auto version of the plt.imshow.
    It will auto choose the imshow mode and max min
    val
    NOTE: THe im can be a file name, in this case, the function will
    read the image first and then disply
    """
    plt.ion()
    # If the im is a file name
    if type(im) == str:
        im = Image.open(im)
    im = np.array(im)
    cmap = None
    if im.ndim == 2:
        cmap = plt.get_cmap('gray')
    elif im.ndim == 3 and im.shape[2] == 1:
        im = im.reshape((im.shape[0], im.shape[1]))
        cmap = plt.get_cmap('gray')
    elif im.ndim >= 4:
        log.error('Can not display the image, shape %s' % str(im.shape))
        return None
    # If the im is not uint8 image, normalize it to 0~1
    if im.dtype != np.uint8:
        im = imnormalize(im)
    # disp the image
    plt.imshow(im, interpolation='none', cmap=cmap)
    plt.show()
    plt.pause(0.1)
    plt.ioff()


def remove_nan(im):
    """
    This funciton will check if the image contains NaN (can be
    normally found in depth images.
    And it will put 0 to the NaN position

    It will return the checked image
    """
    if np.isnan(im).sum() != 0:
        im = np.nan_to_num(im)

    return im


def check_inf(im):
    """
    Check if there is inf in the np.array
    """
    if np.isinf(im).sum() != 0:
        return True
    return False


def imnormalize(im, vmin=0, vmax=1, dtype=np.float32):
    """
    Normalize the image to a certain range.
    default is normalize the image to 0 and 1, the min value is 0
    and the max pixel value is 1.
    """
    im = np.array(im)
    im_float = im.astype(np.float32)
    val_max = im_float.max()
    val_min = im_float.min()

    rate = (float(vmax)-float(vmin)) / (val_max-val_min)
    im_float = im_float - val_min
    im_float = im_float * rate
    return im_float.astype(dtype)


def rgb2gray(rgb):
    rgb = np.array(rgb)
    dtype = rgb.dtype
    return np.dot(rgb[..., :3], [0.299, 0.587, 0.114]).astype(dtype)


def imwrite(im_name, im_array):
    """
    Write the image into file
    """
    im = Image.fromarray(im_array)
    im.save(im_name)


def repair_im(im, val=0):
    """
    Replace the NaN,inf and -inf in the image to the target
    value
    """
    im = np.array(im)
    mask = np.isnan(im)
    im[mask] = val
    mask = np.isinf(im)
    im[mask] = val
    mask = np.isneginf(im)
    im[mask] = val
    return im


def preprocess(im):
    """
    This function preprocess the image data, in order to make it
    fit the imshow
    """
    # Squeeze the data
    im = np.squeeze(im)
    if len(im.shape) == 2:
        return im
    elif len(im.shape) != 3:
        log('\033[01:31mERROR\033[0m: The given image can not be \
parsed. The shape is %s' % str(im.shape))
        return []

    if im.shape[0] == 3:
        im = im.transpose([1, 2, 0])
        return im
    elif im.shape[1] == 3:
        im = im.transpose([0, 2, 1])
        return im
    elif im.shape[2] == 3:
        return im
    else:
        # split the last channel
        return np.split(im, im.shape[2], axis=2)


def replace_color(im, in_color, out_color):
    """
    Replace the certain color in RGB image
    im:     The RGB image with the shape [h, w, 3]
    in_color:   The target color [r, g, b]
    out_color:  The out color [r, g, b]
    """
    # Check the input dimention
    plan = im.shape[2]
    if plan != 3:
        log.error('\033[01;31mERROR\033[0m: The input must be RGB image')

    if len(in_color) != plan or len(out_color) != plan:
        log.error('\033[01;31mERROR\033[0m: The shape of the image \
not match with the input')

    b0 = im[:, :, 0] == in_color[0]
    b1 = im[:, :, 1] == in_color[1]
    b2 = im[:, :, 2] == in_color[2]

    b = b0 & b1 & b2
    im[b, :] = out_color

    return im


def imcrop(im, crop_rate):
    """
    Perform central crop according to the crop_rate
    """
    d0_size = int(float(im.shape[0]) * crop_rate)
    d1_size = int(float(im.shape[1]) * crop_rate)
    d0_beg = (im.shape[0]-d0_size) / 2
    d1_beg = (im.shape[1]-d1_size) / 2
    im_crop = im[d0_beg:d0_beg+d0_size, d1_beg:d1_beg+d1_size, :]

    return im_crop


def transpose(im):
    """
    Transpose the image and return
    """
    if len(im.shape) == 2:
        im = im.transpose()
    elif len(im.shape) == 3:
        im = im.transpose([1, 0, 2])
    else:
        log.error('Can not transpose the image with \
shape %s' % str(im.shape))

    return im
