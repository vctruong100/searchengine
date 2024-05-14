# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys

USAGE_MSG = "usage: python search.py indexfile"


def run_server(path):
    """Runs the server as a long running process
    that constantly accepts user input (from the local machine).
    """
    print("path:", path)
    while True:
        query = input()
        # do query work
        print("received:", query)


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    run_server(path)

