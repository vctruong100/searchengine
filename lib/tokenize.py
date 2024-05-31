# lib/tokenize.py
#
# tokenizes text using treebank tokenizer
#
# has additional helper functions for
# extending or manipulating tokens in-place

import itertools
from nltk.stem import PorterStemmer
from nltk.tokenize.treebank import TreebankWordTokenizer

_stemmer = PorterStemmer()
_tokenizer = TreebankWordTokenizer()


def tokenize(text, n=1):
    """Tokenizes text using the treebank word tokenizer
    If n > 1, then it also creates and returns n-grams up to n.
    Otherwise, n-grams will be empty.
    """
    assert n > 0, "ngram must be positive"
    spans_iter = _tokenizer.span_tokenize(text)

    tokens = []
    ngrams_col = [[] for _ in range(n - 1)]

    # append tokens
    for start, end in spans_iter:
        # build 1-gram (aka token)
        token = text[start:end].lower().strip()
        tokens.append(token.lower().strip())

        # build n-gram (n > 1)
        for i in range(2, n + 1):
            ngrams = ngrams_col[i - 2]
            ngrams.append(start)
            prev = len(ngrams) - i
            if prev >= 0:
                ngrams[prev] = text[ngrams[prev]:end].lower().strip()

    # strip incomplete n-grams
    for i in range(2, n + 1):
        del ngrams_col[i - 2][-(i - 1):]

    return tokens, ngrams_col


def extend_tokens_from_ngrams(tokens, ngrams_col):
    """Extends the list of tokens with tokens from
    all the n-grams in the collection.
    """
    # flattens ngrams_col
    # append to current list of tokens
    tokens.extend(itertools.chain(*ngrams_col))


def stem_tokens(tokens):
    """Stems the list of tokens using Porter stemming.
    """
    # Stem the tokens using the Porter Stemmer
    # https://www.geeksforgeeks.org/python-stemming-words-with-nltk/
    tokens[:] = map(lambda token: _stemmer.stem(token), tokens)

