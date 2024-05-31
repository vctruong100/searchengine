# lib/hits.py

# Implements the HITS Algorithm for documents indexed.

import numpy as np

def initialize_scores(docs):
    # Store hub scores, initializing each score to 1; ensure that all docs start with equal weight
    hub_scores = {doc.docid: 1 for doc in docs}
    # Store authority scores, initializing each score to 1
    authority_scores = {doc.docid: 1 for doc in docs}
    return hub_scores, authority_scores

def hits_algorithm(docs, max_iter=100, tol=1e-6):
    """Calculate HITS scores for documents.

    :param docs: List of Document objects
    :param max_iter: Maximum number of iterations (default 100)
    :param tol: Convergence tolerance (default 1e-6)
    :return: Tuple of dictionaries of docid to hub and authority scores
    """
    hub_scores, authority_scores = initialize_scores(docs)

    # Iterate up to a maximum number of iterations or until convergence
    for _ in range(max_iter):
        # Dictionaries to store new scores for this iteration
        new_hub_scores = {}
        new_authority_scores = {}
        
        # Calculate the new hub and authority scores based on the current scores
        # Hub scores = sum of the authority scores of the documents it links to
        # Auth scores = sum of the hub scores of the documents that link to it
        for doc in docs:
            new_hub_scores[doc.docid] = sum(authority_scores.get(link, 0) for link in doc.links)
            new_authority_scores[doc.docid] = sum(hub_scores.get(link, 0) for link in doc.links)
        
        # Normalize the new hub scores and auth scores to prevent values from escalating
        norm = np.sqrt(sum(score ** 2 for score in new_hub_scores.values()))
        for doc_id in new_hub_scores:
            new_hub_scores[doc_id] /= norm

        norm = np.sqrt(sum(score ** 2 for score in new_authority_scores.values()))
        for doc_id in new_authority_scores:
            new_authority_scores[doc_id] /= norm

        # Check for convergence: if scores change is below the threshold, stop the algorithm
        hub_convergence = all(np.abs(new_hub_scores[doc_id] - hub_scores[doc_id]) < tol for doc_id in hub_scores)
        authority_convergence = all(np.abs(new_authority_scores[doc_id] - authority_scores[doc_id]) < tol for doc_id in authority_split_scores)
        if hub_convergence and authority_convergence:
            break

        # Update the scores with the new values for the next iteration
        hub_scores, authority_scores = new_hub_scores, new_authority_scores

    return hub_scores, authority_scores

# Update the document scores with the hub and authority scores
def update_document_scores(docs, hub_scores, authority_scores):
    continue
