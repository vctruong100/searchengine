# search_logic.py
#
# This module contains the logic for processing search queries.

import math
from collections import defaultdict
from nltk.stem import PorterStemmer
from lib.reader import DOCID_MAPPING, get_postings, get_url

def process_query(query, num_results):
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
    for rank, (doc_id, score) in enumerate(ranked_docs[:num_results], 1):
        url = get_url(doc_id)
        result = f'{rank}. <a href="{url}" target="_blank">{url}</a> (Score: {score:.2f})'
        results.append(result)
   
    return results
