#!/usr/bin/python

# This file contains the functions that related to reading and
# writting the txt file

import glog as log
import numpy as np
import sys
import yaml


def open_file(file_name, param_str):
    try:
        fp = open(file_name, param_str)
    except IOError:
        # May be the encoding of file name is not write
        try:
            fp = open(file_name.decode('utf8'), param_str)
        except:
            log.fatal('\033[01;31mERROR:\033[0m Can not open %s' % file_name)
            sys.exit(2)

    return fp


def write_list_as_line(fp, in_list):
    """
    This function convert the list by yaml to string, and write
    it into the file as a line
    """
    if type(in_list) is np.ndarray:
        in_list = in_list.tolist()
    elif type(in_list) is tuple:
        in_list = list(in_list)
    # Judge if the line is a string
    if type(in_list) is not str:
        in_list = yaml.dump(in_list)

    if in_list[-1] != '\n':
        in_list = in_list + '\n'
    fp.writelines(in_list)


def read_file_lines(fp):
    """This functiolines_listn read the file lines into a list of string
    Return: a list contains strings of the lines
    """
    lines_list = []
    for line in fp.readlines():
        # Check if the end of the line contains the \n
        if line[-1] == '\n':
            line = line[:-1]
        lines_list.append(line)

    return lines_list


def read_lines_from_txtfile(file_name):
    """Open a txt file and read lines into a string list
    """
    fp = open_file(file_name, 'r')
    lines_list = read_file_lines(fp)
    fp.close()
    return lines_list


def write_lines_to_txtfile(file_name, line_list):
    """Write the lines list into a txt file
    NOTE: If the line in the line_list is not a string, this function will
    convert it to string by using yaml lib before store it.
    """
    fp = open_file(file_name, 'w')
    for line in line_list:
        if type(line) is np.ndarray:
            line = line.tolist()
        elif type(line) is tuple:
            line = list(line)
        # Judge if the line is a string
        if type(line) is not str:
            line = yaml.dump(line)

        if line[-1] != '\n':
            line = line + '\n'
        fp.writelines(line)
    fp.close()


def string_list_to_float_list(str_list):
    """This function convert a list contains strings to a list
    contains float numbers
    """
    rst_list = []
    for ele in str_list:
        rst_list.append(float(ele))

    return rst_list
