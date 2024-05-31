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
from lib.reader import get_num_documents, get_postings, initialize, get_document
from lib.indexfiles import *

def process_query(query):
    """Processes the query and returns the results.

    :param query str: The query
    :param num_results int: The number of results to return
    :return: The results
    :rtype: list
    """
    result = []
    stemmer = PorterStemmer()
    query = query.split()
    stemmed_words = [stemmer.stem(word) for word in query]
    doc_count = get_num_documents()

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
    doc_vectors = defaultdict(lambda: defaultdict(float))
    query_vector = defaultdict(float)
    query_length = 0.0

    # map dictionary of docID to score
    doc_scores = defaultdict(float)
    for word, posting_list in postings.items():
        # Calculate IDF (Inverse Document Frequency)
        doc_freq = len(posting_list)
        idf = math.log2((doc_count + 1) / (doc_freq + 1))

        # Calculate TF for query using Inc.Itc
        query_tf = query.count(word)
        query_tf = 1 + math.log(query_tf) if query_tf > 0 else 0
        query_weight = query_tf * idf
        query_vector[word] = query_weight
        query_length += query_weight ** 2

        for posting in posting_list:
            # Skip documents that do not contain all terms
            if posting.docid not in common_docs:
                continue
            else:
                # Calculate logarithmic TF for document
                doc_tf = 1 + math.log(posting.tf) if posting.tf > 0 else 0
                doc_weight = doc_tf
                doc_vectors[posting.docid][word] = doc_weight

    if query_length == 0:
        return ["Query too common or not indexed."]

    # Calculate the Euclidean norm (length) of the query vector
    # Euclidean norm = the square root of the sum of the squares of the weights
    query_length = math.sqrt(query_length)

    # Normalize document vectors and compute cosine similarity
    doc_scores = defaultdict(float)
    for doc_id, term_weights in doc_vectors.items():

        # Calculate the Euclidean norm (length) of the document vector
        doc_length = 0.0
        for weight in term_weights.values():
            doc_length += weight ** 2
        doc_length = math.sqrt(doc_length)

        # Calculate the dot product of the query and document vectors
        for word, weight in term_weights.items():
            normalized_doc_weight = weight / doc_length
            normalized_query_weight = query_vector[word] / query_length

            # Compute cosine similarity
            doc_scores[doc_id] += normalized_doc_weight * normalized_query_weight

    # Rank documents based on sum of tf-idf scores
    ranked_docs = sorted(
        doc_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # Format output to include rankings, URLs, and scores
    results = []
    for rank, (doc_id, score) in enumerate(ranked_docs[:5], 1):  # Limit results to top 10
        document = get_document(doc_id)
        url = document.url if document else "URL not found"
        result = f'{rank}. <a href="{url}" target="_blank">{url}</a> (Score: {score:.2f})'
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
        start_time = time.time_ns()  # Start timing using time_ns() for higher precision
        results = process_query(query)
        for result in results:
            print(result)

        end_time = time.time_ns()  # End timing
        query_time = (end_time - start_time) / 1_000_000  # Convert nanoseconds to milliseconds
        print(f"Query time: {query_time:.2f} milliseconds")

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
