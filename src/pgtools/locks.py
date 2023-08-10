"""Locking graph support."""

import graphviz
import igraph

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

def deadlock_filter(graph):
    """Get subgraph consisting of nodes involved in a deadlock.

    To filter out vertices involved in a deadlock, it sufficies to
    collect all vertexes attached to a edge that is not granted and
    generate the induced subgraph.
    """
    edges = graph.es.select(granted_eq=False)
    vertices = {v for e in edges for v in [e.source, e.target]}
    return graph.induced_subgraph(vertices)


def conflicts_filter(graph):
    """Get subgraph of nodes connected to a conflict.

    Find all vertices that have an incoming edge that is not
    granted. Collect the neighbourhood of the vertices, and get the
    induced subgraph from those vertices.
    """
    edges = graph.es.select(granted_eq=False)
    vertices = [e.target for e in edges]
    neighborhood = sum(graph.neighborhood(vertices), [])
    return graph.induced_subgraph(neighborhood)

FILTERS = {
    'deadlock': deadlock_filter,
    'conflicts': conflicts_filter,
}

class LockGraph:
    """Locking graph for PostgreSQL.

    This will fetch locking information from a server and build a
    locking graph from that.
    """

    def __init__(self):
        """Init function."""
        self.__graph = igraph.Graph(directed=True)
        self.__dbname = None

    def build(self, conn):
        """Build a full lock graph."""
        cursor = conn.cursor()
        cursor.execute("SELECT current_database()")
        (self.__dbname,) = cursor.fetchone()
        print(self.__dbname)

        cursor.execute(SELECT_ALL_LOCKS)
        for pid, reloid, rlabel, mode, granted, query in cursor:
            procnode = f'PID{pid}'
            relnode = f'REL{reloid}'
            plabel = f'PID {pid}\\n{query}'
            self.__graph.add_vertex(procnode, label=plabel, kind='process',
                                    pid=pid, query=query)
            self.__graph.add_vertex(relnode, label=rlabel, kind='relation',
                                    reloid=reloid, relation=rlabel)
            self.__graph.add_edge(procnode, relnode,
                                  granted=granted, mode=mode)
        conn.commit()

    def apply_filters(self, filters):
        """Apply filters to locking graph.

        deadlock: Create subgraph consisting of nodes involved in a
          deadlock.

        """
        graph = self.__graph
        for flt in filters:
            graph = FILTERS[flt](graph)
        self.__graph = graph

    def render(self, fmt):
        """Render a locking graph using Graphviz."""
        dot = graphviz.Digraph(f'{self.__dbname}_lock_graph', format=fmt)

        vertices = self.__graph.vs    # Vertices

        for vert in vertices:
            if vert['kind'] == 'process':
                dot.node(vert['name'],
                         f'PID {vert["pid"]}\\n{vert["query"]}',
                         shape='box', peripheries='2')
            elif vert['kind'] == 'relation':
                dot.node(vert['name'], vert['relation'], shape='box')

        for edge in self.__graph.es:
            dot.edge(vertices[edge.source]["name"],
                     vertices[edge.target]["name"],
                     label=edge["mode"],
                     style=('solid' if edge['granted'] else 'dashed'))
        return dot.render()
