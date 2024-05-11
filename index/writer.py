# index/writer.py
#
# writes to inverted index
# see index/spec

from os import dup


def _struct_str(s):
    """Encodes a string `s` to a byte sequence.
    struct str {
        u32 len;
        char[] buf;
    };
    """
    slen = len(s).to_bytes(
        4,
        byteorder="little",
        signed=False
    )
    sbuf = s.encode("utf-8")
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

        # append
        fh.seek(end_offset, 0)

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
    """Merges k-way using a sequence of partial indices from `partfh`.
    The output is written as a sequence of pages to `fh`.

    `partfh` must be seekable.

    If `partfh` and `fh` refer to the same file, merging behavior is undefined.

    """
    pass

