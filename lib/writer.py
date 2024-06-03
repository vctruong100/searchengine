# lib/writer.py
#
# writes inverted index to disk
# see lib/spec.md

from queue import PriorityQueue
from lib.structs import *
from lib.posting import *
from lib.document import *

PART_VER = 1
MERGE_VER = 1

CHK_P_OK = 0x00                 # partial file is complete
CHK_P_VER_MISMATCH = 0xfd       # wrong partial file version
CHK_P_INCOMPLETE = 0xfe         # partial file is incomplete


def new_partial(filename=None, fh=None):
    """Creates and returns a new file handler that encapsulates the partial container format.
    If a file handler is specified, it uses the file handler instead.
    """
    assert bool(fh) != bool(filename), "either fh or filename must be specified (but not both)"

    if fh:
        fh.seek(0, 0)
        fh.truncate()
    else:
        fh = open(filename, 'w+b')

    # initialize partial header (14 bytes)
    fh.write(u8_repr(PART_VER))     # version
    fh.write(u8_repr(0))            # complete = 0
    fh.write(u64_repr(0))           # docid = 0
    fh.write(u32_repr(0))           # partcnt = 0

    return fh


def check_partial(partfh):
    """Checks partial file. Returns a CHK_P_* constant indicating its status.
    If status is not CHK_P_VER_MISMATCH, also returns its header as a tuple.
    Note: The returned header excludes "version" and "is_complete".
    """
    cur = partfh.tell()
    partfh.seek(0, 0)
    try:
        version, _ = u8_rd(partfh)
        is_complete, _ = u8_rd(partfh)
        partdoc, _ = u64_rd(partfh)
        partcnt, _ = u32_rd(partfh)

        if version != PART_VER:
            return CHK_P_VER_MISMATCH, None
        if is_complete == 0:
            return CHK_P_INCOMPLETE, (partdoc, partcnt)
        return CHK_P_OK, (partdoc, partcnt)

    finally:
        partfh.seek(cur, 0)


def mark_partial(partfh):
    """Marks the partial file as complete.
    """
    cur = partfh.tell()
    partfh.seek(1, 0)
    partfh.write(u8_repr(1))
    partfh.seek(cur, 0)


def write_partial(index, docs, partfh, docfh, doclinksfh):
    """Appends the partial index to `partfh` and the docinfo to `docfh`.
    Clears the index and docs if and only if the write was successful.

    If any write fails, then:
        (1) the files are reverted to their original states,
        (2) the index and docs are not cleared,
        (3) the function propagates the exception.

    :param index dict[str, list[Posting]]: The inverted index
    :param docs list[Document]: A list of documents to be added
    :param partfh: The partial container file handler
    :param docfh: The doc file handler
    :param doclinksfh: The doc links file handler

    :return: Whether the function succeeded
    :rtype: bool

    """
    if not docs:
        index.clear()
        return # no docs

    part_end_offset = partfh.tell()
    doc_end_offset = docfh.tell()

    # get previous header values
    partfh.seek(2, 0)
    prev_docid, _ = u64_rd(partfh)
    prev_partcnt, _ = u32_rd(partfh)

    # buffered write
    # write to doc/doclinks buffer and part buffer
    # (partial tokens are sorted lexicographically)
    part_mmap = bytearray()
    doc_mmap = bytearray()
    doclinks_mmap = bytearray()

    docid = None

    for doc in docs:
        docid = doc.docid
        doc_mmap.extend(sdocument_repr(doc))
        doclinks_mmap.extend(u64_repr(docid))
        doclinks_mmap.extend(u32_repr(len(doc.links)))
        for link in doc.links:
            doclinks_mmap.extend(sstr_repr(link))

    for token in sorted(index.keys()):
        postings = index[token]
        part_mmap.extend(sstr_repr(token))
        part_mmap.extend(u32_repr(len(postings)))
        for p in postings:
            part_mmap.extend(sposting_repr(p))

    # try writing to files
    # if it fails, restore the files and propagate
    try:
        # update header
        partfh.seek(2, 0)
        partfh.write(u64_repr(docid)) # last docid in docs list
        partfh.write(u32_repr(prev_partcnt + 1))

        # update partial container
        partfh.seek(part_end_offset, 0)
        partfh.write(u32_repr(len(part_mmap)))
        partfh.write(part_mmap)

        # update docs
        docfh.write(doc_mmap)

        # update doclinks
        doclinksfh.write(doclinks_mmap)

        # clear index and docs
        index.clear()
        docs.clear()
        return True # success

    except Exception as e:
        # restore original state of partial file
        partfh.seek(2, 0)
        partfh.write(u64_repr(prev_docid))
        partfh.write(u32_repr(prev_partcnt))
        partfh.seek(part_end_offset, 0)
        partfh.truncate()

        # restore original state of docs
        docfh.seek(doc_end_offset, 0)
        docfh.truncate()

        raise e # propagate


def merge_partial(partfh, merge_filename, buckets_dir):
    """Merges the partial container using k-way (k = partcnt).
    The contents are stored in `buckets_dir` as buckets based on
    the first char of the token.

    For each bucket, a corresponding seek file is created to enable
    fast retrieval. This is internally stored as a sequence of string to
    u32 pairs.

    Bucket files have ".bucket" as the file extension.
    Seek files have ".seek" as the file extension.

    :param partfh: The partial container file handler
    :param merge_filename str: The filename where merge info is stored.
    :param buckets_dir str: The directory where buckets are stored.

    :return: Whether the merge was successful
    :rtype: bool

    """
    # read partial header
    partfh.seek(2, 0)
    docid, _ = u64_rd(partfh)
    partcnt, _ = u32_rd(partfh)

    # setup: internals
    tokencnt = 0
    bucket_char = None
    bucket_fh = None
    bucket_seekfh = None

    partseekers = []                            # list of tuples (partsize, partseekerfh)
    key_queue = PriorityQueue(maxsize=partcnt)  # retrieve tokens in sorted order
    val_queue = PriorityQueue()                 # retrieve sorted postings by docid

    # setup: initialize part seekers and key queue
    for pid in range(partcnt):
        partsize, _ = u32_rd(partfh)
        partseekerfh = open(partfh.name, 'rb')
        partseekerfh.seek(partfh.tell(), 0)
        if partsize > 0:
            token, token_rdsize = sstr_rd(partseekerfh)
            partseekers.append((partsize - token_rdsize, partseekerfh))
            key_queue.put((token, pid), block=False)
        else:
            partseekers.append((partsize, partseekerfh))
        partfh.seek(partsize, 1) # skip partition

    token_key = None

    # inner function for dumping token to its proper bucket
    def _dump_token_to_bucket():
        nonlocal bucket_char
        nonlocal bucket_fh
        nonlocal bucket_seekfh
        nonlocal token_key
        codepoint = ord(token_key[0])
        first_char = '\u0080' if codepoint >= 128 else token_key[0]
        num_postings = 0
        token_val_mmap = bytearray()

        # make new bucket if first char doesn't match
        if bucket_char != first_char:
            bucket_char = first_char
            if bucket_fh:
                bucket_fh.close()
                bucket_seekfh.close()
            bucket_fh = open(f'{buckets_dir}/{codepoint}.bucket', 'wb')
            bucket_seekfh = open(f'{buckets_dir}/{codepoint}.seek', 'wb')

        # process value queue until it's empty
        while not val_queue.empty():
            # sequentially writes postings and keeps track of how many
            num_postings += 1
            posting = val_queue.get(block=False)
            token_val_mmap.extend(sposting_repr(posting))

        # append to seek file and bucket
        bucket_seekfh.write(sstr_repr(token_key))
        bucket_seekfh.write(u32_repr(bucket_fh.tell()))
        bucket_fh.write(u32_repr(num_postings))
        bucket_fh.write(token_val_mmap)

    # process key queue until it's empty
    while not key_queue.empty():
        token, pid = key_queue.get(block=False)
        if token != token_key:
            # dump token key, vals to bucket
            # if and only if a token is available
            if token_key:
                _dump_token_to_bucket()

            # update to next token
            tokencnt += 1
            token_key = token

        # add local token postings to value queue
        psize, pseekerfh = partseekers[pid]
        psize -= 4
        num_postings, _ = u32_rd(pseekerfh)
        for _ in range(num_postings):
            posting, posting_rdsize = sposting_rd(pseekerfh)
            psize -= posting_rdsize
            val_queue.put(posting, block=False)
            assert psize >= 0, "malformed partition in partial file"
        if psize > 0:
            # add next token to key queue (partition has data)
            token, token_rdsize = sstr_rd(pseekerfh)
            psize -= token_rdsize
            key_queue.put((token, pid), block=False)

        # update psize for current partseeker
        partseekers[pid] = (psize, pseekerfh)

    # final dump on token key, vals
    if token_key:
        _dump_token_to_bucket()

    # write merge info (32 bytes)
    mergeinfofh = open(merge_filename, 'wb')
    mergeinfofh.write(u8_repr(MERGE_VER))
    mergeinfofh.write(b'\0\0\0')
    mergeinfofh.write(u64_repr(docid))
    mergeinfofh.write(u32_repr(tokencnt))
    mergeinfofh.write(b'\0' * 16)
    mergeinfofh.close()

    # close temp file handlers
    for pseeker in partseekers:
        pseeker[1].close()
    if bucket_fh:
        bucket_fh.close()
        bucket_seekfh.close()

    return True # success


def update_doc_pr_quality(docinfo_filename, scores):
    """Writes the pr_quality field of specified
    documents based on the scores.

    :param scores dict[int, float]: Mapping of docid to float score
    """
    with open(docinfo_filename, 'r+b') as docfh:
        docfh.seek(0, 2)
        docfhend = docfh.tell()
        docfh.seek(0, 0)
        while docfh.tell() != docfhend:
            docid, _ = u64_rd(docfh)
            _, _ = u32_rd(docfh)

            # pr_quality
            score = scores.get(docid, None)
            if score != None:
                docfh.write(f32_repr(score))

            _, _ = f32_rd(docfh)
            _, _ = f32_rd(docfh)
            _, _ = sstr_rd(docfh)


def update_doc_hits_quality(docinfo_filename, scores):
    """Writes the hub_quality and auth_quality fields of
    specified document based on the scores.
    First score is interpreted as hub quality.
    Second score is interpreted as authority quality.

    :param scores dict[int, tuple]: Mapping of docid to 2-tuple float scores
    """
    with open(docinfo_filename, 'r+b') as docfh:
        docfh.seek(0, 2)
        docfhend = docfh.tell()
        docfh.seek(0, 0)
        while docfh.tell() != docfhend:
            docid, _ = u64_rd(docfh)
            _, _ = u32_rd(docfh)
            _, _ = f32_rd(docfh)

            # hub/auth_quality
            score = scores.get(docid, None)
            if score != None:
                docfh.write(f32_repr(score[0]))
                docfh.write(f32_repr(score[1]))

            _, _ = sstr_rd(docfh)


def write_summary(docid, summary, summary_fh):
    """Writes the summary directly to the summary file in a binary format.

    :param docid int: The document identifier
    :param summary str: The summary of the document
    :param summary_fh: The summary file handler
    """
    docid_bytes = u64_repr(docid)
    summary_bytes = sstr_repr(summary)

    summary_fh.write(docid_bytes)
    summary_fh.write(summary_bytes)

