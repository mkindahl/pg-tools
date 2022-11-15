import psycopg2
import argparse
import os
import graphviz
import textwrap
import igraph

from psycopg2 import Error
from psycopg2.extras import RealDictCursor

def display(elems):
    es = list(elems)
    return ", ".join(es[:-2] + [", and ".join(es[-2:])])

EPILOG = f"""
Available formats are: {display(graphviz.FORMATS)}
"""


def parse_arguments():
    parser = argparse.ArgumentParser(description='Get lock graph from PostgreSQL instance',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
    parser.add_argument('-f', '--filter', metavar='FILTER', choices=['deadlock'],
                        nargs='+', default=[],
                        help='Apply filter to graph')
    parser.add_argument('-h', '--host', metavar='HOSTNAME',
                        help='database server host or socket directory')
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help='show this help message and exit')
    parser.add_argument('--format', metavar='FORMAT', default='png',
                        choices=graphviz.FORMATS,
                        help="format for emitted graph")
    return parser.parse_args()

# Select all locks that are available in the current database which
# are not related to the connecting session.
#
# The connecting session just execute this statement so those locks
# are uninteresting, and locks in other databases will not show
# properly so that is not useful either.
SELECT_ALL_LOCKS = """
SELECT pid, relation, relation::regclass, mode, granted, query
  FROM pg_locks JOIN pg_stat_activity USING (pid)
 WHERE locktype = 'relation'
   AND pid != pg_backend_pid()
   AND database = (SELECT oid FROM pg_database WHERE datname = current_database())
"""

def build_lock_graph(conn, args):
    """Build a full lock graph."""

    cursor = conn.cursor()
    cursor.execute("SELECT current_database()")
    print("Connected to database", cursor.fetchall())

    cursor.execute(SELECT_ALL_LOCKS)
    if cursor.rowcount == 0:
        raise "No locks to display"

    full = igraph.Graph(directed=True)
    for pid, reloid, relation, mode, granted, query in cursor:
        procname = f'PID{pid}'
        relname = f'REL{reloid}'
        full.add_vertex(procname, label=f'PID {pid}\\n{query}', kind='process', pid=pid, query=query)
        full.add_vertex(relname, label=relation, kind='relation', reloid=reloid, relation=relation)
        full.add_edge(procname, relname, granted=granted, mode=mode)
    return full

def render_graph(full, args):
    "Render a locking graph using Graphviz."
    dot = graphviz.Digraph(f'{args.dbname}_lock_graph', format=args.format)

    for v in full.vs:
        if v['kind'] == 'process':
            dot.node(v['name'], f'PID {v["pid"]}\\n{v["query"]}', shape='box', peripheries='2')
        elif v['kind'] == 'relation':
            dot.node(v['name'], v['relation'], shape='box')
    for e in full.es:
        dot.edge(full.vs[e.source]["name"], full.vs[e.target]["name"], label=e["mode"], style=('solid' if e['granted'] else 'dashed'))

    return dot.render()

if __name__ == '__main__':
    args = parse_arguments()
    conn = psycopg2.connect(dbname=args.dbname, user=args.user,
                            host=('/tmp' if args.host is None else args.host))

    # Build a full locking graph using the data in the lock tables
    lgraph = build_lock_graph(conn, args)

    # To show only nodes involved in a deadlock, we take all edges
    # that are not granted and generate a subgraph using the vertices
    # that are connected to those edges.
    if 'deadlock' in args.filter:
        edges = lgraph.es.select(granted_eq=False)
        vertices = {v for e in edges for v in [e.source, e.target]}
        render = lgraph.induced_subgraph(vertices)
    else:
        render = lgraph
    
    # Render the graph
    print(render_graph(render, args))
