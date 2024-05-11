# index/writer.py
#
# writes to inverted index
# see index/spec

from queue import PriorityQueue
from index.posting import Posting


def _struct_str(s):
    """Encodes a string `s` to a byte sequence.
    struct str {
        u32 len;
        char[] buf;
    };
    """
    sbuf = s.encode("utf-8")
    slen = len(sbuf).to_bytes(
        4,
        byteorder="little",
        signed=False
    )
    return slen + sbuf


def _get_header(fh):
    """Get header information from `fh`.
    Returns the partial count and highest docid as a tuple.
    """
    fh.seek(0, 0)
    partcnt = int.from_bytes(
        fh.read(4),
        byteorder="little",
        signed=False,
    )
    docid = int.from_bytes(
        fh.read(8),
        byteorder="little",
        signed=False
    )
    return (partcnt, docid)


def write_partial_index(index, docid, fh):
    """Appends the partial inverted index to `fh`.
    The index is cleared when the index is successfully written to.
    Returns True if and only if this function succeeds.

    `fh` must be seekable.

    If the index fails to write, then (1) the file is reverted to its original
    state, (2) the index is not cleared, (3) the function propagates the exception.

    :param index dict[str, list[Posting]]: The inverted index
    :param docid int: The last docID within this partial index.
    :param fh: The file handler
    :return: Whether the function succeeded
    :rtype: bool
    """
    assert fh.seekable(), "file is not seekable"

    end_offset = fh.tell()

    # store previous header values
    partcnt, prev_docid = _get_header(fh)

    try:
        part_mmap = bytearray()

        # update header
        fh.seek(0, 0)
        fh.write((partcnt + 1).to_bytes(
            4,
            byteorder="little",
            signed=False
        ))
        fh.write(docid.to_bytes(
            8,
            byteorder="little",
            signed=False
        ))

        # append either at the last file position or end of header
        # whichever comes last
        fh.seek(max(end_offset, 12), 0)

        # encode key value pairs
        # the keys are sorted lexicographically
        for key in sorted(index.keys()):
            part_mmap.extend(_struct_str(key))

            postings_mmap = bytearray()
            for p in index[key]:
                postings_mmap.extend(p.encode())

            part_mmap.extend(len(postings_mmap).to_bytes(
                4,
                byteorder="little",
                signed=False
            ))
            part_mmap.extend(postings_mmap)

        # write data
        fh.write(len(part_mmap).to_bytes(
            4,
            byteorder="little",
            signed=False
        ))
        fh.write(part_mmap)

        # clear index and mark as success
        index.clear()
        return True
    except Exception as e:
        fh.seek(0, 0)
        fh.write(partcnt.to_bytes(
            4,
            byteorder="little",
            signed=False
        ))
        fh.write(prev_docid.to_bytes(
            8,
            byteorder="little",
            signed=False
        ))
        fh.seek(end_offset, 0)
        fh.truncate(end_offset)
        raise e


def merge_index(partfh, fh):
    """Merges k-way using a sequence of partial sorted indices from `partfh`.
    The output is written to `fh` as a merged key-value map that is sorted.

    `partfh` must be seekable.
    `fh` must be seekable.

    If `partfh` and `fh` refer to the same file, merging behavior is undefined.

    Returns True if it succeeds.
    """
    assert partfh.seekable(), "partfh is not seekable"
    assert fh.seekable(), "fh is not seekable"

    partcnt, docid = _get_header(partfh)

    # reserve 32 bytes for header
    fh.seek(32, 0)

    # internal header variables
    keycnt = 0

    # different file handlers for each partial index
    # each element is a 2-tuple: (size, fh)
    indices = []

    # key priority queue
    key_pq = PriorityQueue(maxsize=partcnt)

    # val priority queue
    # for use in determining the
    # min element within the list of Postings
    val_pq = PriorityQueue()

    # create file handlers for each partial index on disk
    for i in range(partcnt):
        map_size = int.from_bytes(
            partfh.read(4),
            byteorder="little",
            signed=False
        )
        map_fh = open(partfh.name, "rb")
        map_fh.seek(partfh.tell(), 0)
        if map_size > 0:
            indices.append((map_size, map_fh))
        partfh.seek(map_size, 1)

    # initialize key priority queue
    for ipos in range(len(indices)):
        map_size, map_fh = indices[ipos]
        ksize = int.from_bytes(
            map_fh.read(4),
            byteorder="little",
            signed=False
        )
        key = map_fh.read(ksize).decode("utf-8")
        indices[ipos] = (map_size - 4 - ksize, map_fh)
        key_pq.put(
            (key, ipos),
            block=False
        )

    # empty the key priority queue
    data_key = None
    data_mmap = bytearray()
    while not key_pq.empty():
        key, ipos = key_pq.get(block=False)

        if key != data_key:
            if data_key:
                # write the key-val pair to disk before
                # changing the key reference
                fh.write(_struct_str(data_key))
                while not val_pq.empty():
                    posting = val_pq.get(block=False)
                    data_mmap.extend(posting.encode())
                fh.write(len(data_mmap).to_bytes(
                    4,
                    byteorder="little",
                    signed=False
                ))
                fh.write(data_mmap)

            # update references
            data_key = key
            data_mmap = bytearray()
            keycnt += 1

        # read list of Postings for this particular index
        map_size, map_fh = indices[ipos]

        plsize = int.from_bytes(
            map_fh.read(4),
            byteorder="little",
            signed=False
        )
        indices[ipos] = (map_size - 4 - plsize, map_fh)
        map_size = indices[ipos][0]

        while plsize > 0:
            pbytes = map_fh.read(Posting.size)
            posting = Posting()
            posting.decode(pbytes)
            val_pq.put(
                posting,
                block=False
            )
            plsize -= Posting.size

        # append the next key to the key priority queue
        # for this particular index, if it exists
        if map_size <= 0:
            continue
        ksize = int.from_bytes(
            map_fh.read(4),
            byteorder="little",
            signed=False
        )
        key = map_fh.read(ksize).decode("utf-8")
        indices[ipos] = (map_size - 4 - ksize, map_fh)
        key_pq.put(
            (key, ipos),
            block=False
        )

    # write the final key value pair to disk, if it exists
    if data_key:
        fh.write(_struct_str(data_key))
        while not val_pq.empty():
            posting = val_pq.get(block=False)
            data_mmap.extend(posting.encode())
        fh.write(len(data_mmap).to_bytes(
            4,
            byteorder="little",
            signed=False
        ))
        fh.write(data_mmap)

    # update and write headers
    # then mark as success
    header_mmap = bytearray()
    header_mmap.append(0)
    header_mmap.extend(b"\0\0\0\0\0\0\0")
    header_mmap.extend(docid.to_bytes(
        8,
        byteorder="little",
        signed=False
    ))
    header_mmap.extend(keycnt.to_bytes(
        8,
        byteorder="little",
        signed=False
    ))
    fh.seek(0, 0)
    fh.write(header_mmap)
    return True


