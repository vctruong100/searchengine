# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

# import query.abc
import sys
import math
import time
import webbrowser
import threading
import os
from nltk.stem import PorterStemmer
from collections import defaultdict
from indexlib.reader import DOCID_MAPPING, get_postings, get_url
from indexlib.process_query import process_query
from flask import Flask, request, render_template

app = Flask(__name__)

USAGE_MSG = "usage: python search.py"

@app.route("/", methods=["GET", "POST"])
def search():
    results = []
    query_time = 0
    if request.method == "POST":
        query = request.form.get("query")
        num_results = request.form.get("num_results")
        if not num_results:
            num_results = 5  # default value if not provided
        else:
            num_results = int(num_results)

        start_time = time.time_ns()
        results = process_query(query, num_results)
        end_time = time.time_ns()
        query_time = (end_time - start_time) / 1_000_000
    return render_template("search.html", results=results, query_time=query_time)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    # Check WERKZEUG_RUN_MAIN Environment Variable to ensure
    # that the server is only started once
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.25, open_browser).start()

    app.run(debug=True)
