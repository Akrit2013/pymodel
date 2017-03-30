#!/usr/bin/python

# This lib provide a class which can segment the image using ncut method
# in multi thread method

import numpy as np
import time
import threading
import glog as log
import Queue
from skimage import segmentation, filters, color
from skimage.future import graph
import pymeanshift as pms


class seg:
    """
    This class segment the image using Normalized cut approach.

    put(data, block=True):
        For N-Cut: data is [image, label_or_num]
            The image is a rgb or gray image
            The label_or_num can be a pre-segmented super pixel label map
            of a number which the image need to be segmented into super pixels
        For Mean shift: data is [image, [param list]]
        For SLIC: data is [image, [param list]]
        For quickshift: [image, [kernel_size, ...]]

    get():
        return the label image, if the out queue is empty, block
        NOTE: The out order is the same as the in order

    empty():
        Check if the out queue is empty

    full():
        Check if the in queue is full

    start():
        start the threads

    readytojoin():
        If the object is ready to join

    join():
        Block the thread and wait for threads to join
    """

    def __init__(self, in_queue_size=200, out_queue_size=200, thread_num=10):
        # The input is np.array
        self.inqueue = Queue.Queue(maxsize=in_queue_size)
        # The output is str
        self.outqueue = Queue.Queue(maxsize=out_queue_size)
        # The number of the thread
        self.thread_num = thread_num
        # The thread pool
        self.thread_pool = []
        # Signal if the threads should exit
        self._thread_state = True
        # The wait time to copy data from in queue to in buffer
        self.block_time = 5
        self.mutex = threading.Lock()
        # Set the segment algorithm
        self.func_seg_image = self._mean_shift
        # Indicate whether the IO is balance
        self.io_balance = 0
        # The supported segment algorithms
        self.alg_list = ['n-cut', 'm-shift', 'slic', 'q-shift', 'n-cut-b']
        # The corresponding functions
        self.alg_func_list = [self._ncut_seg,
                              self._mean_shift,
                              self._slic,
                              self._quick_shift,
                              self._ncutb_seg]

    def start(self):
        """
        Start the threads, which keep monitor the inqueue and try to convert
        array to datum and to string
        """
        # Check
        if self.func_seg_image is self._ncut_seg and self.thread_num != 1:
            log.warn('\033[0;33mWARNING\033[0m: In Ncut mode, the multithread \
might cause problem.')
        # Start the worker thread
        for i in range(self.thread_num):
            hThread = threading.Thread(
                target=self._thread
            )
            hThread.start()
            self.thread_pool.append(hThread)

    def set_method(self, method):
        """
        Currently, it support
        1. normalized cut, 'n-cut'
        2. mean shift, 'm-shift'
        """
        for name, func in zip(self.alg_list, self.alg_func_list):
            if method.lower() == name.lower():
                self.func_seg_image = func
                return
        else:
            log.error('\033[31mERROR:\033[0m Currently, only support %s'
                      % str(self.alg_list))

    def put(self, data_id, data, block=True):
        """
        Here the thread might be blocked
        """
        self.inqueue.put([data_id, data], block)
        self.io_balance += 1

    def get_inqueue_size(self):
        return self.inqueue.qsize()

    def get_outqueue_size(self):
        return self.outqueue.qsize()

    def empty(self):
        return self.outqueue.empty()

    def full(self):
        return self.inqueue.full()

    def readytojoin(self):
        return self.inqueue.empty() and\
            self.outqueue.empty() and\
            self.io_balance == 0

    def join(self):
        """
        Signal the threads exit, and wait for them
        """
        self._thread_state = False
        for hThread in self.thread_pool:
            hThread.join()
        self.thread_pool = []

    def get(self, block=True):
        """
        Get the string which converted from datum
        If non block, it might raise exception when the queue is empty]
        If can not get anything, return None
        """
        try:
            val = self.outqueue.get(block)
            self.io_balance -= 1
        except:
            return None
        return val[0], val[1]

    def _ncut_seg(self, data_list):
        """
        Use the ncut method to segment the image
        [image, slic_label/[slic_param], [ncut_param]]
        """
        img = data_list[0]
        param = data_list[1]
        param_cut = data_list[2]
        if param_cut is None:
            threahold = 0.001
        else:
            threahold = param_cut[0]
        # Check if the param is the super pixel label or the num of super pixel
        # to be segmented
        try:
            num = int(param[0])
            # super pixel seg
            label1 = segmentation.slic(img, compactness=10, n_segments=num,
                                       slic_zero=True)
        except:
            label1 = param
        # N-Cut
        g = graph.rag_mean_color(img, label1, mode='similarity')
        try:
            label2 = graph.cut_normalized(label1, g, thresh=threahold)
        except:
            log.error('\033[01;31mERROR\033[0m: Unknow Error in cut_normalized \
function.')
            label2 = np.zeros(label1.shape).astype('int')
        return label2

    def _ncutb_seg(self, data_list):
        """
        This function use bounday instead of color to formulate the RAG
        Use the ncut method to segment the image
        [image, slic_label/[slic_param], [ncut_param]]
        """
        img = data_list[0]
        param = data_list[1]
        param_cut = data_list[2]
        if param_cut is None:
            threahold = 0.2
        else:
            threahold = param_cut[0]
        # Check if the param is the super pixel label or the num of super pixel
        # to be segmented
        try:
            num = int(param[0])
            # super pixel seg
            label1 = segmentation.slic(img, compactness=10, n_segments=num,
                                       max_iter=100, slic_zero=True)
        except:
            label1 = param
        # N-Cut
        # Edge detection
        edge = filters.sobel(color.rgb2gray(img))
        # Smooth the edge map
        edge = filters.gaussian(edge, 1)
        edge = filters.gaussian(edge, 1)
        # Reverse the energy map
        ne = edge.max() - edge
        rag = graph.rag_boundary(label1, ne)
        label2 = graph.cut_normalized(label1, rag, thresh=threahold)
        return label2

    def _mean_shift(self, data_list):
        """
        The first parameter is the image
        the second parameter is [spatial_radius, range_radius, min_density]
        If None, the default val will be 6, 4.5, and 50
        """
        im = data_list[0]
        params = data_list[1]
        if params is None:
            sr = 6
            rr = 4.5
            md = 50
        else:
            sr = params[0]
            rr = params[1]
            md = params[2]
        (segmented_image, labels_image, number_regions) = \
            pms.segment(im, spatial_radius=sr, range_radius=rr, min_density=md)
        return labels_image

    def _slic(self, data_list):
        """
        The first param image
        Second param is [n_segments, compactness, max_iter, slic_zero]
        """
        im = data_list[0]
        params = data_list[1]
        n_seg = params[0]
        comp = params[1]
        max_iter = params[2]
        slic0 = params[3]
        enforce_conn = params[4]
        label = segmentation.slic(im, n_segments=n_seg, compactness=comp,
                                  enforce_connectivity=enforce_conn,
                                  max_iter=max_iter, slic_zero=slic0)
        return label

    def _quick_shift(self, data_list):
        """
        The first param is image
        Second param [kernel_size, ...]
        NOTE: If the kernel_size > 10, the speed will be very slow
        """
        im = data_list[0]
        params = data_list[1]
        if params is None:
            kernel_size = 5
        else:
            kernel_size = params[0]
        label = segmentation.quickshift(im, kernel_size=kernel_size)
        return label

    def _fetch_data(self):
        data_id = None
        data = None
        self.mutex.acquire()
        if not self.inqueue.empty():
            val = self.inqueue.get()
            data_id = val[0]
            data = val[1]
        self.mutex.release()
        return data_id, data

    def _dump_data(self, data_id, data):
        # Here might block the thread
        while self._thread_state:
            if self.outqueue.full():
                # Indicate the out buf might not be flushed
                time.sleep(0.1)
                continue
            self.outqueue.put([data_id, data])
            break

    def _thread(self):
        """
        This is the main thread to segment the image and get the result
        """
        while self._thread_state:
            # Get the data
            data_id, data = self._fetch_data()
            if data is None or data_id is None:
                time.sleep(0.1)
                continue
            # Cut the image
            rst = self.func_seg_image(data)

            # Put them to out buffer
            self._dump_data(data_id, rst)
