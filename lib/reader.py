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
_DOCINFO_LINKS_INDEX = {}
_DOCLINKS = []

_MERGEINFO_DOCID = 0
_MERGEINFO_TOTAL_TOKENS = 0

_NONEMPTY_DOC_CNT = 0
_EMPTY_DOC_CNT = 0

_initialized = False
_initialized_docs = False


def initialize(docinfo_filename, mergeinfo_filename, buckets_dir):
    """Initializes the reader by opening index files
    from the docinfo, mergeinfo, and the buckets directories.
    """
    global _initialized
    if _initialized:
        return

    global _INDEX_BUCKETS
    global _INDEX_SEEK
    global _DOCINFO
    global _DOCINFO_LINKS_INDEX
    global _DOCLINKS
    global _MERGEINFO_DOCID
    global _MERGEINFO_TOTAL_TOKENS
    global _NONEMPTY_DOC_CNT
    global _EMPTY_DOC_CNT

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
                    total_tokens=0,
                    empty=True
                ))
                _EMPTY_DOC_CNT += 1
            _DOCINFO.append(document)
            _DOCINFO_LINKS_INDEX[document.url] = document.docid
            _NONEMPTY_DOC_CNT += 1

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
                while seekfh.tell() != seekend:
                    # store entire seek file in memory
                    token, _ = sstr_rd(seekfh)
                    offset, _ = u32_rd(seekfh)
                    _INDEX_SEEK[bid][token] = offset
                seekfh.close()

    _initialized = True # initialized successfully


def initialize_doclinks(doclinks_filename):
    """Initializes each docid with the set of URLs crawled.
    If URL is not contained within the documents or the
    document is not empty, then it is not included in the set.

    Note: You should only call this function when you are doing
    pagerank / HITS computations. The search engine does not need this.
    """
    global _initialized
    global _initialized_docs
    assert _initialized, "call reader.initialize() before calling this"
    if _initialized_docs:
        return

    global _DOCINFO
    global _DOCLINKS
    global _DOCLINKS_INDEX

    # read doclinks
    with open(doclinks_filename, 'rb') as doclinksfh:
        doclinksfh.seek(2, 0)
        doclinksend = doclinksfh.tell()
        doclinksfh.seek(0, 0)
        while doclinksfh.tell() != doclinksend:
            docid, _ = u64_rd(doclinksfh)
            for _ in range(docid - len(_DOCLINKS) - 1):
                # sparse document ids - append with empty set
                _DOCLINKS.append(set())

            urlset = set()
            num_urls, _ = u32_rd(doclinksfh)
            for _ in range(num_urls):
                # store url as docid if it exists and non-empty
                url, _ = sstr_rd(doclinksfh)
                docid = _DOCINFO_LINKS_INDEX.get(url, None)
                if docid:
                    document = _DOCINFO[docid - 1]
                    if document and not document.empty:
                        urlset.add(docid)
            _DOCLINKS.append(urlset)

    _initialized_docs = True # initialized successfully


def get_total_tokens():
    """Returns the total number of unique tokens
    across the entire set of documents.
    """
    global _MERGEINFO_TOTAL_TOKENS
    return _MERGEINFO_TOTAL_TOKENS


def get_num_documents():
    """Returns the total number of documents indexed.
    """
    global _MERGEINFO_DOCID
    return _MERGEINFO_DOCID


def get_num_empty_documents():
    """Returns the total number of empty documents indexed.
    """
    global _EMPTY_DOC_CNT
    return _EMPTY_DOC_CNT


def get_num_nonempty_documents():
    """Returns the total number of non-empty documents indexed.
    """
    global _NONEMPTY_DOC_CNT
    return _NONEMPTY_DOC_CNT


def get_document(docid):
    """Returns the Document object associated with the document ID.
    See 'lib/document.py' for the Document interface.
    """
    global _DOCINFO
    return _DOCINFO[docid - 1]


def get_linked_docids(docid):
    """Returns reachable documents as a set of docids from this
    particular document. Note that reachable means its URL exists
    in the document content.
    """
    global _DOCLINKS
    return _DOCLINKS[docid - 1]


def get_postings(token):
    """Returns a list of postings associated with the token.
    Each posting list is sorted by ascending docID.
    See 'lib/posting.py' for the Posting interface.
    """
    if not token:
        return []
    bid = min(ord(token[0]), 128)

    seekbucket = _INDEX_SEEK.get(bid, None)
    if not seekbucket:
        return []

    seekoffset = seekbucket.get(token, None)
    if not seekoffset:
        return []

    global _INDEX_BUCKETS

    bucketfh = _INDEX_BUCKETS[bid]
    bucketfh.seek(seekoffset, 0)

    num_postings, _ = u32_rd(bucketfh)
    postings = []

    for _ in range(num_postings):
        posting, _ = sposting_rd(bucketfh)
        postings.append(posting)
    return postings

