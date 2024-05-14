# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
from nltk.stem import PorterStemmer
from collections import defaultdict


USAGE_MSG = "usage: python search.py indexfile"

def run_server(path):
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    print("path:", path)

    # load the index file
    index_reader = load_index(path) # some code here to read index

    while True:
        query = input()
        # do query work
        print("received:", query)
        if not query:
            continue

        results = index_reader.search(query)
        for result in results:
            print(result)


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    run_server(path)

