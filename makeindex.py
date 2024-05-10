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
from json import load
from index.posting import Posting
from index.word_count import word_count
from index.mapb_write import write_index
from collections import defaultdict #  to simplify and speed up the insertion of postings
import time

USAGE_MSG = "usage: python makeindex.py pages/ outputfile"

def main(dir, fh):
    """Makes the index from a collection of
    cached pages recursively from the directory (dir).
    Writes the output to the file handler (fh).

    :param dir str: The directory
    :param fh: The output file handler

    """
    start_time = time.time()

    inverted_index = defaultdict(list)
    docID = 0

    # recursively walk through the directory
    for root, _, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                docID += 1
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:

                    # load the json file
                    js = load(f)
                    content = js.get('content', '')

                    # if the content is empty, skip
                    if not content.strip():
                        continue

                    soup = BeautifulSoup(content, 'html.parser')

                    text = soup.get_text()
                    tokens = tokenize(text)
                    token_counts = word_count(tokens)

                    # Iterate over each token and its count and add a Posting to the inverted index
                    for token, count in token_counts.items():
                        posting = Posting(docid=docID, score=count)
                        inverted_index[token].append(posting)

    num_unique_words = len(inverted_index)
    print(f"Number of documents: {docID}")
    print(f"Number of unique words: {num_unique_words}")

    write_index(inverted_index, docID, fh)

    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

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

    file_size = os.path.getsize(sys.argv[2]) / 1024
    print(f"Total size of the index on disk: {file_size:.2f} KB")

