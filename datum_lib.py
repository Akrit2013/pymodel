#!/usr/bin/python

# This module contains the class related to datum structure

import Queue
import threading
import time
import caffe_tools
import numpy as np


class DatumConverter:
    """
    This class can convert the ndarray to datum in mult thread
    way.
    And the datum will be convert to string and saved in a queue
    to be fetched.
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
        self.buf_size = 100
        # The wait time to copy data from in queue to in buffer
        self.block_time = 5
        self.mutex = threading.Lock()
        # To keep the result orgnized, we can not directly send the output
        # and read the input, so, we keep a in buffer and a out buffer apart
        # from the queues, and create a separate thread orgnize it
        self._master = None
        self._clear_buf()
        # Record the current buffer size
        self._curr_buf_sz = 0
        # How to convert array to datum
        self.func_array_to_datum = caffe_tools.load_array_im_to_datum
        # Indicate whether the IO is balance
        self.io_balance = 0
        # The data type of the array should be converted in to datum
        # If set to None, that means it will use the default parameter
        # of the datum converter function
        self._dtype = None

    def start(self):
        """
        Start the threads, which keep monitor the inqueue and try to convert
        array to datum and to string
        """
        # Start the monitor thread
        self._master = threading.Thread(
            target=self._master_thread
        )
        self._master.start()
        # Start the worker thread
        for i in range(self.thread_num):
            hThread = threading.Thread(
                target=self._thread
            )
            hThread.start()
            self.thread_pool.append(hThread)

    def set_dtype(self, type_str):
        """
        Set the data type if the array should be force converted before
        converted into datum
        """
        self._dtype = np.dtype(type_str)

    def set_type_md_vec(self):
        """
        Call this function, the given array will be considered as multi
        dimension vector instead of images.
        Accoridingly, the channels will not be altered
        """
        self.func_array_to_datum = caffe_tools.load_array_to_datum

    def _is_inbuf_empty(self):
        """
        Check if the in buffer is empty
        """
        for idx in range(self._curr_buf_sz):
            ele = self.in_buf[idx]
            if ele is not None:
                return False
        return True

    def _is_outbuf_empty(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            if ele is not None:
                return False
        return True

    def _is_outbuf_full(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            if ele is None:
                return False
        return True

    def _clear_buf(self, size=None):
        if size is None:
            size = self.buf_size
        self.in_buf = [None for i in range(self.buf_size)]
        self.out_buf = [None for i in range(self.buf_size)]

    def _copy_inqueue_to_inbuf(self):
        # Mark the start time
        start_time = time.time()
        # Lock the mutex
        # This will wait until the lock is released by someone else
        self.mutex.acquire()
        idx = 0
        while self._thread_state:
            if self.inqueue.empty():
                time.sleep(0.1)
                # Can not wait too long to fill the buf
                if (time.time()-start_time) > self.block_time:
                    break
                continue
            # This place may block the thread
            val = self.inqueue.get()
            self.inqueue.task_done()
            self.in_buf[idx] = val
            idx += 1
            if idx >= self.buf_size:
                break
        # Set the current buffer size
        self._curr_buf_sz = idx
        # Release the mutex
        self.mutex.release()

    def _copy_outbuf_to_outqueue(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            # This place may block the thread
            self.outqueue.put(ele)
            self.out_buf[idx] = None

    def _fetch_data(self):
        """
        This function fetch data and corresponding index from the
        in buffer.
        """
        data = None
        index = None
        self.mutex.acquire()
        for idx in range(self._curr_buf_sz):
            val = self.in_buf[idx]
            if val is not None:
                data = val
                index = idx
                self.in_buf[idx] = None
                break
        self.mutex.release()
        return data, index

    def _dump_data(self, data, index):
        """
        This function dump the data to out buffer according to the
        index
        """
        # Here might block the thread
        while self._thread_state:
            if self.out_buf[index] is not None:
                # Indicate the out buf might not be flushed
                time.sleep(0.1)
                continue
            self.out_buf[index] = data
            break

    def _master_thread(self):
        """
        This thread keep copy a block of data in the in_buf
        and copy the full out_buf to out_queue
        """
        while self._thread_state:
            # Check if in buf is empty
            if self._is_inbuf_empty() and self._is_outbuf_full():
                # That means that the this batch is finished
                # Flush the output
                # The out must be called before the in func
                self._copy_outbuf_to_outqueue()
                # Reload
                self._copy_inqueue_to_inbuf()
            else:
                time.sleep(0.1)

    def _thread(self):
        """
        This is the main thread to convert the array to datum
        and then convert it to string
        """
        while self._thread_state:
            # Get the data
            data, index = self._fetch_data()
            if data is None or index is None:
                time.sleep(0.1)
                continue
            # Convert the array to datum
            if self._dtype is None:
                # Need not to convert the data type
                datum = self.func_array_to_datum(data)
            else:
                datum = self.func_array_to_datum(data, self._dtype)

            # Convert the datum to string
            data_str = datum.SerializeToString()
            # Put them to out buffer
            self._dump_data(data_str, index)

    def put(self, arr, block=True):
        """
        Here the thread might be blocked
        """
        self.inqueue.put(arr, block)
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
        return self._is_inbuf_empty() and\
            self._is_outbuf_empty() and\
            self.inqueue.empty() and\
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
        self._master.join()
        self._master = None
        # Clear the mess
        self._clear_buf()

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
        return val


# ==========================================================================
class DatumConverterBack():
    """
    This class convert the string to datum and to ndarray in multi-thread
    way
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
        self.buf_size = 100
        # The wait time to copy data from in queue to in buffer
        self.block_time = 5
        self.mutex = threading.Lock()
        # To keep the result orgnized, we can not directly send the output
        # and read the input, so, we keep a in buffer and a out buffer apart
        # from the queues, and create a separate thread orgnize it
        self._master = None
        self._clear_buf()
        # Record the current buffer size
        self._curr_buf_sz = 0
        # How to convert string to array
        self.func_str_to_array = caffe_tools.datum_str_to_array_im
        # Indicate whether the IO is balance
        self.io_balance = 0

    def start(self):
        """
        Start the threads, which keep monitor the inqueue and try to convert
        array to datum and to string
        """
        # Start the monitor thread
        self._master = threading.Thread(
            target=self._master_thread
        )
        self._master.start()
        # Start the worker thread
        for i in range(self.thread_num):
            hThread = threading.Thread(
                target=self._thread
            )
            hThread.start()
            self.thread_pool.append(hThread)

    def set_type_md_vec(self):
        """
        Call this function, the given array will be considered as multi
        dimension vector instead of images.
        Accoridingly, the channels will not be altered
        """
        self.func_str_to_array = caffe_tools.datum_str_to_array

    def _is_inbuf_empty(self):
        """
        Check if the in buffer is empty
        """
        for idx in range(self._curr_buf_sz):
            ele = self.in_buf[idx]
            if ele is not None:
                return False
        return True

    def _is_outbuf_empty(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            if ele is not None:
                return False
        return True

    def _is_outbuf_full(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            if ele is None:
                return False
        return True

    def _clear_buf(self, size=None):
        if size is None:
            size = self.buf_size
        self.in_buf = [None for i in range(self.buf_size)]
        self.out_buf = [None for i in range(self.buf_size)]

    def _copy_inqueue_to_inbuf(self):
        # Mark the start time
        start_time = time.time()
        # Lock the mutex
        # This will wait until the lock is released by someone else
        self.mutex.acquire()
        idx = 0
        while self._thread_state:
            if self.inqueue.empty():
                time.sleep(0.1)
                # Can not wait too long to fill the buf
                if (time.time()-start_time) > self.block_time:
                    break
                continue
            # This place may block the thread
            val = self.inqueue.get()
            self.inqueue.task_done()
            self.in_buf[idx] = val
            idx += 1
            if idx >= self.buf_size:
                break
        # Set the current buffer size
        self._curr_buf_sz = idx
        # Release the mutex
        self.mutex.release()

    def _copy_outbuf_to_outqueue(self):
        for idx in range(self._curr_buf_sz):
            ele = self.out_buf[idx]
            # This place may block the thread
            self.outqueue.put(ele)
            self.out_buf[idx] = None

    def _fetch_data(self):
        """
        This function fetch data and corresponding index from the
        in buffer.
        """
        data = None
        index = None
        self.mutex.acquire()
        for idx in range(self._curr_buf_sz):
            val = self.in_buf[idx]
            if val is not None:
                data = val
                index = idx
                self.in_buf[idx] = None
                break
        self.mutex.release()
        return data, index

    def _dump_data(self, data, index):
        """
        This function dump the data to out buffer according to the
        index
        """
        # Here might block the thread
        while self._thread_state:
            if self.out_buf[index] is not None:
                # Indicate the out buf might not be flushed
                time.sleep(0.1)
                continue
            self.out_buf[index] = data
            break

    def _master_thread(self):
        """
        This thread keep copy a block of data in the in_buf
        and copy the full out_buf to out_queue
        """
        while self._thread_state:
            # Check if in buf is empty
            if self._is_inbuf_empty() and self._is_outbuf_full():
                # That means that the this batch is finished
                # Flush the output
                # The out must be called before the in func
                self._copy_outbuf_to_outqueue()
                # Reload
                self._copy_inqueue_to_inbuf()
            else:
                time.sleep(0.1)

    def _thread(self):
        """
        This is the main thread to convert the array to datum
        and then convert it to string
        """
        while self._thread_state:
            # print 'inqueue size:'+str(self.inqueue.qsize())
            # print 'outqueue size:'+str(self.outqueue.qsize())
            # Get the data
            data, index = self._fetch_data()
            if data is None or index is None:
                time.sleep(0.1)
                continue
            # Convert the string to array

            im_arr = self.func_str_to_array(data)
            # Put them to out buffer
            self._dump_data(im_arr, index)

    def put(self, arr, block=True):
        """
        Here the thread might be blocked
        """
        self.inqueue.put(arr, block)
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
        return self._is_inbuf_empty() and\
            self._is_outbuf_empty() and\
            self.inqueue.empty() and\
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
        self._master.join()
        self._master = None
        # Clear the mess
        self._clear_buf()

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
        return val
