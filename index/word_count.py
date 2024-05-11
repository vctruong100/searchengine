# helpers/word_counts.py
#
# computes the word frequencies of the response
# based on the tokenizer in helpers/tokenize

from index.tokenize import tokenize

def to_tokens(text_content):
    """Returns a list of tokens from after tokenizing text_content.
    See helpers/tokenize for more info on how the tokenizer works,
    and what tokens are returned.

    :param text_content list[str]: The text content
    :return: A list of tokens
    :rtype: list[str]
    """
    tokens = []
    for text in text_content:
        _tokenized = tokenize(text)
        tokens.extend(_tokenized)
    return tokens

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

