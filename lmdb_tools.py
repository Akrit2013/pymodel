#!/usr/bin/python

# This model include the common tools related to lmdb database

import lmdb
import glog as log
import cPickle as pickle
import shutil
import sys
import yaml
import os


def close(db):
    """Close an opened lmdb
    """
    if db is not None:
        try:
            db.close()
        except:
            log.error('\033[0;31mClose lmdb error\033[0m')
    else:
            log.warn('\033[1;33mDB handle is None\033[0m')


def open(lmdb_file, append=False):
    """Check if the lmdb file already exists, and ask whether delete it
    or keep add entries based on it.
    return the lmdb object
    If the append is set to True, it will not ask user whether to del
    the exist lmdb, and directly write based on it
    """
    if os.path.exists(lmdb_file) and append is False:
        print('\033[0;31m%s\033[0m is already exists.' % lmdb_file)
        k = raw_input('Do you want to delete it?[y/n]:')
        if k == 'y' or k == 'Y':
            log.warn('Delete the %s file' % lmdb_file)
            shutil.rmtree(lmdb_file)
        elif k == 'n' or k == 'N':
            log.warn('Keep the %s file, and new entries will be added' %
                     lmdb_file)
        else:
            log.error('Wrong key input, exit the program')
            sys.exit(2)

    db = lmdb.open(lmdb_file, map_size=int(1e12))
    return db


def open_ro(lmdb_file):
    """Open the lmdb in READ ONLY mode, if the db file not exist, return
    None
    """
    db = None
    if os.path.exists(lmdb_file):
        try:
            db = lmdb.open(lmdb_file, readonly=True)
        except:
            log.fatal('\033[0;31mOpen lmdb %s error\033[0m' % lmdb_file)
            return None
    return db


def get_entries(db):
    """Return the entries number of the given db
    """
    stat = db.stat()
    return stat['entries']


def check_key(db, key):
    """Check if the lmdb database already have the given key, if true
    return True, else, return False
    """
    rst = None
    # Don't allow write, and use buffers to avoid memory copy
    with db.begin(write=False, buffers=True) as txn:
        val = txn.get(key)
        if val is None:
            rst = False
        else:
            rst = True
    return rst


def get_keylist(db):
    """This function iter the whole db and return the whole keys
    as a list.
    """
    key_list = []
    with db.begin(write=False) as txn:
        with txn.cursor() as cur:
            for key, val in cur:
                key_list.append(key)

    return key_list


def get_val(db, key, warn=True):
    """Get the val of given key, and return it
    """
    val = None
    with db.begin(write=False) as txn:
        val = txn.get(key)
    if val is None:
        if warn is True:
            log.error('\033[01;31mERROR:\033[0m Can not get \
key: \033[0;31n%s\033[0m from db' % key)
        return None
    return val


def get_val_pickle(db, key, warn=True):
    """
    Get the val of given key from db, and unpickle it
    """
    val = get_val(db, key, warn)
    try:
        val = pickle.loads(val)
    except:
        if warn is True:
            log.error('\033[01;31mERROR:\033[0m Can not unpickle the value of \
key: \033[0;31n%s\033[0m from db' % key)
        return None
    return val


def get_val_yaml(db, key, warn=True):
    """
    Get the val of given key from db, and unyaml it
    """
    val = get_val(db, key, warn)
    try:
        val = yaml.load(val)
    except:
        if warn is True:
            log.error('\033[01;31mERROR:\033[0m Can not unyaml the value of \
key: \033[0;31n%s\033[0m from db' % key)
        return None
    return val


def write(db, key, val, operation=None):
    """
    This function is a wrapper of the lmdb write method, it is a bit of slow
    since it only write one entry every time
    """
    if operation is not None:
        val = operation(val)

    with db.begin(write=True) as txn:
        txn.put(key, val)


def write_pickle(db, key, val):
    """
    Same as the write function, only difference is, this function will pickle
    dump the val first before write
    """
    val = pickle.dumps(val)
    write(db, key, val)


def write_yaml(db, key, val):
    """
    Same as the write function, only difference is, this function will yaml
    dump the val first before write
    """
    val = yaml.dump(val)
    write(db, key, val)


def write_str(db, key, val):
    """
    The val will be converted to str before write to lmdb
    """
    val = str(val)
    write(db, key, val)


def write_dict(db, key_dict, operation=None):
    """
    The key and the val is orgnized into a dict structure, write it into
    a lmdb file as once.
    NOTE: The key and the val of the dict must be in string type
    The operation param define how to convert the val to string
    """
    with db.begin(write=True) as txn:
        for key in key_dict:
            val = key_dict[key]
            if type(key) is not str:
                key = str(key)
            if operation is not None:
                val = operation(val)
            txn.put(key, val)


def write_dict_pickle(db, key_dict):
    """
    Write the given dict into the db, but use pickle to convert the vals
    to string first
    """
    new_dict = {}
    for key in key_dict:
        new_dict[key] = pickle.dumps(key_dict[key])

    write_dict(db, new_dict)


def write_dict_yaml(db, key_dict):
    """
    Write the given dict into the db, but use yaml to convert the vals
    to string first
    """
    new_dict = {}
    for key in key_dict:
        new_dict[key] = yaml.dump(key_dict[key])

    write_dict(db, new_dict)


def write_dict_str(db, key_dict):
    """
    Write the given dict into the db, but use str to convert the vals
    to string first
    """
    new_dict = {}
    for key in key_dict:
        new_dict[key] = str(key_dict[key])

    write_dict(db, new_dict)


def read_dict(db, operation=None):
    """
    Read all contents into a dict and return it
    The operation define how to convert the value back to its original
    format
    """
    rst_dict = {}
    with db.begin(write=False) as txn:
        with txn.cursor() as cur:
            for key, val in cur:
                if operation is not None:
                    val = operation(val)
                rst_dict[key] = val

    return rst_dict


def read_dict_pickle(db):
    """
    Read all contents into a dict and return it
    NOTE:
        all vals will be loads by pickle
    """
    rst_dict = read_dict(db)
    for key in rst_dict:
        rst_dict[key] = pickle.loads(rst_dict[key])

    return rst_dict


def read_dict_yaml(db):
    """
    Read all contents into a dict and return it
    NOTE:
        all vals will be loads by yaml
    """
    rst_dict = read_dict(db)
    for key in rst_dict:
        rst_dict[key] = yaml.load(rst_dict[key])

    return rst_dict


def read_dict_float(db):
    """
    Read all contents into a dict and return it
    NOTE:
        all vals will be converted to float
    """
    rst_dict = read_dict(db)
    for key in rst_dict:
        rst_dict[key] = float(rst_dict[key])

    return rst_dict


def read_dict_int(db):
    """
    Read all contents into a dict and return it
    NOTE:
        all vals will be converted to int
    """
    rst_dict = read_dict(db)
    for key in rst_dict:
        rst_dict[key] = int(rst_dict[key])

    return rst_dict


def delete(db, key):
    """
    Delete the given key, if key exist return True, else, return False
    """
    rst = None
    with db.begin(write=True) as txn:
        rst = txn.delete(key)

    return rst


def delete_keylist(db, key_list):
    """
    Delete keys in given key list
    """
    with db.begin(write=True) as txn:
        for key in key_list:
            txn.delete(key)
