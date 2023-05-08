import os
import os.path
import sys
import time

import sqlite3


def initdb(sqlitedb, wal, verbose=0):
    if os.path.exists(sqlitedb):
        raise ValueError('file found: {} refusing to overwrite'.format(sqlitedb))

    if verbose:
        print('initializing sqlite db', sqlitedb, file=sys.stderr)
    con = sqlite3.connect(sqlitedb)
    cur = con.cursor()

    # XXX this list is also in collect.py
    fields = ('t_static', 't_first', 't_second', 't_first_miss', 't_second_miss', 't_s3', 't_s3_miss')
    errors = ('timeout', 'connection_error', 'slow_down', 'unknown')  # XXX http_
    errors = ['cdx_'+e for e in errors] + ['s3_'+e for e in errors]

    fields_str = ','.join(f+' REAL' for f in fields)
    errors_str = ','.join(e+' INTEGER' for e in errors)

    cur.execute('CREATE TABLE timing (time INTEGER NOT NULL, {})'.format(fields_str))
    cur.execute('CREATE INDEX idx_timing ON timing(time)')

    cur.execute('CREATE TABLE errors (time INTEGER NOT NULL, {})'.format(errors_str))
    cur.execute('CREATE INDEX idx_errors ON errors(time)')

    if wal != 0:
        # cli.py default is None, which != 0
        # there are places below which assume WAL is on
        configure_wal(cur, wal, verbose=verbose)

    cur.close()
    con.commit()
    con.close()
    return 0


def connect(database, *args, verbose=0, **kwargs):
    con = sqlite3.connect(database, *args, **kwargs)

    cur = con.cursor()
    configure_wal(cur, verbose=verbose)
    cur.close()

    if verbose:
        cur = con.cursor()
        for row in cur.execute('PRAGMA journal_mode'):
            assert row[0] == 'wal'
        for row in cur.execute('PRAGMA synchronous'):
            print(row)
            assert row[0] == 1  # 1=NORMAL, does not persist
        for row in cur.execute('PRAGMA wal_autocheckpoint'):
            assert row[0] == 1000  # the default
        cur.close()
    return con


def configure_wal(cur, wal_size=None, verbose=0):
    if verbose:
        print('setting up Write Ahead Log (WAL) in sqlite db, size in pages is', wal_size, file=sys.stderr)
    # XXX
    #if not os.access(path, os.W_OK):
    #    raise ValueError()
    # or look for cc-monitoring.db-shm  cc-monitoring.db-wal

    cur.execute('PRAGMA journal_mode=WAL')
    # recommended for WAL. affects "main" database, does not persist
    cur.execute('PRAGMA synchronous=NORMAL')
    if wal_size is not None:
        # defaults to 1000 4k pages (4 MB), does not persist
        cur.execute('PRAGMA wal_autocheckpoint={}'.format(wal_size))


def write(con, ts, table, data, verbose=0):
    cur = con.cursor()

    if verbose:
        print('inserting', len(data), 'items', file=sys.stderr)

    for k, v in list(data.items()):
        if v is None or k.startswith('http_'):  # http_ not yet created
            del data[k]

    ts = int(ts)
    t0 = time.time()
    cols_str = ','.join(['time', *data.keys()])
    values_str = ','.join('?' * (len(data)+1))
    data_tuple = [ts, *data.values()]

    if verbose:
        print('cols', cols_str)
        print('values', values_str)
        print('data', data_tuple)

        # cols t_static,t_first,t_second,t_first_miss,t_second_miss,t_s3,t_s3_miss
        # values ?,?,?,?,?,?,?
        # data [dict_values([0.309, 0.323, None, 0.343, None, 0.175, 0.701])]
        # skipping OperationalError('near "?": syntax error') {'t_static': 0.309, 't_first': 0.323, 't_second': None, 't_first_miss': 0.343, 't_second_miss': None, 't_s3': 0.175, 't_s3_miss': 0.701}

    try:
        # the following expects data to have a particular order and to contain all columns in the table
        # INSERT INTO table (col1, ...) VALUES (v1, ...);
        cur.execute('INSERT INTO {} ({}) VALUES({})'.format(table, cols_str, values_str), data_tuple)
    except sqlite3.OperationalError as e:
        # sqlite3.OperationalError: no such table: ts_param_127_0_0_1
        if verbose:
            print('skipping', repr(e), data, file=sys.stderr)

    cur.close()

    if verbose > 1:
        print('sqlite insert_many took {} seconds'.format(round(time.time() - t0, 3)))
