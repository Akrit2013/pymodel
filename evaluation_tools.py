#!/usr/bin/python

# This toolbox contains the tools to evaluate the prediction and
# the ground truth

# Different from the error_tools provided in the PROJ1603
# This error_tools has less limitation, which means it can be used
# evaluate more type of data other than depth and surface normal
# prediction


import numpy as np
# import math
import glog as log


def _reshape(label, pred):
    """
    Check if the shape of the pred is not equal with the label, reshape
    it to the label's shape
    """
    # if np.sum(np.isinf(label)) > 0 or np.sum(np.isinf(pred)) > 0:
    #     pdb.set_trace()
    # if np.sum(np.isnan(label)) > 0 or np.sum(np.isnan(pred)) > 0:
    #     pdb.set_trace()

    # Check if the label and pred can be reshaped
    if np.size(pred) != np.size(label):
        log.error('\033[01;31mERROR\033[0m: The size of pred and label are \
not matched. \033[0;33m%d\033[0m vs \033[0;33m%d\033[0m'
                  % (np.size(pred), np.size(label)))

    if label.shape == pred.shape:
        return pred

    if label.shape[0] != pred.shape[0] or \
            np.product(label.shape) != np.product(pred.shape):
        log.info('\033[01[31mERROR\033[0m: The shape of label and pred \
not match %s vs %s' % (str(label.shape), str(pred.shape)))
        return pred

    return pred.reshape(label.shape)


def MARE(label, pred, max_lab=float('inf'), min_lab=float('-inf')):
    """
    Calculate the Mean Absolute relative error
    max_lab:        The max legal label value
    min_lab:        The min legal label value
    """
    if max_lab < min_lab:
        log.error('\033[01;31mERROR\033[0m: The max label must \
be larger than min label')
        return
    label = np.array(label).astype('float')
    pred = np.array(pred).astype('float')
    # Reshape the pred to the label shape
    pred = _reshape(label, pred)
    # Clear all invalid pixel
    # The label may contains ZERO, set them to 1
    mask_min = label < min_lab
    mask_max = label > max_lab

    mask = mask_max | mask_min

    invalid_num = mask.sum()
    valid_num = np.size(label) - invalid_num

    label[mask] = 1

    diff = np.abs(pred-label)
    diff[mask] = 0
    val = np.sum(diff / label)
    rst = val / valid_num
    return rst


def RMSE(label, pred, max_lab=float('inf'), min_lab=float('-inf')):
    """
    The Root Mean Squared Error
    """
    label = np.array(label)
    pred = np.array(pred)
    # Reshape the pred to the label shape
    pred = _reshape(label, pred)

    mask_min = label < min_lab
    mask_max = label > max_lab

    mask = mask_max | mask_min

    invalid_num = mask.sum()
    valid_num = np.size(label) - invalid_num

    label[mask] = 1
    pred[mask] = 1

    diff = pred - label
    diff[mask] = 0
    return np.sqrt(np.sum(diff**2) / valid_num)


def RMS_log(label, pred, max_lab=float('inf'), min_lab=float('-inf')):
    """
    The Root Mean Squared Log-Error
    """
    label = np.array(label)
    pred = np.array(pred)
    # Reshape the pred to the label shape
    pred = _reshape(label, pred)

    mask_min = label < min_lab
    mask_max = label > max_lab

    mask = mask_max | mask_min

    invalid_num = mask.sum()
    valid_num = np.size(label) - invalid_num

    # Clear all invalid pixel
    # The label may contains ZERO, set them to 1
    label[mask] = 1
    pred[mask] = 1

    rst = np.sqrt(np.sum((np.log10(pred) - np.log10(label))**2) / valid_num)
    return rst


def M_log(label, pred, max_lab=float('inf'), min_lab=float('-inf')):
    """
    Mean log Error
    """
    label = np.array(label)
    pred = np.array(pred)
    # Reshape the pred to the label shape
    pred = _reshape(label, pred)

    mask_min = label < min_lab
    mask_max = label > max_lab

    mask = mask_max | mask_min

    invalid_num = mask.sum()
    valid_num = np.size(label) - invalid_num

    label[mask] = 1
    pred[mask] = 1

    return np.sum(np.abs(np.log10(label) - np.log10(pred))) / valid_num


def Threshold(label, pred, param=1.0, max_lab=float('inf'),
              min_lab=float('-inf')):
    """
    The threshold method
    """
    label = np.array(label)
    pred = np.array(pred)
    # Reshape the pred to the label shape
    pred = _reshape(label, pred)

    mask_min = label < min_lab
    mask_max = label > max_lab

    mask = mask_max | mask_min

    invalid_num = mask.sum()
    valid_num = np.size(label) - invalid_num

    label[mask] = 1
    pred[mask] = 1

    thd = 1.25**param

    div1 = pred / label
    div2 = label / pred

    mm = np.maximum(div1, div2)
    mm[mask] = float('inf')
    return np.sum(mm <= thd) / float(valid_num)
