# compute.py

# Computes and assigns PageRank and HITS scores to indexed documents.

import sys
from lib.pagerank import page_rank
from lib.hits import hits_algorithm
from lib.reader import initialize, get_num_documents, get_document
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

    # Gather all documents
    documents = [get_document(doc_id) for doc_id in range(1, get_num_documents() + 1)]

    # Compute PageRank scores
    pr_scores = page_rank(documents)
    for doc in documents:
        doc.pr_quality = pr_scores.get(doc.docid, 0)  

    # Compute HITS scores (Hub and Authority)
    hub_scores, auth_scores = hits_algorithm(documents)
    for doc in documents:
        doc.hub_quality = hub_scores.get(doc.docid, 0)
        doc.auth_quality = auth_scores.get(doc.docid, 0) 


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    compute_scores()
