# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
from nltk.stem import PorterStemmer
from collections import defaultdict
from indexlib.posting import get_postings

USAGE_MSG = "usage: python search.py indexfile"

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

    postings = []
    for word in stemmed_words:
        posting = get_postings(word) # retrieve the posting
        if posting:
            postings.append(posting)
    
    if not postings:
        return [] # no results

    # binary "AND" intersection operation
    # map docID to list of tf-idf scores for intersected docs
    doc_scores = defaultdict(list)
    for posting in postings:
        doc_scores[posting.docid].append(posting.tfidf) # append the tf-idf score

    # Filter out docs that do not appear in all postings
    common_docs = set()
    for doc, scores in doc_scores.items():
        if len(scores) == len(postings):
            common_docs.add(doc)

    # Rank documents based on sum of tf-idf scores
    ranked_docs = sorted(
        common_docs, 
        key=lambda doc: sum(doc_scores[doc]), 
        reverse=True
    )

    # Rank documents based on sum of tf-idf scores
    for doc in ranked_docs:
        result.append((doc, sum(doc_scores[doc])))

    return result

def run_server(path):
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    print("path:", path)

    while True:
        query = input()
        # do query work
        print("received:", query)
        if not query:
            continue
        results = process_query(query)
        for doc, score in results:
            print(f"Doc ID: {doc}, Score: {score}")


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    run_server(path)

