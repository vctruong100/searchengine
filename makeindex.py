# makeindex.py
#
# constructs an index file
# from a collection of web pages
#
# usage: python makeindex.py pages/ outputfile

import os
import sys

USAGE_MSG = "usage: python makeindex.py pages/ outputfile"


def main(dir, fh):
    """Makes the index from a collection of
    cached pages recursively from the directory (dir).
    Writes the output to the file handler (fh).

    :param dir str: The directory
    :param fh: The output file handler

    """
    # read json files from directory and write to output file
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    fh.write(f.read())

if __name__ == "__main__":
    try:
        dir = sys.argv[1]
        assert os.path.isdir(dir), USAGE_MSG
        fh = open(sys.argv[2], "w", encoding="utf-8")
    except:
        print(USAGE_MSG)
        sys.exit(1)

    main(dir, fh)

