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

    try:
        with open(indexfile, 'rb') as fh:
            fh.seek(8)  # Read the docID field from the merged index file
            docid = int.from_bytes(fh.read(8), byteorder="little", signed=False)

            # Read the keycnt field from the merged index file to get the number of unique words
            fh.seek(16)
            keycnt = int.from_bytes(fh.read(8), byteorder="little", signed=False)
            print(f"Number of unique words: {keycnt}")
            print(f"Number of documents: {docid}")

            file_size = os.path.getsize(indexfile) / 1024
            print(f"Size of index file: {file_size:.2f} KB")
    except FileNotFoundError:
        print(f"Error: File '{indexfile}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    indexfile = "index/merged_index"
    print_result(indexfile)