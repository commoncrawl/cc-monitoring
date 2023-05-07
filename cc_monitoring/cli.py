from argparse import ArgumentParser
import time
import os
import os.path
import json
import sys

from . import collect
from . import sqlite


def main(args=None):
    parser = ArgumentParser(description='cc-monitoring command line utilities')

    parser.add_argument('--verbose', '-v', action='count', default=0, help='be verbose')
    parser.add_argument('--sqlitedb', action='store', default='cc-monitoring.db')

    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    initdb = subparsers.add_parser('initdb', help='initialize a sqlite database')
    initdb.add_argument('--wal', action='store', help='size of the write ahead log, default 1000 4k pages. 0 to disable.')
    initdb.set_defaults(func=sqlite.initdb)

    collect = subparsers.add_parser('collect', help='collect data and write to sqlite')
    collect.add_argument('--dt', action='store', type=int, default=300, help='time between calls, seconds, default=300')
    collect.set_defaults(func=collect_cli)

    cmd = parser.parse_args(args=args)
    return cmd.func(cmd)


def sleep_some(t_next, dt, verbose=0):
    if t_next is not None:
        delta = t_next - time.time()
        if delta > 0:
            if verbose:
                print('sleeping for', delta, file=sys.stderr)
            sys.stderr.flush()
            time.sleep(delta)
    return time.time() + dt


def collect_cli(cmd):
    verbose = cmd.verbose
    dt = cmd.dt  # needs to be longer than 6 timeouts

    con = sqlite.connect(cmd.sqlitedb, verbose=verbose)

    t_next = None

    try:
        while True:
            t_next = sleep_some(t_next, dt, verbose=verbose)
            t_start = time.time()

            data, errors = collect.collect_one(verbose=verbose)
            sqlite.write(con, t_start, 'timing', data, verbose=verbose)
            sqlite.write(con, t_start, 'errors', errors, verbose=verbose)

            if verbose:
                print('committing...', file=sys.stderr)
                sys.stderr.flush()
            con.commit()
    except KeyboardInterrupt:
        print('\n^C seen, gracefully closing database', file=sys.stderr)
        sys.stderr.flush()
        con.close()
        sys.exit(1)
