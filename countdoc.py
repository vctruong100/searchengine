import os
import sys
from json import load
import time

USAGE_MSG = "python countdoc.py path/to/pages/"

def count_doc(dir):
    docID = 0
    COUNT_START = time.time_ns()
    for root, _, files in os.walk(dir, 'r'):
        for file in files:
            if file.endswith('.json'):
                actual_path = os.path.join(root, file)
                f = open(actual_path, 'r', encoding='utf-8')
                docID += 1
                print(f"doc {docID}", file=sys.stderr)
                js = load(f)
                url = js.get('url','')
                print(f"{docID},{url}")

                f.close()

                #if docID == 16946:
                #    with open("doc/16946.txt", 'w', encoding='utf-8') as f2:
                #        print(js.get('content', ''), file=f2)
    COUNT_END = time.time_ns()
    print("time taken:", COUNT_END - COUNT_START, file=sys.stderr)

if __name__ == "__main__":
    try:
        dir = sys.argv[1]
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    stdout_redirect = open("countdoc", "w", encoding="utf-8")
    sys.stdout = stdout_redirect

    count_doc(dir)
