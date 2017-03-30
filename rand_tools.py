#!/usr/bin/python

# This file contains the funcions about the random sample or
# something like that
import random


def sync_sample(num, a_list, b_list):
    """This funcions sync sample the a and b list, often used
    in randomly generate sub train set and sub label set
    """
    c = zip(a_list, b_list)
    random.shuffle(c)
    a_list, b_list = zip(*c)

    return a_list[:num], b_list[:num]


def rand_sample(src_list, num):
    """
    This funcion random sample num samples from src_list and
    return them as a list
    if num > len(src_list) the original list will be returned
    """
    if num >= len(src_list):
        return src_list
    random.shuffle(src_list)
    return src_list[:num]


def sample_list(src_list, prob):
    """
    Random sample the list according to the prob
    """
    num = int(prob*len(src_list))
    random.shuffle(src_list)
    return src_list[:num]
