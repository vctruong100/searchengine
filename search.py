# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
import math
import time
from nltk.stem import PorterStemmer
from collections import defaultdict
from indexlib.reader import DOCID_MAPPING, get_postings, get_url

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
    
    postings = {}
    doc_sets = []
    for word in stemmed_words:
        posting_list = get_postings(word)  # retrieve the posting
        if posting_list:
            postings[word] = posting_list

            # Create a set of documents that contain the term 
            doc_sets.append(set(posting.docid for posting in posting_list))

    if not doc_sets:
        return []

    # Find the intersection of documents that contain all terms
    common_docs = set.intersection(*doc_sets)

    # map dictionary of docID to score
    doc_scores = defaultdict(float)  
    for word, posting_list in postings.items():
        # Calculate IDF (Inverse Document Frequency)
        doc_freq = len(posting_list)
        idf = math.log2((doc_count + 1) / (doc_freq + 1)) 
        
        for posting in posting_list:
            # Skip documents that do not contain all terms
            if posting.docid not in common_docs:
                continue
            else:
                # Calculate TF-IDF
                # TF = term frequency of the token / total tokens in the document
                if posting.total_tokens == 0:
                    tf = 0
                else:
                    tf = posting.tf / posting.total_tokens
                tf_idf = idf * tf
                doc_scores[posting.docid] += tf_idf

    # Rank documents based on sum of tf-idf scores
    ranked_docs = sorted(
        doc_scores.items(), 
        key=lambda item: item[1], 
        reverse=True
    )

    # Format output to include rankings, URLs, and scores
    results = []
    for rank, (doc_id, score) in enumerate(ranked_docs[:5], 1):  # Limit results to top 10
        url = get_url(doc_id)
        result = f"{rank}. {url} (Score: {score:.2f})"
        results.append(result)
   
    return results

def run_server():
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    while True:
        query = input("Enter query:")
        # do query work
        if not query:
            continue
        start_time = time.time()
        results = process_query(query)
        for result in results:
            print(result)
        
        end_time = time.time()
        query_time = end_time - start_time
        print(f"Query time: {query_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    run_server()

