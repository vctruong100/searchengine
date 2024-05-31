# lib/posting.py
#
# posting class

from functools import total_ordering
from lib.structs import *

@total_ordering
class Posting:
    def __init__(
        self,
        docid=None,
        tf=None,
        important=False
    ):
        self.docid = docid
        self.tf = tf
        self.fields = dict()
        self.fields['important'] = important

    def __lt__(self, other):
        return self.docid < other.docid

    def __eq__(self, other):
        return self.docid == other.docid


def sposting_rd(fh):
    """read struct posting
    """
    docid, _ = u64_rd(fh)
    tf, _ = u32_rd(fh)
    bits, _ = u32_rd(fh)

    # read fields from bits
    important = bits & 1

    return Posting(
        docid=docid,
        tf=tf,
        important=important,
    ), 16


def sposting_repr(obj):
    """byte repr of struct posting
    """
    docid = obj.docid
    tf = obj.tf
    fields = obj.fields
    bits = (
        fields['important'] << 0
        | 1 << 31
    )

    seq = bytearray()

    seq.extend(u64_repr(docid))
    seq.extend(u32_repr(tf))
    seq.extend(u32_repr(bits))

    return bytes(seq)

