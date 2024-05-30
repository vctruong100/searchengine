# makeindex.py
#
# constructs an index file
# from a collection of web pages
#
# usage: python makeindex.py pages/ outputfile

import os
import sys
import time
from bs4 import BeautifulSoup
from collections import defaultdict # simplify and speed up Posting insertion
from json import load
from nltk.stem import PorterStemmer
from lib.tokenize import tokenize
from lib.posting import Posting
from lib.word_count import word_count
from lib.writer import write_partial_index, merge_index
from print_result import print_result

USAGE_MSG = "usage: python makeindex.py pages/ outputfile"

def main(dir):
    """Makes the index from a collection of
    cached pages recursively from the directory (dir).
    Writes the output to the file handler (fh).

    :param dir str: The directory

    """

    output_path = "index/merged_index"
    if not os.path.exists("index"):
        os.mkdir("index")
    fh = open(output_path, "w+b")
    part_filename = f"{fh.name}.part"

    if os.path.exists(part_filename):
        print(f"Partial index file '{part_filename}' already exists. Skipping indexing.")
        part_fh = open(part_filename, 'w+b')
    else:
        start_time = time.time()
        inverted_index = defaultdict(list)
        docID = 0
        stemmer = PorterStemmer()
        doc_limit = 100  # cutoff point for partial index writing

        part_fh = open(part_filename, 'w+b')
        
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

                        soup = BeautifulSoup(content, 'lxml')

                        text = soup.get_text()
                        tokens = tokenize(text)

                        # Stem the tokens using the Porter Stemmer
                        # https://www.geeksforgeeks.org/python-stemming-words-with-nltk/
                        stemmed_tokens = [stemmer.stem(token) for token in tokens]
                        token_counts = word_count(stemmed_tokens)

                        total_tokens = len(tokens)

                        # Iterate over each token and its count and add a Posting to the inverted index
                        for token, count in token_counts.items():
                            # tf = term frequency of each individual token
                            posting = Posting(docid=docID, tf=count, total_tokens=total_tokens) 
                            inverted_index[token].append(posting)

                    # Periodically write the partial index to disk
                    if docID % doc_limit == 0: # write for every 100 documents
                        write_partial_index(inverted_index, docID, part_fh)
                        print(f"Document ID: {docID}", flush=True)

        # Final write for any remaining documents
        if inverted_index:
            write_partial_index(inverted_index, docID, part_fh)

        end_time = time.time()  # Capture the end time of the indexing process
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        print(f"Elapsed time of indexing: {elapsed_time:.2f} seconds")

    # Merge the partial index files
    start_time = time.time()  # Capture the start time of the merging process
    part_fh.seek(0)  # Move the file pointer to the beginning of the file
    
    print("Merging partial index files...")
    try: 
        merge_index(part_fh, fh)
    except Exception as e:
        print(f"An error occurred during merging: {e}")
        sys.exit(1)
    
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Elapsed time of merging: {elapsed_time:.2f} seconds")

    part_fh.close()
    fh.close()
    os.remove(part_filename)  # Delete the temporary partial index file
    os.remove(output_path)

if __name__ == "__main__":
    try:
        dir = sys.argv[1]
        assert os.path.isdir(dir), USAGE_MSG
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    main(dir)

