#!python

# This module contains the class that automatically show
# the images
import random
import matplotlib
# Change the backend to make sure compatiable with Ipython
# This must be put before import the pyplot
# matplotlib.use('QT5Agg')
from PIL import Image
import matplotlib.pyplot as plt
import glog as log
import numpy as np


class Imshow:
    def __init__(self, im=None, ion=True):
        self._im_obj_list = []
        self._fig = None
        self._ax_list = []
        self._im_list = []
        # Judge if the im is a np.array or an image name
        if type(im) is str:
            self._im_list.append(np.array(Image.open(im)))
        elif im is not None:
            self._im_list.append(np.array(im))
        if ion:
            plt.ion()
        self.cmap = None
        self.vmin = None
        self.vmax = None
        # Indicate the class will auto adjust the image to make
        # it correctly displayed. It can be disabled by set to false
        self._adjust_im = True
        # Define the max number of columns to display the image
        self.disp_cols = 4

    def __del__(self):
        self.close()
        plt.ioff()

    def set_adjust(self, flag):
        """
        Set if try to adjust the image to make it can be correctly displayed
        """
        if type(flag) != bool:
            log.error('The parameter of set_adjust must be a bool')
            return
        self._adjust_im = flag

    def show(self):
        """
        Display the image at once
        """
        if len(self._im_list) == 0:
            # incase need to show the figure before put the image into
            if self._fig is None:
                self._fig = plt.figure()
            plt.pause(0.1)
            return
        if self._fig is None or len(self._im_list) != len(self._im_obj_list) or \
                self._ax_list == []:
            self.reset()
            if self._fig is None:
                self._fig = plt.figure()
            for idx in range(len(self._im_list)):
                st_im = self._im_list[idx]
                im = st_im[0]
                cmap = st_im[1]
                vmin = st_im[2]
                vmax = st_im[3]
                ax = self._fig.add_subplot(*self._calc_disp_pos(idx))
                self._ax_list.append(ax)
                im_obj = self._ax_list[-1].imshow(im,
                                                  interpolation='none',
                                                  cmap=cmap,
                                                  vmin=vmin,
                                                  vmax=vmax)
                self._im_obj_list.append(im_obj)
        else:
            for idx in range(len(self._im_list)):
                self._im_obj_list[idx].set_cmap(self._im_list[idx][1])
                self._im_obj_list[idx].set_data(self._im_list[idx][0])
        plt.pause(0.1)

    def imshow(self, *argv):
        """
        If only one param:
            show the image on the first place
        two params:
            Taken as image, idx (if can be converted to int)
        More than two:
            Show multi images together
        """
        # First check if the figure is valid
        if plt.get_fignums() == []:
            # Clear all data and redraw the figure
            self.clear()

        if len(argv) == 0:
            return
        elif len(argv) == 1:
            self._imshow(argv[0])
        elif len(argv) == 2 and type(argv[1]) is int:
            self._imshow(argv[0], argv[1])
        else:
            for idx in range(len(argv)):
                self.set_data(argv[idx], idx)
            self.show()

    def autoshow(self, *argv):
        """
        This is a wrapper for the imshow
        The difference is, this function will pre-process the images
        1. squeeze the channels to eliminate the 1 channel
           After this step, the image should have at most three channels
        2. If any of the channels is 3, transpose it to the last channel.
        3. If the image have 3 channels, and none of them equals to 3
           split the image according to the last channel
        Then display the new image array by imshow
        """
        if len(argv) == 0:
            return
        # Iter the args
        im_list = []
        for idx in range(len(argv)):
            im_list += self._preprocess(argv[idx])

        self.imshow(*im_list)

    def set_gray(self):
        self.cmap = plt.get_cmap('gray')

    def set_data(self, im, idx=0):
        if type(im) is str:
            im = Image.open(im)
        st_im = self._prepare_image(im)
        self._set_data(self._im_list, st_im, idx)

    def add_data(self, *im_list):
        """
        The im can be a image or a image list
        or the image names
        """
        for im in im_list:
            self._add_data(im)

    def reset(self):
        self._im_obj_list = []
        self._ax_list = []
        # Clear all the axis
        if self._fig is not None:
            self._fig.clear()
            # If the figure is invailed, set it to none
            if not plt.fignum_exists(self._fig.number):
                self._fig = None

    def clear(self):
        self._im_list = []
        self.reset()

    def close(self):
        """
        Close the figure window
        """
        if self._fig is not None:
            plt.close(self._fig)

    def _set_data(self, data_list, data, idx):
        while len(data_list) <= idx:
            data_list.append(None)
        data_list[idx] = data

    def _imshow(self, im, idx=0):
        if type(im) is str:
            im = Image.open(im)
        self.set_data(im, idx)
        self.show()

    def _add_data(self, im):
        if type(im) is str:
            im = Image.open(im)
        st_im = self._prepare_image(im)
        self._im_list.append(np.array(st_im))

    def _prepare_image(self, im):
        """
        Prepare the image and its corresponding display params.
        The return format is:
            [img, cmap, vmin, vmax]
        Note:
            The global setting of cmap, vmin, vmax, etc can overwrite
            the setting determained in this function
        """
        im = np.array(im)
        if self._adjust_im is False:
            return [im, self.cmap, self.vmin, self.vmax]
        else:
            # Check if the image is a gray image
            cmap = None
            vmax = None
            vmin = None

            if im.ndim == 2:
                cmap = plt.get_cmap('gray')
            elif im.ndim == 3 and im.shape[2] == 1:
                im = im.reshape((im.shape[0], im.shape[1]))
                cmap = plt.get_cmap('gray')
            elif im.ndim >= 4:
                log.error('\033[01;31mERROR\033[0m: Can not display the \
image, shape %s' % str(im.shape))
                return None
            # If the im is not uint8 image, normalize it to 0~1
            if im.dtype != np.uint8:
                if im.dtype == np.int16 or im.dtype == np.int32:
                    vmax = im.max()
                    vmin = im.min()
                else:
                    im = self._normalize(im)

            if self.cmap is not None:
                cmap = self.cmap
            if self.vmax is not None:
                vmax = self.vmax
            if self.vmin is not None:
                vmin = self.vmin
            return [im, cmap, vmin, vmax]

    def _normalize(self, im, vmin=0, vmax=1, dtype=np.float64):
        """
        Normalize the float image to 0 to 1
        """
        im = np.array(im)
        im_float = im.astype(np.float32)
        val_max = im_float.max()
        val_min = im_float.min()

        rate = (float(vmax)-float(vmin)) / (val_max-val_min)
        im_float = im_float - val_min
        im_float = im_float * rate
        return im_float.astype(dtype)

    def _calc_disp_pos(self, idx):
        """
        Calc the display position according to the index and
        the self.disp_cols
        """
        length = len(self._im_list)
        row = int(length-1) / int(self.disp_cols) + 1
        if length > self.disp_cols:
            col = self.disp_cols
        else:
            col = length
        return [row, col, idx+1]

    def _preprocess(self, im):
        """
        The pre-process funcion for autoshow
        The return is a list of images
        """
        # Squeeze the data
        im = np.squeeze(im)
        if len(im.shape) == 2:
            return [im]
        elif len(im.shape) != 3:
            log('\033[01:31mERROR\033[0m: The given image can not be \
parsed. The shape is %s' % str(im.shape))
            return []

        if im.shape[0] == 3:
            im = im.transpose([1, 2, 0])
            return [im]
        elif im.shape[1] == 3:
            im = im.transpose([0, 2, 1])
            return [im]
        elif im.shape[2] == 3:
            return [im]
        else:
            # split the last channel
            return np.split(im, im.shape[2], axis=2)


class plot:
    """
    This class can plot lines continuesly
    """
    def __init__(self, *args):
        self._fig = None
        self._ax = None
        self._obj = None
        self._color = [random.random(), random.random(), random.random()]
        plt.ion()

        if len(args) != 0:
            self._plot(args)

    def __del__(self):
        self.reset()
        plt.ioff()

    def _plot(self, args_list):
        if self._fig is None:
            self._fig = plt.figure()
            self._ax = self._fig.add_subplot(1, 1, 1)
            self._obj, = self._ax.plot(*args_list)
        else:
            self._obj.set_data(*args_list)
            self._rescale_ax()
        plt.pause(0.1)

    def reset(self):
        plt.close()
        self._fig = None
        self._ax = None
        self._obj = None

    def plot(self, *args):
        # First check if the figure is valid
        if plt.get_fignums() == []:
            # Clear all data and redraw the figure
            self.reset()
        self._plot(args)

    def _rescale_ax(self):
        if self._ax is not None:
            self._ax.relim()
            self._ax.autoscale_view()
            plt.draw()
