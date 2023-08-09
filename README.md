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

To print the subgraph(s) involving a deadlock, all edges that represents
locks that are not granted are collected and the induced subgraph
consisting of the vertices attached to those edges are built.

If you have a source install, socket files are placed under `/tmp` so
you can read from this by providing the directory as `--host` value
and have `PGDATA` set correctly.

```
mk-lock-graph --host=/tmp
```
