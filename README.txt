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
Post-indexing, you have the option to compute the PageRank and HITS scores to assess
the relevance of each document. Execute:
``python compute.py``

This script updates each document's pr_quality, hub_quality, and auth_quality based
on their link structures and content relevance. If you choose not to run compute.py,
the system will rank search results based on textual relevancy or cosine
similarity by default.


Running the Search Engine
-------------------------
To start the search engine with Web GUI and begin processing local user queries, use:
``python search.py``

You can run queries by typing into the box and clicking the "Search" button.

Note: Using the Web GUI will slightly decrease the query speed.

To not use the Web GUI, execute:
``python searcht.py``

This command launches a local server that allows real-time searching of the indexed documents.
The server calculates net relevance scores for each query, using the previously
computed PageRank and HITS scores along with textual relevance derived from the query.

You will be prompted to enter your query to search. This runs indefinitely until you interrupt
the program using CTRL+C (keyboard interrupt).

Summarizer
----------
The `summarizer.py` script processes HTML content from JSON files to generate summaries
using the BART model.
**Warning:** The processor will take a tremendous amount of time to summarize ALL documents
(approximately 20-40 hours). Run at your own risk. Summaries will NOT affect the query time.
You can stop the script at any time with CTRL+C (keyboard interrupt), but the summary 
file will be incomplete.
Model: https://huggingface.co/facebook/bart-large-cnn

To run the summarizer, execute:
python summarizer.py path/to/pages

This script extracts text from HTML, summarizes it, and writes the results directly to a
file. It's designed to operate efficiently with considerable runtime per document. Then,
when running the search engine (with Web GUI -- ``search.py``), the engine will
provide a summary for each of the result. If chosen not to run the summarizer, the search
engine (search.py) will provide no summary.

