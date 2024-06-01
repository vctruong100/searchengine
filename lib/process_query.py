# search_logic.py
#
# This module contains the logic for processing search queries.

import math
from collections import defaultdict
from nltk.stem import PorterStemmer
from lib.reader import get_num_documents, get_postings, get_document

def calculate_net_relevance_score(doc, text_relevance):
    """Calculate the Net Relevance Score for a single document using provided 
    scores and weights.
    
    :param doc Document: The document
    :param text_relevance float: The textual relevance score
    :return: The net relevance score
    :rtype: float
    """

    # Weights (these can be adjusted based on system performance and goals)
    # controls their impact on the overall relevance calculation, 
    # ensures a balanced and customizable search result based on specific goals.
    w_pr = 0.25  # Weight for PageRank
    w_hub = 0.25  # Weight for HITS Hub score
    w_auth = 0.25  # Weight for HITS Authority score
    w_tr = 0.25  # Weight for Textual Relevance

    # Normalize scores
    normalized_pr = doc.page_rank / max_scores['page_rank'] if max_scores['page_rank'] > 0 else 0
    normalized_hub = doc.hub_score / max_scores['hub_score'] if max_scores['hub_score'] > 0 else 0
    normalized_auth = doc.auth_score / max_scores['auth_score'] if max_scores['auth_score'] > 0 else 0

    # Calculate NRS with normalized score (with weights)
    quality = (w_pr * normalized_pr +
               w_hub * normalized_hub +
               w_auth * normalized_auth +
               w_tr * text_relevance)

    # Calculate NRS without normalizing score (with weights)
    # quality = (w_pr * doc.page_rank +
    #            w_hub * doc.hub_score +
    #            w_auth * doc.auth_score +
    #            w_tr * text_relevance)

    # Calculate NRS without weights or normalization
    # quality = doc.page_rank + doc.hub_score + doc.auth_score + text_relevance
    
    return quality

def stem_query(query):
    stemmer = PorterStemmer()
    return [stemmer.stem(word) for word in query.split()]

def get_postings_for_query(stemmed_words):
    """Retrieve postings for the stemmed words in the query.

    :param stemmed_words list: The stemmed words in the query
    :return: The postings and document sets
    :rtype: tuple
    """

    postings = {}
    doc_sets = []
    for word in stemmed_words:
        posting_list = get_postings(word)
        if posting_list:
            postings[word] = posting_list
            # Create a set of documents that contain the term
            doc_sets.append(set(posting.docid for posting in posting_list))
    return postings, doc_sets

def calculate_document_scores(postings, common_docs, doc_count):
    """Calculate the document scores based on the query.
    
    :param postings dict: The postings for the query terms
    :param common_docs set: The set of documents that contain all query terms
    :param doc_count int: The total number of documents
    :return: The document vectors, query vector, and query length
    :rtype: tuple
    """

    # map dictionary of docID to score
    doc_vectors = defaultdict(lambda: defaultdict(float))
    query_vector = defaultdict(float)
    query_length = 0.0

    # map dictionary of docID to score
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
    return doc_vectors, query_vector, query_length

def compute_cosine_similarity(doc_vectors, query_vector, query_length, max_scores):
    """ Compute the cosine similarity between the query and documents.

    :param doc_vectors dict: The document vectors
    :param query_vector dict: The query vector
    :param query_length float: The length of the query vector
    :param max_scores dict: The maximum scores for normalization
    :return: The document scores
    :rtype: dict
    """

    # Normalize document vectors and compute cosine similarity
    doc_scores = defaultdict(float)
    for doc_id, term_weights in doc_vectors.items():

        # Calculate the Euclidean norm (length) of the document vector
        doc_length = 0.0
        for weight in term_weights.values():
            doc_length += weight ** 2
        doc_length = math.sqrt(doc_length)
            
        # Calculate the dot product of the query and document vectors
        cosine_similarity = 0.0
        for word, weight in term_weights.items():
            normalized_doc_weight = weight / doc_length
            normalized_query_weight = query_vector[word] / query_length
            cosine_similarity += normalized_doc_weight * normalized_query_weight

        doc = get_document(doc_id)
        quality = calculate_net_relevance_score(doc, cosine_similarity, max_scores)
        doc_scores[doc_id] = quality

    return doc_scores

def process_query(query, num_results):
    """Processes the query and returns the results.

    :param query str: The query 
    :param num_results int: The number of results to return
    :return: The results
    :rtype: list
    """
    result = []
    stemmed_words = stem_query(query)
    doc_count = get_num_documents()

    postings, doc_sets = get_postings_for_query(stemmed_words)

    if not doc_sets:
        return []

    # Find the intersection of documents that contain all terms
    common_docs = set.intersection(*doc_sets)

    max_scores = {
        'page_rank': max((get_document(doc_id).page_rank for doc_id in common_docs), default=0),
        'hub_score': max((get_document(doc_id).hub_score for doc_id in common you_docs), default=0),
        'auth_score': max((get_document(doc_id).auth_score for doc_id in common_docs), default=0)
    }

    doc_vectors, query_vector, query_length = calculate_document_scores(postings, common_docs, doc_count)

    if query_length == 0:
        return ["Query too common or not indexed."]
        
    # Calculate the Euclidean norm (length) of the query vector
    # Euclidean norm = the square root of the sum of the squares of the weights
    query_length = math.sqrt(query_length)

    doc_scores = compute_cosine_similarity(doc_vectors, query_vector, query_length, common_docs, max_scores)

    return format_results(doc_scores, num_results)

def format_results(doc_scores, num_results):
    """ Sort the document scores and format the results.

    :param doc_scores dict: The document scores
    :param num_results int: The number of results to return
    :return: The formatted results
    :rtype: list
    """
   # Rank documents based on sum of tf-idf scores
    ranked_docs = sorted(
        doc_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # Format output to include rankings, URLs, and scores
    results = []
    for rank, (doc_id, score) in enumerate(ranked_docs[:num_results], 1):
        document = get_document(doc_id)
        url = document.url if document else "URL not found"
        result = f'{rank}. <a href="{url}" target="_blank">{url}</a> (Score: {score:.2f})'
        results.append(result)

    return results