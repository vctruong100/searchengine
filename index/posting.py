# index/posting.py
#
# posting class

class Posting:
    def __init__(self, docid=None, tfidf=None, fields=dict()):
        self.docid = docid
        self.tfidf = tfidf
        self.fields = fields

    def decode(self, seq):
        """Updates the Posting object based on the bytes.
        """
        posting = cls.__new__(cls)
        posting.fields = dict()

        # docid, score
        posting.docid = int.from_bytes(seq[:8], "little")
        posting.tfidf = int.from_bytes(seq[8:12], "little")

    def encode(self):
        """Returns the Posting in bytes.
        """
        docid = self.docid
        tfidf = self.tfidf

        seq = bytearray()
        seq.extend(docid.to_bytes(8, "little"))
        seq.extend(tfidf.to_bytes(4, "little"))

        return bytes(seq)

