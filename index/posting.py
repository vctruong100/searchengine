# index/posting.py
#
# posting class

from functools import total_ordering


@total_ordering
class Posting:
    size = 12

    def __init__(self, docid=None, tfidf=None, fields=dict()):
        self.docid = docid
        self.tfidf = tfidf
        self.fields = fields

    def __lt__(self, other):
        return self.docid < other.docid

    def __eq__(self, other):
        return self.docid == other.docid

    def decode(self, seq):
        """Updates the Posting object based on the bytes.
        """
        self.docid = int.from_bytes(seq[:8], "little")
        self.tfidf = int.from_bytes(seq[8:12], "little")

    def encode(self):
        """Returns the Posting in bytes.
        """
        docid = self.docid
        tfidf = self.tfidf

        seq = bytearray()
        seq.extend(docid.to_bytes(8, "little"))
        seq.extend(tfidf.to_bytes(4, "little"))

        return bytes(seq)

