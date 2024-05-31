# lib/reader.py
#
# reader for index files

import os
import glob
from collections import defaultdict
from lib.structs import *
from lib.posting import *
from lib.document import *

_INDEX_BUCKETS = {}
_INDEX_SEEK = defaultdict(dict)
_DOCINFO = []

_MERGEINFO_DOCID = 0
_MERGEINFO_TOTAL_TOKENS = 0

_initialized = False


def initialize(docinfo_filename, mergeinfo_filename, buckets_dir):
    """Initializes the reader by opening index files
    from the docinfo, mergeinfo, and the buckets directories.
    """
    if _initialized:
        return

    # parse docinfo - store docinfo file in memory
    with open(docinfo_filename, 'rb') as docfh:
        docfh.seek(0, 2)
        docend = docfh.tell()
        docfh.seek(0, 0)
        while docfh.tell() != docend:
            document, _ = sdocument_rd(docfh)
            for _ in range(document.docid - len(_DOCINFO) - 1):
                # sparse document ids - append with empty docs
                _DOCINFO.append(Document(
                    docid=len(_DOCINFO) + 1,
                    url='',
                    total_tokens=0
                ))
            _DOCINFO.append(document)

    # parse mergeinfo - store mergeinfo file in memory
    with open(mergeinfo_filename, 'rb') as mergefh:
        mergefh.seek(4, 0)
        _MERGEINFO_DOCID, _ = u64_rd(mergefh)
        _MERGEINFO_TOTAL_TOKENS, _ = u32_rd(mergefh)

    # parse seek files / open bucket files
    for path in glob.glob("*", root_dir=buckets_dir):
        full_path = os.path.join(buckets_dir, path)
        if os.path.isfile(full_path):
            bid = None
            if path.endswith(".bucket"):
                # bucket file
                bid = int(path[:-7])
                bucketfh = open(full_path, 'rb')
                _INDEX_BUCKETS[bid] = bucketfh
            elif path.endswith(".seek"):
                # seek file
                bid = int(path[:-5])
                seekfh = open(full_path, 'rb')
                seekfh.seek(0, 2)
                seekend = seekfh.tell()
                seekfh.seek(0, 0)
                while seek.tell() != seekend:
                    # store entire seek file in memory
                    token, _ = sstr_rd(seekfh)
                    offset, _ = u32_rd(seekfh)
                    _INDEX_SEEK[bid][token] = offset
                seekfile.close()

    _initialized = True # initialized successfully


def get_total_tokens():
    """Returns the total number of unique tokens
    across the entire set of documents.
    """
    return _MERGEINFO_TOTAL_TOKENS


def get_num_documents():
    """Returns the number of documents indexed.
    """
    return _MERGEINFO_DOCID


def get_document(docid):
    """Returns the Document object associated with the document ID.
    See 'lib/document.py' for the Document interface.
    """
    return _DOCINFO[docid - 1]


def get_postings(token):
    """Returns a list of postings associated with the token.
    Each posting list is sorted by ascending docID.
    See 'lib/posting.py' for the Posting interface.
    """
    if not token:
        return []
    bid = min(ord(token[0], 128)

    seekbucket = _INDEX_SEEK.get(bid, None)
    if not seek_bucket:
        return []

    seekoffset = seekbucket.get(token, None)
    if not seekoffset:
        return []

    bucketfh = _INDEX_BUCKETS[bid]
    bucketfh.seek(seekoffset, 0)

    num_postings, _ = u32_rd(bucketfh)
    postings = []

    for _ in range(num_postings):
        posting, _ = sposting_rd(bucketfh)
        postings.append(posting)
    return postings

