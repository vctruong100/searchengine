# makeindex.py
#
# constructs an index file
# from a collection of web pages
#
# usage: python makeindex.py pages/ outputfile

import os
import sys
from bs4 import BeautifulSoup
from index.tokenize import tokenize
from json import *
from index.posting import Posting

USAGE_MSG = "usage: python makeindex.py pages/ outputfile"


def main(dir, fh):
    """Makes the index from a collection of
    cached pages recursively from the directory (dir).
    Writes the output to the file handler (fh).

    :param dir str: The directory
    :param fh: The output file handler

    """
    inverted_index = {}
    docID = 0

    # Walk through the directory and parse json files
    for root, _, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                docID += 1
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    js = load(f)
                    content = js['content']
                    soup = BeautifulSoup(content, 'lxml')
                    text = soup.get_text()
                    tokens = tokenize(text)

    # Write the inverted index to the file handler
    for token, doc_freq in inverted_index.items():
        fh.write(f"{token}: {doc_freq}\n")

if __name__ == "__main__":
    try:
        dir = sys.argv[1]
        assert os.path.isdir(dir), USAGE_MSG
        fh = open(sys.argv[2], "wb")
    except:
        print(USAGE_MSG)
        sys.exit(1)

    main(dir, fh)
    fh.close()

