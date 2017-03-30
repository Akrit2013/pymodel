# This model contains the tools for list operation

import glog as log


def clip_list(in_list, start_ele, end_ele, echo=True):
    """
    This function clip the list from the start ele to end ele
    the order of the new list will be from the start_ele to
    end_ele
    If the start_ele or the end_ele can not be found, return None
    """
    try:
        start_idx = in_list.index(start_ele)
    except:
        if (echo):
            log.error('\033[01;31mERROR\033[0m: Can not find \033[01;31m%s\033[0m \
in list %s' % (start_ele, str(in_list)))
        return None
    try:
        end_idx = in_list.index(end_ele)
    except:
        if (echo):
            log.error('\033[01;31mERROR\033[0m: Can not find \033[01;31m%s\033[0m \
in list %s' % (end_ele, str(in_list)))
        return None

    if end_idx >= start_idx:
        step = 1
    else:
        step = -1

    end_idx = end_idx + step

    return in_list[start_idx: end_idx: step]
