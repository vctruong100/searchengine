# lib/params.py

def _assert_sum_is_one(*args, assertmsg=''):
    _sum = sum(args)
    assert _sum >= 1-1e-5 and _sum <= 1+1e-5, assertmsg


# score multiplier for important text
importance = [
    0.8,    # untagged (not important)
    3.5,    # title
    2.5,    # h1
    2.1,    # h2
    1.6,    # h3
    1.3,    # h4 (bold)
    1.1,    # strong (bold)
    1.1,    # b (bold)
    1.0,    # mark (highlighted text)
]


# scoring parameters
# net_relevance is for tfidf + cosine similarities
# quality is the static quality score
net_relevance_factor = 0.61
quality_factor = 1 - net_relevance_factor

_assert_sum_is_one(net_relevance_factor, quality_factor,
    assertmsg="scoring factors must sum to 1")


# relevance parameters
# tfidf is term frequency * inverse document frequenc
# cosine is cosine similarity
tfidf_factor = 0.73
cosine_factor = 1 - tfidf_factor

_assert_sum_is_one(tfidf_factor, cosine_factor,
    assertmsg="relevance factors must sum to 1")


# quality factor parameters
# pagerank, hits (hub/auth)
pr_factor = 0.59
hub_factor = 0.23
auth_factor = 0.18

_assert_sum_is_one(pr_factor, hub_factor, auth_factor,
    assertmsg="quality factors must sum to 1")


