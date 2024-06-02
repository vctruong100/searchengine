# summarizer.py

import os
import sys
import time
import json
from transformers import pipeline
from bs4 import BeautifulSoup
from queue import PriorityQueue
from lib.structs import *
from lib.indexfiles import *
from lib.writer import write_summary

USAGE_MSG = "usage: python summarizer.py path/to/pages"

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def setup_dir():
    """Sets up the necessary directories for storing the index.
    """
    if not os.path.isdir(INDEX_DIR):
        os.mkdir(INDEX_DIR)

def summarize_text(text):
    """Generates a summary for the provided text using the BART model."""
    max_input_length = 512
    truncated_text = text[:max_input_length]
    summary = summarizer(truncated_text, max_length=60, min_length=20)[0]['summary_text']
    return summary

def extract_text_from_html(html_content):
    """Extracts text from HTML content."""
    soup = BeautifulSoup(html_content, 'lxml')
    text = soup.get_text()
    cleaned_text = ' '.join(text.split())
    return cleaned_text

def process_directory(json_dir):
    setup_dir()

    docid = 0
    summary_fh = open(SUMMARY_NAME, "ab")

    for root, _, files in os.walk(json_dir):
        for filename in files:
            if filename.endswith('.json'):
                docid += 1
                path = os.path.join(root, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as pagefh:
                        jsond = json.load(pagefh)
                        content = jsond.get('content', '').strip()
                        if content:
                            text = extract_text_from_html(content)

                            start_time = time.time()
                            summary = summarize_text(text)

                            print(f"Time elapsed for document {docid}: {time.time() - start_time:.2f} seconds")
                            print(f"Document {docid}: {summary}")

                            write_summary(docid, summary, summary_fh)

                except Exception as e:
                    print(f"Failed to process {filename}: {e}")

    summary_fh.close()

    print(f"Completed summarizing. Time elapsed: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(USAGE_MSG)
        sys.exit(1)
    
    json_dir = sys.argv[1]
    
    print("Summarizing documents...")
    process_directory(json_dir)
