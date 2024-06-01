# lib/pagerank.py
#
# Implements the PageRank Algorithm for documents indexed.

import numpy as np

def page_rank(docs, damping=0.85, max_iter=100, tol=1e-6):
    """Calculate PageRank scores for documents.

    :param docs: List of Document objects
    :param damping: Damping factor (default 0.85)
    :param max_iter: Maximum number of iterations (default 100)
    :param tol: Convergence tolerance (default 1e-6)
    :return: Dictionary of docid to PageRank score
    """

    n = len(docs)  
    if n == 0:
        return {} 

    # Initialize the page rank dict with an equal rank to all pages
    page_ranks = {doc.docid: 1 / n for doc in docs}
    
    # Create a dictionary of docids and the set of docs that link to each
    link_structure = {doc.docid: set() for doc in docs}
    for doc in docs:
        if doc.links: 
            for link in doc.links:
                if link in link_structure:
                    link_structure[link].add(doc.docid)

    # Iterative calculation of page rank
    for iteration in range(max_iter):
        new_ranks = {}
        # Calculate each document's new rank
        for docid, linked_by in link_structure.items():
            # Sum the PageRank of each linking document divided by the number of links it has
            rank_sum = sum(page_ranks[linking_docid] / len(docs[linking_docid].links) for linking_docid in linked_by)
            
            # Calculate the new rank using the damping factor
            new_ranks[docid] = (1 - damping) + (damping * rank_sum)

        # Check for convergence: if the change in PageRank is less than the tolerance for all documents, stop iterating
        if all(abs(new_ranks[docid] - page_ranks[docid]) < tol for docid in page_ranks):
            break

        # Update the PageRanks for the next iteration
        page_ranks = new_ranks

    return page_ranks

