# this is a wrapper for threading.
# Since by default, the threading module can not give return value
# this wrapper can get the return value just by calling the join()
# Usage:
# def add(x,y):
#     return x +y
#
# add_worker = ThreadWorker(add)
# print add_worker.start((1,2,))
# print add_worker.status()
# print add_worker.get_results()
# or
# print add_worker.join()
import threading


class ThreadWorker():
    '''
    The basic idea is given a function create an object.
    The object can then run the function in a thread.
    It provides a wrapper to start it,check its status,and get data out
    the function.
    '''
    def __init__(self, func):
        self.thread = None
        self.data = None
        self.func = self.save_data(func)

    def save_data(self, func):
        '''modify function to save its returned data'''
        def new_func(*args, **kwargs):
            self.data = func(*args, **kwargs)

        return new_func

    def start(self, params):
        self.data = None
        if self.thread is not None:
            if self.thread.isAlive():
                # could raise exception here
                return 'running'

        # unless thread exists and is alive start or restart it
        self.thread = threading.Thread(target=self.func, args=params)
        self.thread.start()
        return 'started'

    def join(self):
        """
        Join the thread and return the result
        """
        self.thread.join()
        return self.data

    def status(self):
        if self.thread is None:
            return 'not_started'
        else:
            if self.thread.isAlive():
                return 'running'
            else:
                return 'finished'

    def get_results(self):
        if self.thread is None:
            # could return exception
            return 'not_started'
        else:
            if self.thread.isAlive():
                return 'running'
            else:
                return self.data
