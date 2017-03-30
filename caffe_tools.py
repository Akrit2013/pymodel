# This script contains the functions which are useful in caffe python
# interface

import caffe
from skimage.io import imread
import numpy as np
from scipy.misc import imresize
from sklearn.decomposition import PCA


# The following two class is extracted from the caffe example script
class SimpleTransformer:
    """
    SimpleTransformer is a simple class for preprocessing and deprocessing
    images for caffe.
    """

    def __init__(self, mean=[128, 128, 128]):
        self.mean = np.array(mean, dtype=np.float32)
        self.scale = 1.0

    def set_mean(self, mean):
        """
        Set the mean to subtract for centering the data.
        """
        self.mean = mean

    def set_scale(self, scale):
        """
        Set the data scaling.
        """
        self.scale = scale

    def preprocess(self, im):
        """
        preprocess() emulate the pre-processing occuring in the vgg16 caffe
        prototxt.
        """

        im = np.float32(im)
        im = im[:, :, ::-1]  # change to BGR
        im -= self.mean
        im *= self.scale
        im = im.transpose((2, 0, 1))

        return im

    def deprocess(self, im):
        """
        inverse of preprocess()
        """
        im = im.transpose(1, 2, 0)
        im /= self.scale
        im += self.mean
        im = im[:, :, ::-1]  # change to RGB

        return np.uint8(im)


class CaffeSolver:

    """
    Caffesolver is a class for creating a solver.prototxt file. It sets default
    values and can export a solver parameter file.
    Note that all parameters are stored as strings. Strings variables are
    stored as strings in strings.
    """

    def __init__(self, testnet_prototxt_path="testnet.prototxt",
                 trainnet_prototxt_path="trainnet.prototxt", debug=False):

        self.sp = {}

        # critical:
        self.sp['base_lr'] = '0.001'
        self.sp['momentum'] = '0.9'

        # speed:
        self.sp['test_iter'] = '100'
        self.sp['test_interval'] = '250'

        # looks:
        self.sp['display'] = '25'
        self.sp['snapshot'] = '2500'
        self.sp['snapshot_prefix'] = '"snapshot"'  # string withing a string!

        # learning rate policy
        self.sp['lr_policy'] = '"fixed"'

        # important, but rare:
        self.sp['gamma'] = '0.1'
        self.sp['weight_decay'] = '0.0005'
        self.sp['train_net'] = '"' + trainnet_prototxt_path + '"'
        self.sp['test_net'] = '"' + testnet_prototxt_path + '"'

        # pretty much never change these.
        self.sp['max_iter'] = '100000'
        self.sp['test_initialization'] = 'false'
        self.sp['average_loss'] = '25'  # this has to do with the display.
        self.sp['iter_size'] = '1'  # this is for accumulating gradients

        if (debug):
            self.sp['max_iter'] = '12'
            self.sp['test_iter'] = '1'
            self.sp['test_interval'] = '4'
            self.sp['display'] = '1'

    def add_from_file(self, filepath):
        """
        Reads a caffe solver prototxt file and updates the Caffesolver
        instance parameters.
        """
        with open(filepath, 'r') as f:
            for line in f:
                if line[0] == '#':
                    continue
                splitLine = line.split(':')
                self.sp[splitLine[0].strip()] = splitLine[1].strip()

    def write(self, filepath):
        """
        Export solver parameters to INPUT "filepath". Sorted alphabetically.
        """
        f = open(filepath, 'w')
        for key, value in sorted(self.sp.items()):
            if not(type(value) is str):
                raise TypeError('All solver parameters must be strings')
            f.write('%s: %s\n' % (key, value))


def load_image(image_name, color=True):
    img = imread(image_name, as_gray=not color)
    if img.ndim == 2:
        img = img[:, :, np.newaxis]
        if color:
            img = np.tile(img, (1, 1, 3))
    elif img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def load_image_to_datum(image_name, resize_height=None,
                        resize_width=None, normalize=False):
    """This function read function from disk, and store it into datum
    structure, which can be put into lmdb database.
    1. If normalize is False, the image is 0-255 int value, else, the
    image will be stored as 0-1 float value.
    2. This function will convert the image (ndarray) from RGB to BGR
    and store it int datum.
    3. If resize_width and resize_height is set, resize the image
    before put into datum
    """
    # Load the image
    if normalize is True:
        img = caffe.io.load_image(image_name)
    else:
        img = load_image(image_name)

    # Resize image if needed
    if resize_height is not None or resize_width is not None:
        curr_height = img.shape[0]
        curr_width = img.shape[1]
        new_size = [resize_height, resize_width]
        if new_size[0] is None:
            new_size[0] = curr_height
        if new_size[1] is None:
            new_size[1] = curr_width
    if normalize is True:
        img = caffe.io.resize_image(img, new_size)
    else:
        img = imresize(img, new_size)

    # Change RGB to BGR
    img = img[:, :, (2, 1, 0)]
    # Store the array to datum
    im_dat = caffe.io.array_to_datum(img.astype(float).transpose((2, 0, 1)))

    return im_dat


def load_array_to_datum(arr, dtype=None):
    """This function store the float array into the datum, and return
    the datum.
    This approach is commonly used in the regression model, when the
    label is a float (vector) instead of a single int value.
    """
    arr = np.array(arr)
    if dtype is None:
        if arr.dtype == np.uint8:
            dtype = np.uint8
        else:
            dtype = np.float64

    # The arr must have 3 dimension
    if arr.ndim == 0:
        arr = arr.astype(dtype).reshape(1, 1, 1)
    elif arr.ndim == 1:
        arr = arr.astype(dtype).reshape(arr.shape[0], 1, 1)
    elif arr.ndim == 2:
        arr = arr.astype(dtype).reshape(arr.shape[0], arr.shape[1], 1)
    elif arr.ndim == 3:
        arr = arr.astype(dtype)
    else:
        return None
    im_dat = caffe.io.array_to_datum(arr)

    return im_dat


def load_array_to_datum_str(arr, dtype=None):
    im_dat = load_array_to_datum(arr, dtype)
    return im_dat.SerializeToString()


def load_array_im_to_datum(arr, dtype=None, force_swith_channel=False):
    """This function store the float array image into the datum, and return
    the datum.
    Different from the load_array_to_datum, this function assume the data
    is a np.array image, which have a [RGB] order and [Height, width, channel]
    So, it will be changed into [BGR] and [Channel, Height, Width]
    Before change to datum
    Also Since this function is designed for np.array image, this use uint8
    as default data type, but it also can be set as other type

    NOTE:
        By default, only when the dtype == np.uint8 the RGB will be converted
        to BGR.
        And if the force_swith_channel set to True, it will change the change
        the channels by force
    """
    arr = np.array(arr)
    if dtype is None:
        if arr.dtype == np.uint8:
            dtype = np.uint8
        else:
            dtype = np.float64

    # The arr must have 3 dimension
    if arr.ndim == 0:
        arr = arr.astype(dtype).reshape(1, 1, 1)
    elif arr.ndim == 1:
        arr = arr.astype(dtype).reshape(arr.shape[0], 1, 1)
    elif arr.ndim == 2:
        arr = arr.astype(dtype).reshape(arr.shape[0], arr.shape[1], 1)
    elif arr.ndim == 3:
        arr = arr.astype(dtype)
        if arr.shape[2] == 3 and \
                (dtype == np.uint8 or force_swith_channel is True):
            # Change RGB to BGR
            arr = arr[:, :, (2, 1, 0)]
    else:
        return None
    im_dat = caffe.io.array_to_datum(arr.astype(dtype).transpose((2, 0, 1)))

    return im_dat


def load_array_im_to_datum_str(arr, dtype=None):
    im_dat = load_array_im_to_datum(arr, dtype)
    return im_dat.SerializeToString()


def load_image_ready_for_blob(image_name):
    """Load an image according to the name, and prepare the image
    for the caffe model's input blob.
    It will transfer the image shape to fit the input blob
    """
    # The transform object to preprocess the image
    transformer = SimpleTransformer()
    # Load the image
    im = load_image(image_name)
    # Transform the image (RGB to BGR, transpose the channel)
    return transformer.preprocess(im)


def parse_string_to_datum(datum_str):
    """
    Parse the given string into datum structure and return it
    If the string can not be parsed, return None
    """
    datum = caffe.proto.caffe_pb2.Datum()
    try:
        datum.ParseFromString(datum_str)
    except:
        return None
    return datum


def datum_to_array_im(datum, force_swith_channel=False):
    """
    This function convert the datum into a array image.
    NOTE: The BGR will be convert to RGB
    and the [channel, height, width] will be converted
    to [height, width, channel]

    NOTE:
        By default, only when the dtype == np.uint8 the RGB will be converted
        to BGR.
        And if the force_swith_channel set to True, it will change the change
        the channels by force
    """
    arr = caffe.io.datum_to_array(datum)
    arr = arr.transpose((1, 2, 0))
    if arr.shape[2] == 3:
        if force_swith_channel is True or arr.dtype == np.uint8:
            arr = arr[:, :, (2, 1, 0)]

    return arr


def datum_str_to_array_im(datum_str):
    """
    Directly convert the datum string into a original np.array image
    This function can be used to check the content of lmdb database
    """
    datum = parse_string_to_datum(datum_str)
    im = datum_to_array_im(datum)

    return im


def datum_str_to_array(datum_str):
    """
    Directly convert the datum string into a original np.array image
    This function can be used to check the content of lmdb database
    """
    datum = parse_string_to_datum(datum_str)
    arr = caffe.io.datum_to_array(datum)
    return arr


def _pca_feature_map(blob_data, pca_dim=3):
    """
    This function use PCA to turn the [1, c, h, w] feature map blob
    into [h, w, pca_dim] which can be displayed as RGB image.
    The input also can be [c, h, w]

    If the num is larger than 1, it only convert the first n, and
    ignore the rest.

    The pca_dim is the final channel number, default is 3 which indicate
    the RGB channel
    """
    if len(blob_data.shape) == 4:
        data = blob_data[0, :, :, :]
    data = data.transpose([1, 2, 0])
    # Generate the PCA model
    pca = PCA(n_components=pca_dim)
    org_shape = data.shape
    pca.fit(data.reshape(-1, data.shape[-1]))
    # Reduce the dim
    data = pca.transform(data.reshape(-1, org_shape[-1]))
    data = data.reshape(org_shape[0], org_shape[1], 3)

    return data


def pca_feature_map(blob_data, pca_dim=3):
    """
    This is a wrapper of the _pca_feature_map.
    This function can take the blob data with n larger than 1
    when the input is [n, c, h, w] where n > 1
    The output will be [n, h, w, pca_dim]
    When the input is [1, c, h, w] or [c, h, w]
    The output will be [h, w, pca_dim]
    """
    if len(blob_data.shape) == 4 and blob_data.shape[0] > 1:
        rst = np.zeros([blob_data.shape[0],
                        blob_data.shape[2],
                        blob_data.shape[3],
                        pca_dim])
        for idx in range(blob_data.shape[0]):
            data = _pca_feature_map(blob_data[idx, :, :, :],
                                    pca_dim=pca_dim)
            rst[idx, :, :, :] = data
        return rst

    return _pca_feature_map(blob_data, pca_dim=pca_dim)
