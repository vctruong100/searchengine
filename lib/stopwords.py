# lib/stopwords.py
#
# word set for rsrc/stopwords.txt
# check if a particular word is a stopword or not

_STOPWORDS_SET = set()

# open rsrc/stopwords.txt
# load words into STOPWORDS_SET
with open("rsrc/stopwords.txt", "r") as infile:
    for word in infile:
        _STOPWORDS_SET.add(word.strip())

def is_stopword(word):
    """Returns True if `word` is a stopword according to
    rsrc/stopwords.txt. Returns False otherwise.
    
    :param word str: The string
    :return: Whether it's a stopword
    :rtype: bool
    """
    return word in _STOPWORDS_SET

