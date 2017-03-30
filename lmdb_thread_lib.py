#!/usr/bin/python

# This module create a object that can be used as an indenpendent
# thread, which will accelerate the lmdb write process

import Queue
import time
import lmdb_tools
import threading


class DbWriteThread(threading.Thread):
    """
    This class is a indenpendent writting thread, it will create a queue
    User can put list: [key, val] in this queue.
    The thread will watch the queue and keep write the data in the lmdb
    file until the queue is empty.
    """
    def __init__(self, db, queue_size=1000, dumper=None):
        """
        The db can be the db file name and also can be the lmdb db object
        which is already been opened.
        So, it can be a 'str' and also can be a db object
        The queue_size is the size of the queue

        dumper: If set, the content of the input will be converted to
        string by the dumper function, e.g. pickle.dumps or yaml.dump or str
        If not set, it will be assumed the content already been string type
        """
        # Call the parents __init__ first
        super(DbWriteThread, self).__init__()

        if type(db) == str:
            self.db = lmdb_tools.open(db)
            self.need_close = True
        else:
            self.db = db
            self.need_close = False

        # Create the queue
        self.queue = Queue.Queue(maxsize=queue_size)
        # When set to True, the thread will keep runing
        # When set to False, the thread will exit
        self._thread_state = True
        self.dumper = dumper
        # Indicate whether the IO of this object is balance
        # When put a number to inqueue, +1
        # When write a number to outqueue, -1
        self.io_balance = 0
        # Lock to avoid the disorder of the io_balance
        self.mutex = threading.Lock()

    def __del__(self):
        if self.need_close:
            lmdb_tools.close(self.db)

    def get_db_entries(self):
        return lmdb_tools.get_entries(self.db)

    def readytojoin(self):
        return self.queue.empty() and self.io_balance == 0

    def join(self):
        """
        Call this to signal the thread exit
        """
        self._thread_state = False
        super(DbWriteThread, self).join()

    def put(self, val):
        """
        Call this to put [key, val] into the queue
        """
        key = val[0]
        content = val[1]
        if self.dumper is not None:
            content = self.dumper(content)
        self.queue.put([key, content])
        self.mutex.acquire()
        self.io_balance += 1
        self.mutex.release()

    def _read_queue_until_empty(self):
        data_list = []
        while not self.queue.empty():
            data_list.append(self.queue.get())
            self.queue.task_done()
        return data_list

    def run(self):
        """
        The main exe code in this function
        When the start function is called, this function will be exec
        """
        # A loop until the self._thread_state be False
        while self._thread_state:
            data_list = self._read_queue_until_empty()
            if len(data_list) == 0:
                time.sleep(0.2)
                continue
            # Store the data into lmdb
            with self.db.begin(write=True) as txn:
                for data in data_list:
                    key = data[0]
                    val = data[1]
                    txn.put(key, val)
                    self.mutex.acquire()
                    self.io_balance -= 1
                    self.mutex.release()

            # Sleep a while
            time.sleep(0.2)

        # Before exit, Flush the buffer again, incase there are data remains
        data_list = self._read_queue_until_empty()
        if len(data_list) == 0:
            return
        # Store the data into lmdb
        with self.db.begin(write=True) as txn:
            for data in data_list:
                key = data[0]
                val = data[1]
                txn.put(key, val)
                self.mutex.acquire()
                self.io_balance -= 1
                self.mutex.release()


# =========================================================================

class DbReadThread(threading.Thread):
    """
    This class is a indenpendent reading thread, it will create a queue
    User can put key in this queue.
    The thread will watch the queue and keep reading the data in the lmdb
    file until the queue is empty.
    The class will also maintain a read queue, through it, user can read
    a [key, val] list to get the value of the target key
    """
    def __init__(self, db, queue_size=1000, dumper=None):
        """
        The db can be the db file name and also can be the lmdb db object
        which is already been opened.
        So, it can be a 'str' and also can be a db object
        The queue_size is the size of the queue

        dumper: If set, the content of the input will be converted to
        string by the dumper function, e.g. pickle.dumps or yaml.dump or str
        If not set, it will be assumed the content already been string type
        """
        # Call the parents __init__ first
        super(DbReadThread, self).__init__()

        if type(db) == str:
            self.db = lmdb_tools.open_ro(db)
            self.need_close = True
        else:
            self.db = db
            self.need_close = False

        # Create the queue
        self.inqueue = Queue.Queue(maxsize=queue_size)
        self.outqueue = Queue.Queue(maxsize=queue_size)
        # When set to True, the thread will keep runing
        # When set to False, the thread will exit
        self._thread_state = True
        self.dumper = dumper
        # Indicate whether the IO is balance
        self.io_balance = 0

    def __del__(self):
        if self.need_close:
            lmdb_tools.close(self.db)

    def get_db_entries(self):
        return lmdb_tools.get_entries(self.db)

    def readytojoin(self):
        return self.inqueue.empty() and\
            self.outqueue.empty() and\
            self.io_balance == 0

    def join(self):
        """
        Call this to signal the thread exit
        """
        self._thread_state = False
        super(DbReadThread, self).join()

    def put(self, val, block=True):
        """
        Call this to put [key, val] into the queue
        """
        key = val
        if self.dumper is not None:
            key = self.dumper(key)
        self.inqueue.put(key, block)
        self.io_balance += 1

    def get(self, block=True):
        """
        Get the data from the outqueue
        If the outqueue is empty, the function will block the thread
        """
        self.io_balance -= 1
        return self.outqueue.get(block)

    def full(self):
        """
        Return if the inqueue is full
        """
        return self.inqueue.full()

    def empty(self):
        """
        Return if the outqueue is empty
        """
        return self.outqueue.empty()

    def get_inqueue_size(self):
        return self.inqueue.qsize()

    def get_outqueue_size(self):
        return self.outqueue.qsize()

    def _read_queue_until_empty(self):
        data_list = []
        while not self.inqueue.empty():
            data_list.append(self.inqueue.get())
            self.inqueue.task_done()
        return data_list

    def run(self):
        """
        The main exe code in this function
        When the start function is called, this function will be exec
        """
        # A loop until the self._thread_state be False
        while self._thread_state:
            data_list = self._read_queue_until_empty()
            if len(data_list) == 0:
                time.sleep(0.2)
                continue

            # Store the data into lmdb
            with self.db.begin(write=False) as txn:
                for key in data_list:
                    val = txn.get(key)
                    # Dump the data to the out queue
                    self.outqueue.put([key, val])

        # Before exit, Flush the buffer again, incase there are data remains
        data_list = self._read_queue_until_empty()
        if len(data_list) == 0:
            return
        # Store the data into lmdb
        with self.db.begin(write=False) as txn:
            for key in data_list:
                val = txn.get(key)
                self.outqueue.put([key, val])
