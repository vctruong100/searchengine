# lib/queryproc.py
#
# processes queries

import math
import numpy as np
import heapq
from collections import defaultdict
from lib.reader import *
from lib.tokenize import *
from lib.stopwords import is_stopword
from lib.word_count import *
from lib.params import *
from lib.structs import *

def postings_set(tokenset):
    """Returns postings set indexed both by
    doc id (document-at-a-time) or token (term-at-a-time)
    """
    docid_postings = defaultdict(dict)
    token_postings = defaultdict(list)

    docid_sets = []
    for token in tokenset:
        postings = get_postings(token)
        docid_set = set() # set of documents that have the term
        for posting in postings:
            docid_set.add(posting.docid)
            docid_postings[posting.docid][token] = posting
        docid_sets.append(docid_set)

    # consider only the intersection of doc ids
    query_docids = set.intersection(*docid_sets)
    for docid in list(docid_postings.keys()):
        if docid not in query_docids:
            del docid_postings[docid]

    for vec in docid_postings.values():
        token_postings[token].append(vec[token])

    return docid_postings, token_postings


def compute_scores(docid_postings, token_postings, query_vec):
    """Computes the net score for each document
    """
    doc_tfidfs = defaultdict(lambda: defaultdict(float))
    doc_cosine = defaultdict(float)
    net_relevance = defaultdict(float)

    doc_pr_quality = defaultdict(float)
    doc_hub_quality = defaultdict(float)
    doc_auth_quality = defaultdict(float)
    net_quality = defaultdict(float)

    net_scores = defaultdict(float)


    ### compute relevance ###

    # compute tfidf
    # this also promotes TFIDF if the posting contains
    # important text - the multiplier varies by its tag
    num_docs = get_num_nonempty_documents()
    idfs = defaultdict(float)
    for token, postings in token_postings.items():
        df = 1 + len(postings)
        idf = math.log((1 + num_docs) / df)
        for posting in postings:
            document = get_document(posting.docid)
            tf = posting.tf / document.total_tokens
            tfidf = tf * idf
            tfidf *= importance[posting.fields['important']]
            doc_tfidfs[posting.docid][token] = tfidf
        idfs[token] = idf

    doc_tfidf_sums = {docid: sum(tfidf.values()) for docid, tfidf in doc_tfidfs.items()}

    # compute cosine
    query_total_tokens = sum(query_vec.values())
    query_tfidf = defaultdict(float)
    for token, tf in query_vec.items():
        tf /= query_total_tokens
        query_tfidf[token] = tf * idfs[token]

    for docid, doc_tfidf in doc_tfidfs.items():
        for token, tfidf in query_tfidf.items():
            doc_cosine[docid] += (doc_tfidf[token] * tfidf)

    # compute norms of tfidf sum and cosine similarity
    doc_tfidf_sums_norm = np.linalg.norm(
        np.fromiter(doc_tfidf_sums.values(), dtype=float)
    )
    doc_cosine_norm = np.linalg.norm(
        np.fromiter(doc_cosine.values(), dtype=float)
    )

    # compute net relevance
    # note: if query and document is too dissimilar, we exclude the document
    for docid in docid_postings.keys():
        normalized_tfidf = (doc_tfidf_sums[docid] / doc_tfidf_sums_norm
            if doc_tfidf_sums_norm else 0.0)
        normalized_cosine = (doc_cosine[docid] / doc_cosine_norm
            if doc_cosine_norm else 0.0)
        net_relevance[docid] = (tfidf_factor * normalized_tfidf
            + cosine_factor * normalized_cosine)


    ### compute quality ###

    # retrieve qualities
    for docid in docid_postings.keys():
        document = get_document(docid)
        doc_pr_quality[docid] = document.pr_quality
        doc_hub_quality[docid] = document.hub_quality
        doc_auth_quality[docid] = document.auth_quality

    # compute norms of qualities
    doc_pr_norm = np.linalg.norm(
        np.fromiter(doc_pr_quality.values(), dtype=float)
    )
    doc_hub_norm = np.linalg.norm(
        np.fromiter(doc_hub_quality.values(), dtype=float)
    )
    doc_auth_norm = np.linalg.norm(
        np.fromiter(doc_auth_quality.values(), dtype=float)
    )

    # compute net quality
    for docid in docid_postings.keys():
        normalized_pr = (doc_pr_quality[docid] / doc_pr_norm
            if doc_pr_norm else 0.0)
        normalized_hub = (doc_hub_quality[docid] / doc_hub_norm
            if doc_hub_norm else 0.0)
        normalized_auth = (doc_auth_quality[docid] / doc_auth_norm
            if doc_auth_norm else 0.0)
        net_quality[docid] = (pr_factor * normalized_pr
            + hub_factor * normalized_hub
            + auth_factor * normalized_auth)


    ### compute net scores ###

    # combines relevance and quality scores
    for docid in docid_postings.keys():
        document = get_document(docid)
        net_scores[docid] = (net_relevance_factor * net_relevance[docid]
            + quality_factor * net_quality[docid])

    return net_scores


def process_query(query):
    """Returns the ranked results from this query
    """
    # tokenize query and stem
    import time
    tt = time.time()

    tokens, _ = tokenize(query)
    stem_tokens(tokens)
    frequencies = word_count(tokens)

    et = time.time()

    tt2 = time.time()

    # number of pruned tokens (non-unique)
    # number of total valid tokens (non-unique) in query
    # number of unique valid tokens in query
    prune_count = 0
    valid_count = 0
    num_valid_tokens = 0

    # validate tokens and ignore any
    # tokens that do not yield any docs
    # stopwords are removed temporarily for extra filtering
    #
    # if a token is ignored, the prune count increases if and only if
    # the token is alphanumeric
    stopwords = set()
    stopwords_heap = []
    for token in sorted(frequencies.keys()):
        postings = get_postings(token)
        doc_freq = len(postings)
        if doc_freq == 0:
            if token.isalnum(): # alphanumeric counts towards prune
                prune_count += frequencies[token]
            del frequencies[token]
            continue
        num_valid_tokens += 1
        valid_count += frequencies[token]
        if is_stopword(token):
            token_freq = frequencies[token]
            if not token_freq:
                continue
            heapq.heappush(
                stopwords_heap,
                (doc_freq, token_freq, token)
            )
            stopwords.add(token)
            del frequencies[token]

    # if the number of pruned tokens is substantial
    # (i.e. no docs contain these tokens), the query was
    # probably not good in the first place, so return an empty result
    if prune_count > valid_count * 2:
        return []

    # if unique stopwords are insignificant, prune the stopwords
    # otherwise, consider the first k+1 unique stopwords that are least
    # frequently represented in docs (but are represented)
    # where k = log2(number of stopwords)
    if len(stopwords) > 0 and not (len(stopwords) < num_valid_tokens * 0.3):
        k = 1 + int(math.log2(len(stopwords)))
        for _ in range(k):
            _, freq, token = heapq.heappop(stopwords_heap)
            frequencies[token] = freq

    if not frequencies:
        return [] # empty query after pruning

    et2 = time.time()

    tt3 = time.time()

    docid_postings, token_postings = postings_set(frequencies.keys())

    et3 = time.time()

    print('tokenize', et-tt)
    print('stopwords', et2-tt2)
    print('postings', et3-tt3)

    if not docid_postings:
        return [] # no documents matched

    tt4 = time.time()

    net_scores = compute_scores(docid_postings, token_postings, frequencies)

    et4 = time.time()

    print('compute', et4-tt4)

    tt5 = time.time()

    ranked_scores = sorted(
        net_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    et5 = time.time()

    print('ranking', et5-tt5)

    return ranked_scores


def format_results_tty(result, k):
    """Returns the top K results and formats
    the results for the terminal interface.
    """
    results = []
    for rank, (docid, score) in enumerate(result[:k], 1):
        if score <= 0.01:
            break # score is too low
        document = get_document(docid)
        url = document.url if document.url else "URL not found"
        result = f'Rank {rank}: {url} (Score: {score:.2f})'
        results.append(result)
    return results


def format_results_web(result, k, SUMMARY_NAME):
    """Returns the top K results and formats
    the results for the web interface.
    """
    # Format output to include rankings, URLS, and scores
    results = []
    for rank, (docid, score) in enumerate(result[:k], 1):
        if score <= 0.01:
            break # score is too low
        document = get_document(docid)
        url = document.url if document.url else "URL not found"
        summary = get_summary(docid)
        print(summary)
        results.append(
            f'{rank}. <a href="{url}" target="_blank">{url}</a> (Score: {score:.2f})<br>Summary: {summary}'
        )
    return results
