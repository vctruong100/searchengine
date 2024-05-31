Search engine
=============

A search engine in Python.

To install dependencies, use ``python -m pip install -r requirements.txt`` or 
``pip install -r requirements.txt``. You might need to add the ``--user`` flag if 
you do not have the permissions.

To build the index, use ``python makeindex.py path/to/pages/``.
Optionally, if you want to keep the partial index, you can pass in an optional
argument "--keep-partial" or "-p" before the path to pages argument.

To run the search engine that processes user queries locally, use
``python search.py``.

