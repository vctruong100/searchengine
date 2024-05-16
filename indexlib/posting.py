# indexlib/posting.py
#
# posting class

from functools import total_ordering

@total_ordering
class Posting:
    size = 16

    def __init__(self, docid=None, tf=None, total_tokens=None, fields=dict()):
        self.docid = docid
        self.tf = tf
        self.total_tokens = total_tokens
        self.fields = fields

    def __lt__(self, other):
        return self.docid < other.docid

    def __eq__(self, other):
        return self.docid == other.docid

    def decode(self, seq):
        """Updates the Posting object based on the bytes.
        """
        self.docid = int.from_bytes(seq[:8], "little")
        self.tf = int.from_bytes(seq[8:12], "little")
        self.total_tokens = int.from_bytes(seq[12:16], "little")

    def encode(self):
        """Returns the Posting in bytes.
        """
        docid = self.docid
        tf = self.tf
        total_tokens = self.total_tokens
        
        seq = bytearray()

        seq.extend(docid.to_bytes(8, "little"))
        seq.extend(tf.to_bytes(4, "little"))
        seq.extend(total_tokens.to_bytes(4, "little"))

        return bytes(seq)

