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


def collect_cli(cmd):
    collect.collect_loop(cmd.sqlitedb, cmd.dt, verbose=cmd.verbose)
