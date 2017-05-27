# This lib contains the tools for fast serialize, which is useful to
# store the data into the lmdb database

import numpy as np
import zlib
import glog as log
import snappy
import color_lib


class serialize_numpy:
    """
    This class serialize and de-serialize the numpy array
    into string
    -----------------------------------------------------
    The format of the serialized string
    byte[0]:int8     The dtype of the numpy data, see the self._types
    byte[1]:int8     The dims of the array, e.g. for rgb image, byte[1] = 3
    byte[2:4]:int16  The first dim size
    byte[4:6]:int16  The second dim size
    byte[6:8]:int16  The third dim size
    ...
    """
    def __init__(self, compress=True, compressor='snappy'):
        """
        The compressor can be snappy or zlib
        """
        self._compress = compress
        self._types = ['uint8', 'int8', 'uint16', 'int16', 'uint32',
                       'int32', 'uint64', 'int64', 'float32', 'float64']
        self._color = color_lib.color(True)
        self._err = self._color.red('ERROR') + ': '
        if compressor == 'snappy':
            self._compressor = snappy.compress
            self._decompressor = snappy.decompress
        elif compressor == 'zlib':
            self._compressor = zlib.compress
            self._decompressor = zlib.decompress
        else:
            log.error(self._err + 'Can not recognize the compressor: %s'
                      % compressor)
            return

    def _parse_head(self, raw_data_str):
        """
        Parse the input string
        return dtype, shape, pure_data_str
        """
        btype = raw_data_str[0]
        dtype_idx = np.fromstring(btype, dtype='int8')[0]
        dtype = self._types[dtype_idx]
        bdims = raw_data_str[1]
        dims = np.fromstring(bdims, dtype='int8')[0]
        shape = []
        for idx in range(2, 2 * dims + 1, 2):
            bdim = raw_data_str[idx: idx + 2]
            dim = np.fromstring(bdim, dtype='int16')[0]
            shape.append(dim)
        # Calc the head length
        headlen = 2 + 2 * dims
        data_str = raw_data_str[headlen:]
        return dtype, shape, data_str

    def _add_head(self, data_str, dtype, shape):
        """
        Add head to the data_str to formulate the raw_data_str
        """
        # Find the type index
        try:
            dtype_idx = self._types.index(dtype)
        except:
            log.error(self._err + 'Unknown dtype ' + self._color.red(dtype))
            log.error('The current dtype: %s' % str(self._types))
            return

        head = np.int8(dtype_idx).tostring()
        dims = np.int8(len(shape))
        head += dims.tostring()
        for dim in shape:
            head += np.int16(dim).tostring()

        return head + data_str

    def dumps(self, array):
        """
        dump the array into the strings
        """
        if type(array) != np.ndarray:
            array = np.array(array)
        data_str = array.tostring()
        raw_data_str = self._add_head(data_str, array.dtype, array.shape)
        if self._compress:
            raw_data_str = self._compressor(raw_data_str)
        return raw_data_str

    def loads(self, raw_data_str):
        """
        de-serialize the string into the numpy array
        """
        if self._compress:
            raw_data_str = self._decompressor(raw_data_str)
        # Parse the string
        dtype, shape, data_str = self._parse_head(raw_data_str)
        array = np.fromstring(data_str, dtype=dtype)
        array = array.reshape(shape)
        return array
