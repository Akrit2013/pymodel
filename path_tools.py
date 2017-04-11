#!/usr/bin/python

# This model contains the function related to path or file names

import os
import glog as log


def check_path(path, create_if_not=True):
    """Check if the path exist, if true, return True. If not exist:
    If create_if_not=True, create it and return False. or
    If create_if_not=False, return False
    """
    if os.path.exists(path):
        return True
    if create_if_not:
        try:
            os.makedirs(path)
        except:
            log.error('\033[0;31mFailed to create path %s\033[0m' % path)
            raise

    return False


def check_file_list(file_list):
    """
    This function check all files in the file list
    IF all of them exist, return true, else, return false
    """
    flag = True
    for files in file_list:
        if not os.path.exists(files):
            flag = False
            log.warn('\033[01;33mWARNING\033[0m: Can not find the \
file \033[0;33m%s\033[0m' % files)
    return flag


def get_pure_name(full_name):
    """This function get the pure name from a full file name.
    which is, the path name and the ext name will be ignored.
    For Example: if the input is /home/nile/something.jpg
    The return value is the 'something'
    """
    return os.path.splitext(os.path.split(full_name)[-1])[0]


def get_base_name(full_name):
    """
    This function get the file name apart from the path name
    e.g. input /aa/bb/cc.jpg, output: cc.jpg
    """
    return os.path.basename(full_name)


def get_path(full_name):
    """
    Opposite to the get_pure_name, this function only return
    the path.
    e.g. aa/bb/c will return aa/bb
    """
    words = os.path.split(full_name)
    return words[0]


def get_full_path(path_name, file_name):
    """
    Get the absolute path string from the given file name and
    reletive path
    """
    full_name = []
    if path_name[-1] == '/':
        full_name = path_name + file_name
    else:
        full_name = path_name + '/' + file_name
    return os.path.abspath(full_name)


def get_dir_list(path, is_abspath=True):
    """This function return the dir list from the given path
    If is_abspath is True, the absolute path will be returned
    else, only return the dir name
    """
    if os.path.exists(path) is False:
        log.error('\033[01;31mERROR:\033[0m The path %s dose not exist'
                  % path)
        return None
    dir_list = []
    # Get the file list from the path
    for file_name in os.listdir(path):
        full_name = get_full_path(path, file_name)
        # Judge if the file is a dir
        if os.path.isdir(full_name) is True:
            if is_abspath is True:
                dir_list.append(full_name)
            else:
                dir_list.append(file_name)

    return dir_list


def get_file_list(path, is_abspath=True, ext=None):
    """This function return the nodir file list from the given path
    If is_abspath is True, the absolute path will be returned
    else, only return the file name
    The ext indicate the extension name of the file, if set to None,
    all type of file will be returned, if set to jpg or txt. etc
    only certain type of file will be returned.
    """
    if os.path.exists(path) is False:
        log.error('\033[01;31mERROR:\033[0m The path %s dose not exist'
                  % path)
        return None
    file_list = []
    # Get the file list from the path
    for file_name in os.listdir(path):
        full_name = get_full_path(path, file_name)
        # Judge if the file is a dir
        if os.path.isdir(full_name) is True:
            continue
        # Check the extend name if needed
        if ext is not None:
            file_ext = os.path.splitext(file_name)
            if file_ext.lower() != ext.lower():
                continue

        if is_abspath is True:
            file_list.append(full_name)
        else:
            file_list.append(file_name)

    return file_list


def replace_ext(full_name, ext_name):
    """
    This function will change the target ext name with the ext_name
    and return the changed name
    NOTE: the path of the full_name will be kept
    """
    words = os.path.splitext(full_name)
    prefix = words[0]
    if ext_name[0] != '.':
        ext_name = '.' + ext_name
    return prefix + ext_name


def replace_datalist(datalist, path, warning=True):
    """
    This function take a datalist and path as input, it will check
    if the pure name of the datalist can be found in path, the
    path and the ext name will be replaced to formulate a new datalist
    representing the new data in the path
    """
    datalist_out = []
    # Formulate the datalist from the path
    datalist_path = get_file_list(path)
    datalist_dict = {}
    for data_entry in datalist_path:
        pure_name = get_pure_name(data_entry)
        datalist_dict[pure_name] = data_entry

    # Iter the datalist
    for data_entry in datalist:
        pure_name = get_pure_name(data_entry)
        if pure_name in datalist_dict:
            datalist_out.append(datalist_dict[pure_name])
        elif warning is True:
            log.warn('\033[33mWARNING\033[0m: Can not find the \033[31m%s\033[0m \
in the path %s' % (pure_name, path))

    return datalist_out


def replace_datalist_part(datalist, path, warning=True):
    """
    This function is modified from the replace_datalist
    The difference is: If only PART of the candidate file name matched
    the entries in the datalist, the match will be made.
    e.g. entry: 0120, file name img_0120.mat, they matched
    =============================================================
    This function take a datalist and path as input, it will check
    if the pure name of the datalist can be found in path, the
    path and the ext name will be replaced to formulate a new datalist
    representing the new data in the path
    """
    datalist_out = []
    # Formulate the datalist from the path
    datalist_path = get_file_list(path)
    datalist_dict = {}
    for data_entry in datalist_path:
        pure_name = get_pure_name(data_entry)
        datalist_dict[pure_name] = data_entry

    # Iter the datalist
    for data_entry in datalist:
        pure_name = get_pure_name(data_entry)
        # Iter the datalist_dict
        for key in datalist_dict:
            if pure_name in key:
                datalist_out.append(datalist_dict[key])
                datalist_dict.pop(key)
                break
        else:
            if warning is True:
                log.warn('\033[33mWARNING\033[0m: Can not find the \033[31m%s\033[0m \
in the path %s' % (pure_name, path))

    return datalist_out


def replace_path(org_full_name, target_path):
    """
    This function replace the original path to the new path, which is commonly
    used when copying the files
    """
    word_list = os.path.split(org_full_name)
    if target_path[-1] == '/':
        rst = target_path + word_list[-1]
    else:
        rst = target_path + '/' + word_list[-1]

    return rst
