#!/usr/bin/python

# This lib include the class can perform the basic opeartions
# on the lmdb database

import lmdb_tools
import glog as log
import timer_lib


class lmdb:
    """
    This class can perform read / write / list and almost all
    required operation on the lmdb database
    """
    def __init__(self, db_file, readonly=True, echo=True, append=False):
        self.readonly = readonly
        self.db_file = db_file
        self._echo = echo
        self._warn = True
        # If max commit interval time is 60 sec, it the commit interval
        # is more than it, the buffer will be commited.
        self._max_commit_interval = 60
        # The timer
        self._timer = timer_lib.timer(start=True)

        # Define the dumper of the key and value
        self._key_dumper = None
        self._val_dumper = None
        self._key_parser = None
        self._val_parser = None
        # The size of the commit buffer
        self._buf_size = 100
        self._buf_counter = 0
        self._cur = None
        self._iter = None

        if readonly:
            self.db = lmdb_tools.open_ro(db_file)
        else:
            self.db = lmdb_tools.open(db_file, append=append)

        if self.db is None:
            log.error('\033[01;31mERROR\033[0m: Can not open the \
db file \033[32m%s\033[0m' % db_file)
            return

        self._txn = self.db.begin(write=not self.readonly)

        if echo:
            log.info('Open %s, size: \033[01;31m%d\033[0m'
                     % (db_file, self.get_entries()))

    def __del__(self):
        self._txn.commit()
        if self._echo:
            log.info('Close \033[0;32m%s\033[0m, \
entries: \033[0;31m%d\033[0m' % (self.db_file, self.get_entries()))
        self.db.close()

    def __iter__(self):
        self._cur = self._txn.cursor()
        self._iter = self._cur.__iter__()
        return self

    def next(self):
        key, val = self._iter.next()
        return self._parse(key, self._key_parser), \
            self._parse(val, self._val_parser)
        # raise StopIteration

    def set_buf_size(self, buf_size):
        self._buf_size = buf_size

    def set_key_dumper(self, dumper_func):
        self._key_dumper = dumper_func

    def set_key_parser(self, parser_func):
        self._key_parser = parser_func

    def set_val_dumper(self, dumper_func):
        self._val_dumper = dumper_func

    def set_val_parser(self, parser_func):
        self._val_parser = parser_func

    def disable_warn(self):
        self._warn = False

    def check_key(self, key):
        """
        Check if the database already have the key
        """
        key = self._dump(key, self._key_dumper)
        val = self._txn.get(key)
        if val is None:
            return False
        return True

    def get_keylist(self, num=None):
        """
        NOTE: this function will use the parser to process the key
        if needed
        Param:
            If set the number, it only return the first num keys of
            the whole dataset, it is useful when the dataset is too
            large to get the whole keylist
        """
        key_list = []
        with self._txn.cursor() as cur:
            for key, val in cur:
                key = self._parse(key, self._key_parser)
                key_list.append(key)
                if num is not None and len(key_list) >= num:
                    break
        return key_list

    def get_entries(self):
        # self.commit()
        return lmdb_tools.get_entries(self.db)

    def get(self, key):
        """
        IF the key dose not exist, return None
        """
        val = None
        key = self._dump(key, self._key_dumper)
        val = self._txn.get(key)
        if val is None:
            if self._warn:
                log.error('\033[01;31mERROR:\033[0m Can not get \
    key: \033[0;31n%s\033[0m from db' % key)
            return None

        return self._parse(val, self._val_parser)

    def put(self, key, val):
        key = self._dump(key, self._key_dumper)
        val = self._dump(val, self._val_dumper)
        self._txn.put(key, val)
        self._buf_counter += 1
        if self._buf_counter > self._buf_size or \
                self._timer.elapse() > self._max_commit_interval:
            self.commit()
            self._timer.start()
            self._buf_counter = 0

    def write_dict(self, key_val_dict):
        """
        This function write the whole dict into the db, the key will be the
        key, and the val is the val
        """
        for key in key_val_dict:
            val = key_val_dict[key]
            self.put(key, val)
        self.commit()

    def load_dict(self):
        """
        Load the whole db as a dict
        """
        rst_dict = {}
        with self._txn.cursor() as cur:
            for key, val in cur:
                key = self._parse(key, self._key_parser)
                val = self._parse(val, self._val_parser)
                rst_dict[key] = val
        return rst_dict

    def delete(self, key):
        key = self._dump(key, self._key_dumper)
        self._txn.delete(key)
        self._buf_counter += 1
        if self._buf_counter > self._buf_size:
            self.commit()
            self._buf_counter = 0

    def delete_keylist(self, key_list):
        for key in key_list:
            self.delete(key)
        self.commit()

    def commit(self):
        self._txn.commit()
        self._txn = self.db.begin(write=not self.readonly)

    def _dump(self, val, dumper):
        """
        If the val is already a string and the dumper is None
        the val will be remain the same.
        If the val is not a string, and the dumper is None, it will
        try to use str() to convert to the val to string, and give a warning
        """
        if dumper is not None:
            return dumper(val)
        if type(val) is str:
            return val
        val_str = str(val)
        log.warn('\033[0;32mWARNING:\033[0m The %s is not a string, try using \
str() to convert is' % val_str)
        return val_str

    def _parse(self, val, parser):
        if parser is not None:
            return parser(val)
        return val

    def _get_keylist(self):
        """
        NOTE: this function will NOT use the parser to process the key
        """
        key_list = []
        with self._txn.cursor() as cur:
            for key, val in cur:
                key_list.append(key)
        return key_list
