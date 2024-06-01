Search engine
=============

A Python-based search engine designed to index web pages, compute PageRank and HITS scores, and process user queries.

Dependencies
------------
To install dependencies, run the following command:
``python -m pip install -r requirements.txt``
or 
``pip install -r requirements.txt``

You might need to add the ``--user`` flag if you do not have the permissions.

Building the Index
------------------
To construct an index from a collection of web pages, execute:
``python makeindex.py path/to/pages/``
For example: 
``python makeindex.py ./DEV``

Optionally, if you want to keep the partial index, you can pass in an optional
argument "--keep-partial" or "-p" before the path to pages argument.
``python makeindex.py --keep-partial path/to/pages/``


Computing PageRank and HITS Scores
----------------------------------
Once the index is built, compute the PageRank and HITS scores to evaluate the relevance of each document. Run:
``python compute.py``

This script will update each document's `pr_quality`, `hub_quality`, and `auth_quality` attributes, 
based on their link structure and content.

Running the Search Engine
-------------------------
To start the search engine and begin processing local user queries, use:
``python search.py``

This command launches a local server that allows real-time searching of the indexed documents. 
The server calculates net relevance scores for each query, using the previously computed PageRank and HITS 
scores along with textual relevance derived from the query.
