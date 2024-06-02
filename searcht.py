# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
import math
import time
import numpy as np
from nltk.stem import PorterStemmer
from collections import defaultdict
from lib.reader import get_num_nonempty_documents, get_postings, initialize, get_document
from lib.stopwords import is_stopword
from lib.indexfiles import *
from lib.tokenize import *
import lib.queryproc as queryproc

def run_server():
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    while True:
        query = input("Enter query:")
        # do query work
        if not query:
            continue

        start_time = time.time_ns()  # Start timing using time_ns() for higher precision
        result = queryproc.process_query(query)
        end_time = time.time_ns()  # End timing

        for result in queryproc.format_results_tty(result, 5):
            print(result)

        query_time = (end_time - start_time) / 1_000_000  # Convert nanoseconds to milliseconds
        print(f"Query time: {query_time:.2f} milliseconds")

USAGE_MSG = "usage: python searcht.py"

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    initialize(
        docinfo_filename=DOCINFO_NAME,
        mergeinfo_filename=MERGEINFO_NAME,
        buckets_dir=BUCKETS_DIR
    )

    run_server()
