# print_result.py
#
# print the result of the index file (merged)
#
# usage: python print_result.py indexfile

import sys
import os

USAGE_MSG = "usage: python print_result.py indexfile"

def print_result(indexfile):
    """Prints the result of the index file (merged).

    :param indexfile str: The index file

    """

    with open(indexfile, 'rb') as fh:

        fh.seek(8) # Read the docID field from the merged index file
        docid = int.from_bytes(fh.read(8), byteorder="little", signed=False)

        # Read the keycnt field from the merged index file to get the number of unique words
        fh.seek(16)

        # convert the read bytes to an unsigned integer
        # byteorder="little" - data is stored in little-endian format, least significant byte (the "little end") comes first
        keycnt = int.from_bytes(fh.read(8), byteorder="little", signed=False)
        print(f"Number of unique words: {keycnt}")
        print(f"Number of documents: {docid}")

    file_size = os.path.getsize(indexfile) / 1024
    print(f"Size of index file: {file_size:.2f} KB")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(USAGE_MSG)
        sys.exit(1)

    indexfile = sys.argv[1]

    if not os.path.isfile(indexfile):
        print(f"Error: File '{indexfile}' does not exist.")
        sys.exit(1)

    print_result(indexfile)