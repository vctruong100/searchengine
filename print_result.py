# print_result.py
#
# print the result of the index file (merged)
#
# usage: python print_result.py indexfile

import sys
import os
from index.writer import _get_header

USAGE_MSG = "usage: python print_result.py indexfile"

def print_result(indexfile):
    """Prints the result of the index file (merged).

    :param indexfile str: The index file

    """
    try:
        with open(indexfile, 'r') as fh:
            partcnt, docid = _get_header(fh)
            # Read the keycnt field from the merged index file to get the number of unique words
            fh.seek(16)

            # convert the read bytes to an unsigned integer
            # byteorder="little" - data is stored in little-endian format, least significant byte (the "little end") comes first
            keycnt = int.from_bytes(fh.read(8), byteorder="little", signed=False)
            print(f"Number of unique words: {keycnt}")
            print(f"Number of documents: {docid}")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

    file_size = os.path.getsize(indexfile) / 1024
    print(f"Size of index file: {file_size:.2f} KB")

if __name__ == "__main__":
    try:
        indexfile = sys.argv[1]
        assert os.path.isfile(indexfile), USAGE_MSG
    except Exception as e:
        print(USAGE_MSG)
        print("Error:", e)
        sys.exit(1)

    print_result(indexfile)