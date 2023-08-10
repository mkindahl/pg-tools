"""Module for the pg-lock-graph tool."""

import os
import argparse

import graphviz
import psycopg2

from .. import __version__
from ..locks import LockGraph, FILTERS

def display(elems):
    """Display a list of elements using Oxford comma."""
    elements = list(elems)
    return ", ".join(elements[:-2] + [", and ".join(elements[-2:])])

EPILOG = f"""
Available formats are: {display(graphviz.FORMATS)}
"""

def parse_arguments(description):
    """Parse arguments to tool."""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     add_help=False, epilog=EPILOG)
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument('-U', '--username', dest='user',
                        default=(os.getenv("PGUSER") or os.getlogin()),
                        help='user name to connect as')
    parser.add_argument('--password', dest='password',
                        help='optional password of the user to connect as')
    parser.add_argument('-d', '--dbname', metavar='DBNAME', dest='dbname',
                        default=(os.getenv("PGDATABASE") or os.getlogin()),
                        help='name of the database to read locking information from')
    parser.add_argument('-p', '--port', metavar='PORT',
                        help='database server port number')
    parser.add_argument('-f', '--filter', metavar='FILTER', choices=FILTERS,
                        nargs='+', dest='filters', default=[],
                        help='Apply filter to graph')
    parser.add_argument('-h', '--host', metavar='HOSTNAME',
                        help='database server host or socket directory')
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help='show this help message and exit')
    parser.add_argument('--format', metavar='FORMAT', default='png',
                        choices=graphviz.FORMATS,
                        help="format for emitted graph")
    return parser.parse_args()

def main():
    """Get lock graph from PostgreSQL instance."""
    args = parse_arguments(main.__doc__)
    conn = psycopg2.connect(dbname=args.dbname, user=args.user,
                            password=(None if args.password is None else args.password),
                            host=args.host)
    lgraph = LockGraph()
    lgraph.build(conn)
    lgraph.apply_filters(args.filters)
    print(lgraph.render(args.format))
