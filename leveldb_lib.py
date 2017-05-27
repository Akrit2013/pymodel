#!/usr/bin/python

# This lib include the class can perform the basic opeartions
# on the leveldb lmdb_tools
import glog as log
import plyvel
import color_lib
import path_tools
import shutil
import sys
import timer_lib


class leveldb:
    """
    This class can perform read / write / list and almost all
    required operation on the leveldb database
    """
    def __init__(self, db_file, readonly=True, echo=True, append=False):
        self._db_file = db_file
        self._echo = echo
        self._warn = True
        # If max commit interval time is 60 sec, it the commit interval
        # is more than it, the buffer will be commited.
        self._max_commit_interval = 60
        # The timer
        self._timer = timer_lib.timer(start=True)
        self._color = color_lib.color(bold=True)
        self._err = self._color.red('ERROR') + ': '
        self._warn = self._color.yellow('WARNING') + ': '
        self._info = self._color.green('INFO') + ': '

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
        # The keylist of the keys
        self._key_list = []
        # If true, need to regenerate the key list
        self._dirty_key_list = True

        if readonly:
            if not path_tools.check_path(self._db_file, False):
                log.error(self._err + 'Can not find the ' +
                          self._color.yellow(self._db_file))
                return
            self._db = plyvel.DB(self._db_file)
        else:
            if path_tools.check_path(self._db_file, False):
                print('%s %s already exists.'
                      % (self._warn, self._color.red(self._db_file)))
                k = raw_input('Do you want to delete it?[y/n]:')
                if k == 'y' or k == 'Y':
                    log.warn('Delete the %s file' % self._db_file)
                    shutil.rmtree(self._db_file)
                elif k == 'n' or k == 'N':
                    log.warn('Keep the %s file, and new entries will be added'
                             % self._db_file)
                else:
                    log.error('Wrong key input, exit the program')
                    sys.exit(2)

            self._db = plyvel.DB(self._db_file, create_if_missing=True)

        if self._db is None:
            log.error('\033[01;31mERROR\033[0m: Can not open the \
db file \033[32m%s\033[0m' % self._db_file)
            return

        if echo:
            log.info(self._info + 'Open ' +
                     self._color.yellow(self._db_file))

    def __del__(self):
        if self._echo:
            db_size = 'n/a'
            if not self._dirty_key_list:
                db_size = str(len(self._key_list))
            log.info(self._info + 'Close \033[0;32m%s\033[0m, \
db size: %s' % (self._db_file, self._color.red(db_size)))
        self._db.close()

    def __iter__(self):
        self._iter = self._db.iterator()
        return self

    def _gen_keylist(self, num=None):
        if self._dirty_key_list:
            self._key_list = []
            counter = 0
            for key in self._db.iterator(include_value=False):
                self._key_list.append(key)
                counter += 1
                if num is not None and counter > num:
                    return
            self._dirty_key_list = False

    def next(self):
        key, val = self._iter.next()
        return self._parse(key, self._key_parser), \
            self._parse(val, self._val_parser)
        # raise StopIteration

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
        self._gen_keylist()
        key = self._dump(key, self._key_dumper)
        if key in self._key_list:
            return True
        else:
            return False

    def get_keylist(self, num=None):
        """
        NOTE: this function will use the parser to process the key
        if needed
        Param:
            If set the number, it only return the first num keys of
            the whole dataset, it is useful when the dataset is too
            large to get the whole keylist
        """
        self._gen_keylist(num)
        return self._key_list

    def get_entries(self):
        self._gen_keylist()
        return len(self._key_list)

    def get(self, key):
        """
        IF the key dose not exist, return None
        """
        val = None
        key = self._dump(key, self._key_dumper)
        val = self._db.get(key)
        if val is None:
            if self._warn:
                log.error('\033[01;31mERROR:\033[0m Can not get \
key: \033[0;31m%s\033[0m from db %s'
                          % (key, self._color.yellow(self._db_file)))
            return None

        return self._parse(val, self._val_parser)

    def put(self, key, val):
        key = self._dump(key, self._key_dumper)
        val = self._dump(val, self._val_dumper)
        self._db.put(key, val)
        self._dirty_key_list = True

    def write_dict(self, key_val_dict):
        """
        This function write the whole dict into the db, the key will be the
        key, and the val is the val
        """
        for key in key_val_dict:
            val = key_val_dict[key]
            self.put(key, val)

    def load_dict(self):
        """
        Load the whole db as a dict
        """
        rst_dict = {}
        for key, val in self._db.iterator():
            key = self._parse(key, self._key_parser)
            val = self._parse(val, self._val_parser)
            rst_dict[key] = val
        return rst_dict

    def delete(self, key):
        key = self._dump(key, self._key_dumper)
        self._db.delete(key)
        self._dirty_key_list = True

    def delete_keylist(self, key_list):
        for key in key_list:
            self.delete(key)

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
