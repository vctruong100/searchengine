# indexlib/reader.py
#
# reader for index files

import glob
from indexlib.posting import Posting

INDEX_FILES = {}
INDEX_SEEK = {}
DOCID_MAPPING = []

# parse seek files and open index data files
# precomputed
_root_dir = "index/"
for path in glob.glob("*", root_dir=_root_dir):
    if path.endswith(".seek"):
        seekfile = open(_root_dir + path, "rb")
        while True:
            slen = seekfile.read(4)
            if not slen:
                break
            slen = int.from_bytes(
                slen,
                byteorder="little",
                signed=False
            )
            str = seekfile.read(slen).decode("utf-8")
            seekkey = str[0] if ord(str[0]) < 128 else "misc"
            dic = INDEX_SEEK.get(seekkey, None)
            if not dic:
                dic = {}
                INDEX_SEEK[seekkey] = dic
            dic[str] = int.from_bytes(
                seekfile.read(4),
                byteorder="little",
                signed=False
            )
        seekfile.close()
    else:
        bucketfile = open(_root_dir + path, "rb")
        if path != "misc":
            INDEX_FILES[chr(int(path))] = bucketfile
        else:
            INDEX_FILES[path] = bucketfile


# parse countdoc file
with open("countdoc", "r", encoding="utf-8") as cdf:
    for line in cdf:
        if not line:
            continue
        docID = line.split(",")[0]
        url = line[len(docID) + 1:].rstrip()
        DOCID_MAPPING.append(url)


# parse header
# TODO


def _get_bucketkey(str):
    return str[0] if ord(str[0]) < 128 else "misc"


def get_url(docid):
    """Gets the URL associated with the document ID.
    """
    return DOCID_MAPPING[docid - 1]

def get_postings(token):
    """Returns a list of postings associated with the token.
    Each posting list is sorted by ascending docID.
    """
    if not token:
        return []
    bucketkey = _get_bucketkey(token)
    seek_bucket = INDEX_SEEK.get(bucketkey, None)
    if not seek_bucket:
        return []
    seek_pos = seek_bucket.get(token, None)
    if not seek_pos:
        return []
    indexfile = INDEX_FILES[bucketkey]
    indexfile.seek(seek_pos)

    posting_ls_size = int.from_bytes(
        indexfile.read(4),
        byteorder="little",
        signed=False
    )
    posting_ls = []
    size_read = 0
    while size_read < posting_ls_size:
        size_read += Posting.size
        posting = Posting()
        posting.decode(indexfile.read(Posting.size))
        posting_ls.append(posting)
    return posting_ls

