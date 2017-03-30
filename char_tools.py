#!/usr/bin/python

# This tools contains the function related to the encoding of the chars

import chardet
import crash_on_ipy
import pdb
import log_tools


def str2unicode(string):
    """
    Detect the coding of the given string, and transform it into unicode
    """
    # Detect the coding type
    rst_dict = chardet.detect(string)
    coding = rst_dict['encoding']
    if coding is None:
        return None
    if coding == 'ascii':
        return string

    try:
        cod_str = string.decode(coding)
    except:
        if coding == 'Big5' or coding == 'GB2312':
            try:
                cod_str = string.decode('utf8')
            except:
                return string
        else:
#            log_tools.log_err('%s unknow type %s' % (string, coding))
#            pdb.set_trace()
            cod_str = string
    return cod_str
