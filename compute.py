# compute.py

# Computes and assigns PageRank and HITS scores to indexed documents.

import sys
from lib.pagerank import page_rank
from lib.hits import hits_algorithm
from lib.reader import initialize, get_num_documents, get_document, initialize_doclinks
from lib.writer import update_doc_pr_quality, update_doc_hits_quality
from lib.indexfiles import *

USAGE_MSG = "usage: python compute.py"

def compute_scores():
    """Compute and update PageRank and HITS scores for all documents.
    """
    initialize(
        docinfo_filename=DOCINFO_NAME,
        mergeinfo_filename=MERGEINFO_NAME,
        buckets_dir=BUCKETS_DIR
    )

    initialize_doclinks(DOCLINKS_NAME)
    
    # Gather all documents
    documents = [get_document(doc_id) for doc_id in range(1, get_num_documents() + 1)]

    # Compute PageRank scores
    pr_scores = page_rank(documents)
    update_doc_pr_quality(DOCINFO_NAME, pr_scores)

        
    # Compute HITS scores (Hub and Authority)
    hub_scores, auth_scores = hits_algorithm(documents)
    hits_scores = {doc_id: (hub_scores.get(doc_id, 0), auth_scores.get(doc_id, 0)) for doc_id in hub_scores}  
    update_doc_hits_quality(DOCINFO_NAME, hits_scores)

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    print("Computing scores...")
    compute_scores()
    print("Scores computed successfully.")
