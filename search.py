# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
from nltk.stem import PorterStemmer
from collections import defaultdict


USAGE_MSG = "usage: python search.py indexfile"

def load_index(indexfile):
    """Loads the index file and returns the index object.
    """
    pass

def search_query(query, index):
    """Searches the query in the index and returns the results.
    """
    pass

def run_server(indexfile):
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    print("file:", indexfile)
    # load the index file
    index = load_index(indexfile)

    while True:
        query = input()
        # do query work
        print("received:", query)
        if not query:
            continue

        results = search_query(query, index)
        for result in results:
            print(result)


if __name__ == "__main__":
    try:
        indexfile = sys.argv[1]
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    run_server(indexfile)

