# PostgreSQL Tools

Tools for inspection of various things in PostgreSQL servers.

# Installation

To install this package, first make sure that you have a recent
version of ``setuptools``.

```
pip install --upgrade setuptools
```

After that, you can use ``pip`` to install the package directly from
this directory:

```
pip install .
```

# Running the tools

## Show locking graph using `pg-lock-graph`

The tool `pg-lock-graph` will show a graph of all locks in a database
as a graph with edges between processes and relations. It can be used
to either get a full locking graph of the system (with the exception
of the session that connects to read the locking graph), or limit the
graph to only the nodes involved in a deadlock.

### Restricting graph to deadlock

To print the subgraph(s) involving a deadlock, all edges that
represents locks that are not granted are collected and the induced
subgraph consisting of the vertices attached to those edges are
built. To show just the subgraph of nodes involved in the deadlock,
use the `deadlock` filter.

```bash
pg-lock-graph -f deadlock
```

### Restrict graph to nodes of conflicts

To print the subgraph of nodes involved in a conflict, use the
`conflicts` filter:

```bash
pg-lock-graph -f conflicts
```

This will print all nodes attached to the node having an edge that is
not granted. This can be useful to narrow down the graph to just the
part of the processes and relations involved in the conflict.

### Use non-default socket location

If you have a source install, socket files are placed under `/tmp` so
you can read from this by providing the directory as `--host` value
and have `PGDATA` set correctly.

```
pg-lock-graph --host=/tmp
```
