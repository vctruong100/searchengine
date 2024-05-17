# search_logic.py
#
# This module contains the logic for processing search queries.

import math
from collections import defaultdict
from nltk.stem import PorterStemmer
from indexlib.reader import DOCID_MAPPING, get_postings, get_url

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
    for rank, (doc_id, score) in enumerate(ranked_docs[:num_results], 1):
        url = get_url(doc_id)
        result = f'{rank}. <a href="{url}" target="_blank">{url}</a> (Score: {score:.2f})'
        results.append(result)
   
    return results