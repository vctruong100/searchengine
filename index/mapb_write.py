# index/mapb_write.py
#
# writes the inverted index to a file
# each token consists of a list of Postings
# see "index/posting.py"
#
# version: 0
#
# list of supported types:
#   - i32 0x01
#       => { i32 val; };
#   - str 0x02
#       => { u32 len; char[] buf; };
#   - list[Posting] 0xC8
#       => { u32 len; Posting[] postings; }


def _encode_i32(i):
    """Returns the canonical byte sequence of the i32 value.
    See list of supported types.
    """
    seq = bytearray()
    seq.append(0x01)
    seq.extend(i.to_bytes(4, "little"))
    return bytes(seq)


def _encode_str(str):
    """Returns the canonical byte sequence of the str value.
    See list of supported types.
    """
    seq = bytearray()
    utf8_seq = str.encode("utf-8")
    seq.append(0x02)
    seq.extend(len(utf8_seq).to_bytes(4, "little", signed=False))
    seq.extend(utf8_seq)
    return bytes(seq)


def _encode_list_postings(postings):
    """Returns the canonical byte sequence of the list of postings.
    See list of supported types.
    """
    seq = bytearray()
    plen = len(postings)
    seq.append(0xC8)
    seq.extend(plen.to_bytes(4, "little", signed=False))
    for p in postings:
        seq.extend(p.encode())
    return bytes(seq)


def write_index(index, num_docs, fh):
    """Writes the index to file.
    Keys are sorted lexicographically.
    The index consists of tokens mapped to a list of Postings.

    :param index dict[str, list[Posting]]: The inverted index as a hash map
    :param num_docs int: The number of documents
    :param fh: The file handler
    """

    # Header chunk
    #   - version: 1 byte
    #   - [7 bytes reserved]
    #   - num_docs: 8 bytes
    #   - num_tokens: 8 bytes
    #   - refsize: 8 bytes
    #   - datasize: 8 bytes
    header_mmap = bytearray()
    header_mmap.append(0)
    header_mmap.extend(b"\0\0\0\0\0\0\0")
    header_mmap.extend(num_docs.to_bytes(8, "little"))
    header_mmap.extend(len(index.keys()).to_bytes(8, "little"))

    # Reference chunk
    # Sequence of key,value pairs
    #   - key: 8 bytes
    #       - data_offset: 4 bytes
    #       - data_size: 4 bytes
    #   - value: 8 bytes
    #       - data_offset: 4 bytes
    #       - data_size: 4 bytes
    ref_mmap = bytearray()

    # Data chunk
    # Sequence of arbitrary byte sequences
    #   - type: 1 byte
    #   - data: n bytes
    data_mmap = bytearray()
    data_offset = 0

    # Write data from the index hashmap
    # The words are sorted lexicographically.
    for word in sorted(index.keys()):
        # Append word as key
        word_seq = _encode_str(word)
        ref_mmap.extend(data_offset.to_bytes(4, "little"))
        ref_mmap.extend(len(word_seq).to_bytes(4, "little"))
        data_mmap.extend(word_seq)
        data_offset += len(word_seq)

        # Append list of postings as key
        postings_seq = _encode_list_postings(index[word])
        ref_mmap.extend(data_offset.to_bytes(4, "little"))
        ref_mmap.extend(len(postings_seq).to_bytes(4, "little"))
        data_mmap.extend(postings_seq)
        data_offset += len(postings_seq)

    # Finalize header data
    header_mmap.extend(len(ref_mmap).to_bytes(8, "little"))
    header_mmap.extend(len(data_mmap).to_bytes(8, "little"))

    # Write header, refs, and data chunks sequentially
    fh.write(header_mmap)
    fh.write(ref_mmap)
    fh.write(data_mmap)

