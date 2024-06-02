# lib/params.py

def _assert_sum_is_one(*args, assertmsg=''):
    _sum = sum(args)
    assert _sum >= 1-1e-5 and _sum <= 1+1e-5, assertmsg


# score multiplier for important text
importance = [
    1.0     # untagged (not important)
    3.0,    # title
    2.0,    # h1
    1.6,    # h2
    1.4,    # h3
    1.2,    # h4 (bold)
    1.2,    # strong (bold)
    1.2,    # b (bold)
    1.2,    # mark (highlighted text)
]


# scoring parameters
# net_relevance is for tfidf + cosine similarities
# quality is the static quality score
net_relevance_factor = 1
quality_factor = 1 - net_relevance_factor

_assert_sum_is_one(net_relevance_factor, quality_factor,
    assertmsg="scoring factors must sum to 1")


# relevance parameters
# tfidf is term frequency * inverse document frequenc
# cosine is cosine similarity
tfidf_factor = 0.8
cosine_factor = 1 - tfidf_factor

_assert_sum_is_one(tfidf_factor, cosine_factor,
    assertmsg="relevance factors must sum to 1")


# quality factor parameters
# pagerank, hits (hub/auth)
pr_factor = 0.6
hub_factor = 0.2
auth_factor = 0.2

_assert_sum_is_one(pr_factor, hub_factor, auth_factor,
    assertmsg="quality factors must sum to 1")


