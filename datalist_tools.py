#!/usr/bin/python

# This models contains the tools functions about datalist

import txt_tools
import path_tools


def get_imageid_list_from_datalist(datalist):
    """This function will get the image id from the datalist and return it
    in a list
    """
    datalist_list = txt_tools.read_lines_from_txtfile(datalist)
    id_list = []
    for line in datalist_list:
        word_list = line.split()
        img_id = path_tools.get_pure_name(word_list[0])
        id_list.append(img_id)

    return id_list


def get_imagepath_list_from_datalist(datalist):
    """This function will get the image path from the datalist and return it
    in a list
    """
    datalist_list = txt_tools.read_lines_from_txtfile(datalist)
    id_list = []
    for line in datalist_list:
        word_list = line.split()
        id_list.append(word_list[0])

    return id_list


def get_image_dict_from_datalist(datalist):
    """This function read the datalist and return it as a dict
    the key of the dict is the image id
    and the value of the dict is a float or a float list
    """
    datalist_list = txt_tools.read_lines_from_txtfile(datalist)
    data_dict = {}
    for line in datalist_list:
        word_list = line.split()
        img_id = path_tools.get_pure_name(word_list[0])
        if len(word_list) == 1:
            data_dict[img_id] = None
        elif len(word_list) == 2:
            data_dict[img_id] = float(word_list[1])
        else:
            data_dict[img_id] = \
                txt_tools.string_list_to_float_list(word_list[1:])

    return data_dict
