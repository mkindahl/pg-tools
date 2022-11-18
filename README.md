# PostgreSQL Tools

Tools for inspection of various things in PostgreSQL servers.

# Installation

To install this package, first make sure that you have a recent
version of ``setuptools``

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
as a graph with edges between processes and relations.



