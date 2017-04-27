#!/usr/bin/python

# This module contains the tools related to the interface between
# matlab and python

import h5py
import glog as log
import numpy as np
import scipy.io as sio
import crash_on_ipy


def _filter_vars(data_dict):
    """
    Check the var names, and exclude the invalid vars, such as '__xxxx__'
    """
    # exclude the '__xxx__' vars
    for var_name in data_dict.keys():
        if var_name[:2] == '__' and var_name[-2:] == '__':
            data_dict.pop(var_name)

    return data_dict


def load_mat(mat_file, var_name=None, is_switch_HW=True, v73=True):
    """
    This function can load the mat file saved by matlab, and extract
    the matrix var from it.
    A numpy array will be returned.
    NOTE1:
        Since the height and width storage method is different between
        numpy and matlab, if is_switch_HW set to True, the H and W
        dimension will be switched.
    NOTE2:
        Since this function use h5py lib as interface. It ONLY support
        v7.3 format mat file
        HOWEVER, the HW switch only will be performs if the dim of mat
        between 2 to 4
    NOTE3:
        If error, return None
    NOTE4:
        If the mat is saved in other format instead of v7.3 hdf5 format
        Set the v73 to false
        When this is set, the is_switch_HW is ignored
    NOTE4:
        If the var_name is None, it will return the first value in the
        return dict
    NOTE5:
        If the var_name is set, but not match with the var_name inside
        If their are only one var in the mat, it will load the var and
        give a warning.
    """
    is_v73 = v73

    if v73 is True:
        try:
            matfile = h5py.File(mat_file, 'r')
        except IOError, e:
            # Try to use sio to open it
            try:
                matfile = sio.loadmat(mat_file)
                is_v73 = False
            except:
                log.error('Can not open mat file: %s\n' % e)
                return None

    else:
        try:
            matfile = sio.loadmat(mat_file)
        except IOError, e:
            # Try to use h5py to open it
            try:
                matfile = h5py.File(mat_file, 'r')
            except IOError, e:
                log.error('Can not open mat file: %s\n' % e)
                return None
            is_v73 = True

    try:
        if var_name is None:
            matfile = _filter_vars(matfile)
            data = matfile.values()[0]
            if len(matfile) > 1:
                log.warn('\033[33mWARNING\033[0m: The mat %s contains %d \
vars: \033[32m%s\033[0m, the var name should be asigned to make sure load \
the right var' % (mat_file, len(matfile), str(matfile.keys())))

        else:
            data = matfile[var_name]
    except KeyError, e:
        if len(matfile) == 1:
            log.warn('\033[01;33mWARNING\033[0m: The var contained in \
the mat is \033[32m%s\033[0m instead of the \033[33m%s\033[0m, \
load it instead' % (matfile.keys()[0], var_name))
            data = matfile.values()[0]
        else:
            log.error('Can not find key: %s\n' % e)
            log.info('The var name in the mat is: \033[32m%s\033[0m'
                     % str(matfile.keys()))
            return None

    data = np.array(data)
    # Switch the height and width
    if is_v73 and is_switch_HW:
        data = mat2nparray(data)

    return data


def load_mat_list(mat_file, is_switch_HW, *var_name_list):
    """
    Different from the load_mat, this function can extract multi
    vars from one mat file
    =================================================================
    This function can load the mat file saved by matlab, and extract
    the matrix var from it.
    A numpy array will be returned.
    NOTE1:
        Since the height and width storage method is different between
        numpy and matlab, if is_switch_HW set to True, the H and W
        dimension will be switched.
    NOTE2:
        Since this function use h5py lib as interface. It ONLY support
        v7.3 format mat file
        HOWEVER, the HW switch only will be performs if the dim of mat
        between 2 to 4
    NOTE3:
        If error, return None
    """
    try:
        matfile = h5py.File(mat_file, 'r')
    except IOError, e:
        log.error('Can not open mat file: %s\n' % e)
        return None

    rst_list = []
    for var_name in var_name_list:
        try:
            data = matfile[var_name]
        except KeyError, e:
            log.error('Can not find key: %s\n' % e)
            return None
        data = np.array(data)

        # Switch the height and width
        if is_switch_HW:
            data = mat2nparray(data)
        rst_list.append(data)

    return rst_list


def mat2nparray(data):
    """
    This function convert the mat to np.array.
    In other word, it will switch the height and width axis if the dim
    of mat between 2 and 4
    """
    ndim = data.ndim
    if ndim == 2:
        # Convert [width, height] to [height, width]
        data = data.transpose((1, 0))
    elif ndim == 3:
        # Convert [channel, width, height] to [height, width, channel]
        data = data.transpose((2, 1, 0))
    elif ndim == 4:
        # Convert [num, channel, width, height]
        # to [num, height, width, channel]
        data = data.transpose((0, 3, 2, 1))

    return data


def save_mat(mat_name, var_name, var):
    """
    This function write the np.array into a mat file.
    NOTE:
        This function use the tradation format to save
        the mat. So if using load_mat to load the mat file created by
        this function, the v73 param should be set to false
    """
    sio.savemat(mat_name, {var_name: var})
