#!/usr/bin/python

# This module contains the functions do the bit operations

import glog as log
from bitarray import bitarray


def set_bit(target, idx, val, byte=1):
    """
    Set the target number's idx bit to val (0 or 1)
    The byte indicate the number of byte the target containd
    Note:
        The idx start with 0
    """
    if int(val) != 0 and int(val) != 1:
        log.error('ERROR: The set value must be 0 or 1')
        return target

    mask = bitarray(8*byte)
    if val == 0:
        mask.setall(1)
        mask[-(idx+1)] = 0
    else:
        mask.setall(0)
        mask[-(idx+1)] = 1

    mask_val = int(mask.to01(), 2)
    if val == 0:
        return target & mask_val
    else:
        return target | mask_val


def get_bit(target, idx):
    """
    Return the bit of the certain positon
    Note:
        The idx start with 0
    """
    mask = 1 << idx
    return bool(target & mask)
