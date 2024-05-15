# helpers/contra_set.py
#
# word set for rsrc/contractions.txt
# check if a particular word is a contraction or not

CONTRA_SET = set()
GENERIC_CONTRA_SET = set()

# open rsrc/contractions.txt
# load words/patterns into CONTRA_SET or GENERIC_CONTRA_SET
with open("rsrc/contractions.txt", "r") as infile:
    for word in infile:
        word = word.strip()

        # normal contraction
        # add to CONTRA_SET
        if not word[0] == "-":
            CONTRA_SET.add(word)

        # generic contraction
        # add suffix (exclude "-") to GENERIC_CONTRA_SET
        if word.startswith("-"):
            GENERIC_CONTRA_SET.add(word[1:])

def is_contraction(word):
    """Returns True if `word` is a contraction according to
    rsrc/contractions.txt. Returns False otherwise.

    :param word str: The string
    :return: Whether it's a contraction
    :rtype: bool
    """
    if word in CONTRA_SET:
        return True
    for suffix in GENERIC_CONTRA_SET:
        if word.endswith(suffix):
            return True
    return False
