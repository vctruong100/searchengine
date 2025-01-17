# search.py
#
# accept user inputs from this machine and
# retrieves documents based on query

import time
import webbrowser
import threading
import os
import sys
from flask import Flask, request, render_template
from lib.queryproc import process_query, format_results_web
from lib.reader import initialize, initialize_summary
from lib.indexfiles import *

app = Flask(__name__)

USAGE_MSG = "usage: python search.py"

# https://flask.palletsprojects.com/en/3.0.x/
@app.route("/", methods=["GET", "POST"])
def search():
    results = []
    query_time = 0
    query = ""
    total_results = 0
    if request.method == "POST":
        query = request.form.get("query")
        num_results = request.form.get("num_results")

        all_results = False

        if num_results == "all":
            all_results = True
        else:
            num_results = int(num_results)

        start_time = time.time_ns()
        result = process_query(query)
        total_results = len(result)

        end_time = time.time_ns()
        results = format_results_web(result, num_results if not all_results else total_results, SUMMARY_NAME)
        query_time = (end_time - start_time) / 1_000_000
    return render_template('search.html', results=results, query_time=query_time, query=query, total_results=total_results)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print(USAGE_MSG)
        sys.exit(1)

    try:
        initialize(
            docinfo_filename=DOCINFO_NAME,
            mergeinfo_filename=MERGEINFO_NAME,
            buckets_dir=BUCKETS_DIR
        )

        initialize_summary(SUMMARY_NAME)  

    except Exception as e:
        print(f"Failed to initialize reader: {e}")
        sys.exit(1)

    # Check WERKZEUG_RUN_MAIN Environment Variable to ensure
    # that the server is only started once
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.25, open_browser).start()

    app.run(debug=True)
