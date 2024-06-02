# summarizer.py

import os
import sys
import time
import json
from transformers import pipeline
from bs4 import BeautifulSoup
from queue import PriorityQueue
from lib.structs import *

USAGE_MSG = "usage: python summarizer.py path/to/pages"

SUM_DIR = "summary"

PART_NAME = f"{SUM_DIR}/.part"
SUMMARY_NAME = f"{SUM_DIR}/.summary"

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def setup_dir():
    """Sets up the necessary directories for storing the index.
    """
    if not os.path.isdir(SUM_DIR):
        os.mkdir(SUM_DIR)

def summarize_text(text):
    """Generates a summary for the provided text using the BART model."""
    max_input_length = 512
    truncated_text = text[:max_input_length]
    summary = summarizer(truncated_text, max_length=60, min_length=20, length_penalty=2.0, num_beams=1, early_stopping=True)[0]['summary_text']
    return summary

def write_partial_summary(index, summaries, partfh):
    if not summaries:
        index.clear()
        return
    
    # Save current file offset
    part_end_offset = partfh.tell()
    
    # Read previous header values
    partfh.seek(2, 0)
    prev_docid, _ = u64_rd(partfh)
    prev_partcnt, _ = u32_rd(partfh)
    
    # Prepare byte arrays for buffered write
    part_mmap = bytearray()
    docid = None

    for docid, summary in summaries.items():
        # Encode summary and pad/truncate to 80 bytes
        summary_bytes = summary.encode('utf-8')[:80]
        summary_bytes = summary_bytes.ljust(80, b'\0')
        # Append docid and summary to byte array
        part_mmap.extend(u64_repr(docid))
        part_mmap.extend(summary_bytes)

    try:
        # Update header in the file
        partfh.seek(2, 0)
        partfh.write(u64_repr(docid))
        partfh.write(u32_repr(prev_partcnt + 1))
        
        # Write the buffered data to the file
        partfh.seek(part_end_offset, 0)
        partfh.write(u32_repr(len(part_mmap)))
        partfh.write(part_mmap)
        
        # Clear index and summaries
        index.clear()
        summaries.clear()
        return True
    except Exception as e:
        # Restore original state if write fails
        partfh.seek(2, 0)
        partfh.write(u64_repr(prev_docid))
        partfh.write(u32_repr(prev_partcnt))
        partfh.seek(part_end_offset, 0)
        partfh.truncate()
        raise e

def merge_partial_summaries(partfh, merge_filename):
    # Read partial header
    partfh.seek(2, 0)
    docid, _ = u64_rd(partfh)
    partcnt, _ = u32_rd(partfh)
    
    # Open final summary file for writing
    summary_fh = open(merge_filename, 'wb')

    partseekers = []
    key_queue = PriorityQueue(maxsize=partcnt)

    for pid in range(partcnt):
        # Read part size and position file handler
        partsize, _ = u32_rd(partfh)
        partseekerfh = open(partfh.name, 'rb')
        partseekerfh.seek(partfh.tell(), 0)
        if partsize > 0:
            # Read docid and summary bytes
            docid, docid_rdsize = u64_rd(partseekerfh)
            partseekers.append((partsize - docid_rdsize, partseekerfh))
            summary_bytes = partseekerfh.read(80)
            # Add to priority queue
            key_queue.put((docid, summary_bytes, pid), block=False)
        else:
            partseekers.append((partsize, partseekerfh))
        partfh.seek(partsize, 1)

    while not key_queue.empty():
        # Retrieve smallest docid entry
        docid, summary_bytes, pid = key_queue.get(block=False)
        summary_fh.write(u64_repr(docid))
        summary_fh.write(summary_bytes)

        # Update part seeker
        psize, pseekerfh = partseekers[pid]
        psize -= 88
        if psize > 0:
            next_docid, next_docid_rdsize = u64_rd(pseekerfh)
            next_summary_bytes = pseekerfh.read(80)
            partseekers[pid] = (psize - next_docid_rdsize, pseekerfh)
            key_queue.put((next_docid, next_summary_bytes, pid), block=False)

    # Close summary file and part seekers
    summary_fh.close()
    for pseeker in partseekers:
        pseeker[1].close()

def extract_text_from_html(html_content):
    """Extracts text from HTML content."""
    soup = BeautifulSoup(html_content, 'lxml')
    text = soup.get_text()
    cleaned_text = ' '.join(text.split())
    return cleaned_text

def process_directory(json_dir):
    setup_dir()

    docid = 0
    summary_metadata = {}
    partial_iter = 0
    partial_flush_period = 100

    partfh = open(PART_NAME, "w+b")

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
                            summary_metadata[docid] = summary
                            print(f"Document {docid}: {summary}")
                            if partial_iter % partial_flush_period == 0 and summary_metadata:
                                print(f"Flushing partial summary {partial_iter}...")
                                write_partial_summary(summary_metadata, summary_metadata, partfh)
                                summary_metadata.clear()
                                print(f"Partial summary {partial_iter} flushed.")
                            partial_iter += 1
                except Exception as e:
                    print(f"Failed to process {filename}: {e}")

    if summary_metadata:
        write_partial_summary(summary_metadata, summary_metadata, partfh)

    merge_partial_summaries(partfh, SUMMARY_NAME)
    partfh.close()

    print(f"Completed summarizing. Time elapsed: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(USAGE_MSG)
        sys.exit(1)
    
    json_dir = sys.argv[1]
    
    print("Summarizing documents...")
    process_directory(json_dir)
