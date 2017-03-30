#!/usr/bin/python

# This model is a wrapper of the lmdb_tools.py, which wrap the functions
# and include necessary log information

import lmdb_tools
import glog as log
import lmdb_lib


def open(db_file):
    log.info('Opening lmdb file: \033[0;33m%s\033[0m' % db_file)
    db = lmdb_tools.open(db_file)
    log.info('Db size: \033[0;32m%d\033[0m' % lmdb_tools.get_entries(db))
    return db


def open_ro(db_file):
    log.info('Opening lmdb file: \033[0;33m%s\033[0m for read only' % db_file)
    db = lmdb_tools.open_ro(db_file)
    log.info('Db size: \033[0;32m%d\033[0m' % lmdb_tools.get_entries(db))
    return db


def save_dict_to_db(db_file, key_dict, operation=None, append=False):
    """
    Open a new db (if exist, ask whether to delete the old one)
    save the dict to db and close.
    NOTE:
        1. If the key is not string, use str to convert it
        2. If the val is not string, try str first, if not work, use pickle
    """
    log.info('Saving dict to \033[0;33m%s\033[0m, the size of dict \
is \033[0;32m%d\033[0m' % (db_file, len(key_dict)))

    db = lmdb_tools.open(db_file, append)
    try:
        lmdb_tools.write_dict(db, key_dict, operation)
    except:
        try:
            lmdb_tools.write_dict_str(db, key_dict)
        except:
            lmdb_tools.write_dict_pickle(db, key_dict)

    log.info('Finished, the Db size: \033[0;32m%d\033[0m'
             % lmdb_tools.get_entries(db))
    lmdb_tools.close(db)


def load_dict_from_db(db_file, operation=None):
    """
    Open a db and load the content into a dict. close the db after finish
    The operation defines how to convert the value back to its original format
    """
    log.info('Loading from \033[0;33m%s\033[0m' % db_file)
    db = lmdb_tools.open_ro(db_file)
    rst_dict = lmdb_tools.read_dict(db, operation)
    lmdb_tools.close(db)
    log.info('Finish. loaded \033[0;32m%d\033[0m lines' % len(rst_dict))
    return rst_dict


def load_keylist_from_db(db_file):
    """
    Load the keys from a lmdb file, return the keys as a list
    """
    log.info('Loading keys from \033[0;33m%s\033[0m' % db_file)
    db = lmdb_tools.open_ro(db_file)
    rst_list = lmdb_tools.get_keylist(db)
    lmdb_tools.close(db)
    log.info('Finish. loaded \033[0;32m%d\033[0m lines' % len(rst_list))
    return rst_list


def delete_keylist_from_db(db_file, key_list):
    """
    Open the db file, delete the keys in the key list
    """
    db = lmdb_tools.open(db_file, append=True)
    log.info('Deleting entries from \033[0;33m%s\033[0m, \
Db size: \033[0;32m%d\033[0m, list size: \033[0;32m%d\033[0m'
             % (db_file, lmdb_tools.get_entries(db), len(key_list)))
    lmdb_tools.delete_keylist(db, key_list)
    log.info('Finish. DB size: \033[0;32m%d\033[0m'
             % lmdb_tools.get_entries(db))
    lmdb_tools.close(db)


def append_db(db_file_src, db_file_dst):
    """
    Append all contains of db_file_src to db_file_dst
    """
    db_src = lmdb_tools.open_ro(db_file_src)
    log.info('Src Db \033[0;33m%s\033[0m size: \033[0;32m%d\033[0m'
             % (db_file_src, lmdb_tools.get_entries(db_src)))
    db_dst = lmdb_tools.open(db_file_dst, append=True)
    log.info('Dst Db \033[0;33m%s\033[0m size: \033[0;32m%d\033[0m'
             % (db_file_dst, lmdb_tools.get_entries(db_dst)))
    with db_src.begin(write=False) as txn_src:
        with txn_src.cursor() as cur:
            for key, val in cur:
                with db_dst.begin(write=True) as txn_dst:
                    txn_dst.put(key, val)
    log.info('Append Finished. Dst Size: \033[0;32m%d\033[0m' %
             lmdb_tools.get_entries(db_dst))
    lmdb_tools.close(db_src)
    lmdb_tools.close(db_dst)


def merge_dbs(out_db, use_org_keys, *in_dbs):
    """
    This function will merge multi lmdb file into one.
    If use_org_keys is True:
        It will use the original keys in each lmdb, if the repeated
        key is found, this function will check if the val are same, if
        not, give a warning.
    else:
        It wll use a unique 10 chars key to record all entries
    """
    counter = 0
    DB_out = lmdb_lib.lmdb(out_db, readonly=False)
    DB_out.disable_warn()
    DB_in_list = []
    for in_db in in_dbs:
        DB_in = lmdb_lib.lmdb(in_db)
        DB_in_list.append(DB_in)

    for DB_in in DB_in_list:
        for key, val in DB_in:
            if use_org_keys is True:
                cur_val = DB_out.get(key)
                if cur_val is None:
                    DB_out.put(key, val)
                else:
                    if val == cur_val:
                        continue
                    else:
                        log.warn('\033[33mWARNING\033[0m: Detected confliction \
in key %s' % key)
                        continue
            else:
                new_key = '{:0>10d}'.format(counter)
                counter += 0
                DB_out.put(new_key, val)
