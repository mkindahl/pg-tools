"""Set up PostgreSQL Tools.

Some of the code used here are based on the setup script for the tool
pip (https://github.com/pypa/pip/blob/main/setup.py).

"""

import os

from setuptools import setup, find_packages

def read(rel_path: str) -> str:
    """Read a file and return its contents."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), encoding="ascii") as inputfile:
        return inputfile.read()

def get_version(rel_path: str) -> str:
    """Read the version from the given file.

    Format for the version looks like this::

        __version__ = "0.9"
    """
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setup(
    name = "pg-tools",
    version = get_version("src/pgtools/__init__.py"),
    author = "Mats Kindahl",
    author_email = "mats@kindahl.net",
    description ="Tools for working with PostgreSQL servers",
    license = "Apache 2",
    keywords = "postgresql",
    project_urls={
        "Documentation": "https://pip.pypa.io",
        "Source": "https://github.com/mkindahl/pg-tools",
        "Changelog": "https://pip.pypa.io/en/stable/news/",
    },
    package_dir={"": "src"},
    packages=find_packages(where='src', exclude=['tests']),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache 2 License",
        "Topic :: Database :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    install_requires=[
          'psycopg2', 'graphviz', 'igraph',
    ],
    entry_points={
        "console_scripts": [
            "pg-lock-graph=pgtools.cli.lock_graph:main",
        ],
    },
    python_requires=">=3.7",
)
