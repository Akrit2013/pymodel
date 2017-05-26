# This lib contains the tools for fast serialize, which is useful to
# store the data into the lmdb database

import numpy as np
import zlib
import glog as log


class numpy:
    """
    This class serialize and de-serialize the numpy array
    into string
    """
    def __init__(self, compress=True):
        self._compress = compress

    def dumps(self, array):
        """
        dump the array into the strings
        """
        data_str = array.tostring()
        if self._compress:
            data_str = zlib.compress(data_str)
        return data_str

    def loads(self, data_str):
        """
        de-serialize the string into the numpy array
        """
        if self._compress:
            data_str = zlib.decompress(data_str)
        array = np.fromstring(data_str, dtype=np.int8)
        return array
