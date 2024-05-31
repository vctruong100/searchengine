# lib/word_count.py
#
# computes the word frequencies of the
# list of tokens

def word_count(tokens):
    """Returns the mapping of tokens/words to its frequency.

    :param tokens list[str]: The list of tokens
    :return: The mapping
    :rtype: dict[str, int]
    """
    word_dict = dict()
    for token in tokens:
        word_dict[token] = word_dict.get(token, 0) + 1
    return word_dict

