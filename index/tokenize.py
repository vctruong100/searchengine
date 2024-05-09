# tokenize.py
#
# custom tokenizer for handling words in pages
# somtimes treats certain symbols as part of the token
# also handles contractions too

# symbols (non-alnum chars) that are in this set will not split the token and
# instead be included in the token
GROUP_SYMBOLS = r"-./_~."

# of the chars in GROUP_SYMBOLS, these symbols are non-terminable (i.e. tokens
# cannot end with these symbols) (e.g. "a..." is not a token)
NONTERM_GROUP_SYMBOLS = r"."

# of the chars in GROUP_SYMBOLS, these symbols cannot repeat in sequence inside
# a token (e.g. "a..b" is not a token)
NONREPEAT_GROUP_SYMBOLS = r"."


def _add_processed_word(word, processed_list, alnum_hit):
    """Private helper function to add word to processed_list after checking constraints"""
    # words must contain at least 1 alnum grapheme
    if not word or not alnum_hit:
        return
    # strip right end so that words
    # cannot end in NONTERM_GROUP_SYMBOLS
    word = word.rstrip(NONTERM_GROUP_SYMBOLS)
    processed_list.append(word)


def tokenize(text):
    """Tokenizes text into a list of processed tokens.

    The tokenizer processes tokens under these rules:
        -   Tokens converted to lowercase
        -   Tokens are discarded if it's a stopword (see helpers/stopwords_set.py)
        -   Tokens are kept if it's a contraction (see helpers/contra_set.py)
        -   Symbols split the token unless it's in GROUP_SYMBOLS.
            If it's a GROUP_SYMBOL, it's treated as part of the token regardless of where it's at
        -   ASCII alnum chars are always kept
            For non-ASCII graphemes, let the Python interpreter determine what's alnum (using str.isalnum())
            For example, these are alnum: Привет, ハーロー
        -   Tokens are considered if and only if it contains at least one alnum char/grapheme

    Observations from str.alnum():
        -   alnum() returns true if it's a printable non-punctuation grapheme (from any language)
        -   The alphabet for other languages is not limited to the set [A-Za-z]

    :param text str: Text content
    :return: A list of processed tokens based on the tokenizer policy
    :rtype: list[str]
    """
    # preprocessing: split tokens by whitespace
    preprocessed = text.split()

    # allocate list of processed tokens
    processed = []

    # for each preprocessed token, process it
    for token in preprocessed:
        # lowercase only
        token = token.lower()

        # process token grapheme-by-grapheme
        # for loop over strings will loop over graphemes (not by byte/char)
        # when non-alnum or non-GROUP SYMBOL hit, split word
        # treat symbols in GROUP_SYMBOLS as part of the word
        # if word does not contain at least 1 alnum char, discard the word

        word = "" # word to build
        alnum_hit = False # word contains at least 1 alnum grapheme
        gs_repeat = None # current NONREPEAT_GROUP_SYMBOL sequence

        for grapheme in token:
            # only happens if word is in a NONREPEAT_GROUP_SYMBOL sequence
            # consumes the same symbol until there's no more left
            if gs_repeat:
                if grapheme == gs_repeat:
                    word += grapheme
                    continue
                else:
                    _add_processed_word(word, processed, alnum_hit)
                    word, alnum_hit = "", False
                    gs_repeat = None # no longer in a repeat sequence

            # alnum is always part of the token
            if grapheme.isalnum():
                alnum_hit = True
                word += grapheme
                continue

            # check if grapheme is in GROUP_SYMBOLS
            # treat GROUP_SYMBOL as part of the token unless it violates a rule

            if grapheme in GROUP_SYMBOLS:
                # note: if word is empty, then this check doesn't matter
                # make sure grapheme is allowed to repeat itself
                # if it's not allowed, make sure the grapheme doesn't violate the rule
                if not word or grapheme not in NONREPEAT_GROUP_SYMBOLS or word[-1] != grapheme:
                    word += grapheme
                    continue

                # nonrepeat rule violated
                # split word to the word before the sequence and the sequence itself
                _add_processed_word(word[:-1], processed, alnum_hit)
                word, alnum_hit = grapheme * 2, False
                gs_repeat = grapheme # currently in a repeat sequence

            else:
                # grapheme is not in GROUP_SYMBOLS
                # append word if non-empty
                if word:
                    _add_processed_word(word, processed, alnum_hit)
                    word, alnum_hit = "", False

        # make sure non-empty words are appended to processed list when it
        # finishes reading the graphemes
        if word:
            _add_processed_word(word, processed, alnum_hit)


    return processed
