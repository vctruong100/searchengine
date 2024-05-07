# index/posting.py
#
# posting class

class Posting:
    size = 12

    def __init__(self, docid, score, fields=dict()):
        self.docid = id
        self.score = score
        self.fields = fields

    @staticmethod
    def read(cls, fh):
        posting = cls.__new__(cls)
        posting.docid = int.from_bytes(fh.read(8), "little")
        posting.score = int.from_bytes(fh.read(4), "little")
        posting.fields = dict()

    def write(self, fh):
        fh.write(int.to_bytes(self.docid, 8, "little")
        fh.write(int.to_bytes(self.score, 4, "little")

