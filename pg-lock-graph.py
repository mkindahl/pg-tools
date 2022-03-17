import psycopg2
import argparse
import os
import graphviz
import textwrap

from psycopg2 import Error
from psycopg2.extras import RealDictCursor

def display(elems):
    es = list(elems)
    return ", ".join(es[:-2] + [", and ".join(es[-2:])])

EPILOG = f"""
Available formats are: {display(graphviz.FORMATS)}

The include option allow you to focus the graph on just some specific
relations or processes. The option accept a list of inclusion
designators and can be given multiple times. The graph produced will
contain all processes and relations that are connected with any of the
processes or relations given in the list. It defaults to display all
processes and relations.

The accepted formats for the designators are:

pid:<pid>
   Focus on process with PID <pid>

pid:/<regexp>/
   Focus on process with a query that matches <regexp>.

rel:<oid>
   Focus on the relation with OID <oid>

rel:<name>
   Focus on the relation with name <name>

"""


def parse_arguments():
    parser = argparse.ArgumentParser(description='Get lock graph from PostgreSQL instance',
                                     add_help=False, epilog=EPILOG)
    parser.add_argument('-U', '--username', dest='user',
                        default=(os.getenv("PGUSER") or os.getlogin()),
                        help='user name to connect as')
    parser.add_argument('-d', '--dbname', metavar='DBNAME', dest='dbname',
                        help='name of the database to read locking information from')
    parser.add_argument('dbname', metavar='DBNAME', nargs='?',
                        default=(os.getenv("PGDATABASE") or os.getlogin()),
                        help='name of the database to read locking information from')
    parser.add_argument('-p', '--port', metavar='PORT',
                        help='database server port number')
    parser.add_argument('-h', '--host', metavar='HOSTNAME',
                        help='database server host or socket directory')
    parser.add_argument('-i', '--include', metavar='INCLUSION',
                        action='append',
                        help='include relations or processes in graph')
    parser.add_argument('-x', '--exclude', metavar='EXCLUSION',
                        action='append',
                        help='exclude relations or processes in graph')
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help='show this help message and exit')
    parser.add_argument('--format', metavar='FORMAT', default='png',
                        choices=graphviz.FORMATS,
                        help="format for emitted graph (default is 'png')")
    return parser.parse_args()

SELECT_ALL_LOCKS = """
SELECT pid, relation, relation::regclass, mode, granted, query
  FROM pg_locks JOIN pg_stat_activity USING (pid)
 WHERE locktype = 'relation';
"""

def build_lock_graph(conn):
    """Build lock graph.

    Build lock graph from a connector and a set of filters.
    """
    cursor = conn.cursor()
    cursor.execute(SELECT_ALL_LOCKS)
    if cursor.rowcount == 0:
        raise "No locks to display"
    
    dot = graphviz.Digraph(f'{args.dbname}_lock_graph', format=args.format)
    for pid, reloid, relation, mode, granted, query in cursor:
        # Here we want to filter out any nodes that are not related to
        # a specific relation or process. This means building a graph
        # of all the nodes, and then use the connectivity to filter
        # out nodes.
        procname = f'PID{pid}'
        relname = f'REL{reloid}' 
        dot.node(procname, f'PID {pid}\\n{query}', shape='box', peripheries='2')
        dot.node(relname, relation, shape='box')
        dot.edge(procname, relname, label=mode, style=('solid' if granted else 'dashed'))

    return dot.render()

if __name__ == '__main__':
    args = parse_arguments()
    
    kwrds = {'dbname': args.dbname, 'user': args.user }
    kwrds['host'] = '/tmp' if args.host is None else args.host
    conn = psycopg2.connect(**kwrds)

    print(build_lock_graph(conn))
