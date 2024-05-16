# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
import math
from nltk.stem import PorterStemmer
from collections import defaultdict
from indexlib.reader import DOCID_MAPPING, get_postings

USAGE_MSG = "usage: python search.py"

def process_query(query):
    """Processes the query and returns the results.

    :param query str: The query
    :return: The results as a list of tuples (docID, score)
    :rtype: list[tuple[int, float]]
    """
    result = []
    stemmer = PorterStemmer()
    query = query.split()
    stemmed_words = [stemmer.stem(word) for word in query]
    
    doc_count = len(DOCID_MAPPING)
    postings = []
    for word in stemmed_words:
        posting = get_postings(word) # retrieve the posting
        if posting:
            postings.append(posting) 

    # binary "AND" intersection operation
    # map docID to list of tf-idf scores for intersected docs
    doc_scores = defaultdict(list)

    for word, posting_list in postings.items():
        # Calculate IDF
        doc_freq = len(posting_list)
        idf = math.log2((doc_count + 1) / (doc_freq + 1))
        
        for posting in posting_list:
            # Calculate TF-IDF
            tf_idf = idf * posting.tfidf
            doc_scores[posting.docid] += tf_idf

    # Rank documents based on sum of tf-idf scores
    ranked_docs = sorted(
        doc_scores.items(), 
        key=lambda item: item[1], 
        reverse=True
    )

    return ranked_docs

def run_server():
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    while True:
        query = input("Enter query:")
        # do query work
        print("Received:", query)
        if not query:
            continue
        results = process_query(query)
        for doc, score in results:
            print(f"Doc ID: {doc}, Score: {score:.3f}")
        else:
            print("No results found.")


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    run_server()

