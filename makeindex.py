# makeindex.py
#
# constructs an index file
# from a collection of web pages
#
# usage: python makeindex.py [--keep-partial | -p] path/to/pages

import os
import sys
import time
import itertools

from bs4 import BeautifulSoup
from collections import defaultdict # simplify and speed up Posting insertion
from collections import deque
from json import load
from nltk.stem import PorterStemmer
from hashlib import sha256
from urllib.parse import urldefrag, urljoin

from lib.duphash import * # similar / exact hashing from scratch
from lib.tokenize import *
from lib.word_count import word_count
from lib.posting import Posting
from lib.writer import *
from lib.indexfiles import * # constants for index paths

USAGE_MSG = "usage: python makeindex.py [--keep-partial | -p] path/to/pages"


def setup_dir():
    """Sets up the necessary directories for storing the index.
    """
    if not os.path.isdir(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not os.path.isdir(BUCKETS_DIR):
        os.mkdir(BUCKETS_DIR)


def clean_index_metainfo():
    """Cleans metainfo from the index
    """
    if os.path.isfile(DOCINFO_NAME):
        os.remove(DOCINFO_NAME)
    if os.path.isfile(DOCLINKS_NAME):
        os.remove(DOCLINKS_NAME)


def make_partial(pagedir, partfh, partdoc):
    """Uses JSON files from within `pagedir` and writes the
    partial index to `partfh` starting from doc ID `partdoc` + 1.
    """

    start_time = time.time()

    if partdoc == 0:
        partfh = new_partial(fh=partfh) # restart partial file
    partfh.seek(0, 2) # start from end

    docid = 0
    docfh = open(DOCINFO_NAME, 'ab')
    doclinksfh = open(DOCLINKS_NAME, 'ab')

    stemmer = PorterStemmer()
    inverted_index = defaultdict(list)
    docs = []

    # USED FOR DETECTING DUPLICATE PAGES
    # NOTE: this resets if makeindex is interrupted
    urls_found = set()
    exact_hashes = set()
    similar_hashes = deque() # use a deque to pop old similar hashes

    # consider only the most recent similar hashes
    # the idea is that as similar hashes accumulate, they start to
    # slow down the indexing processing due to the need to compare
    # against every hash
    max_similar_hashes = 200

    # number of documents eliminated
    # by duplicate detection (exact / similar / duplicate URL)
    # or empty content
    #
    # note: pruned docs resets if makeindex is interrupted
    pruned_docs = 0

    # periodic flushing of the partial index to disk
    # these variables keep track of this
    partial_iter = 0
    partial_flush_period = 100


    # recursively walk the pages directory
    for root, _, files in os.walk(dir):
        for file in files:
            # Periodically writes partial index to disk
            # if and only if docs is non-empty
            # Note: This does not advance iterations if a flush is due
            if partial_iter % partial_flush_period == 0 and docs:
                write_partial(inverted_index, docs, partfh, docfh, doclinksfh)
                print(f"partial flush @ docID: {docid} ; pruned={pruned_docs}", flush=True)
            partial_iter += 1

            # consider JSON files only
            if file.endswith(".json"):
                # Note: Whenever a document is skipped (as duplicate or empty content):
                # docid still counts towards that document,
                # but the document will be empty (effectively removed from the index)
                docid += 1
                if docid <= partdoc:
                    continue # already written; skip

                ### Read JSON file ###

                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as pagefh:
                    jsond = load(pagefh)
                    content = jsond.get('content', '').strip()
                    url = urldefrag(jsond.get('url', ''))

                if not content:
                    pruned_docs += 1
                    continue # empty content; skip

                # url duplicates after defragging?
                if url in urls_found:
                    continue # url exists (after defragging)
                urls_found.add(url) # add to urls found set to ensure no duplicate urls


                ### Detection of duplicate pages (EXACT) ###
                ###
                ### Note: We can determine exactness quickly by the content hash
                ### However, we can't determine similarity yet unless we tokenize and count the words
                ### Similarity is deferred after we do content extraction!!!!

                # exact hashing
                # if content matches, then skip the document
                content_exact_hash = exact_hash(content)
                if content_exact_hash in exact_hashes:
                    continue
                exact_hashes.add(content_exact_hash) # add exact hash if no duplicates


                ### Content Extraction ###
                ###
                ### Extract content using bs4
                ### This extracts regular test / important text
                ### After extraction, memory used by soup is freed by decomposition

                # soupify content
                soup = BeautifulSoup(content, 'lxml')
                important_tokens = set()

                # extract regular text
                text = soup.get_text()
                tokens, ngrams_col = tokenize(text, n=1)
                text = "" # possibly free up memory

                # extract important text
                #
                # bold text, headings up to h4 (h4 is similar to bold)
                # and mark (highlighted) text
                important_tags = soup.find_all([
                    'h1', 'h2', 'h3', 'h4',
                    'b', 'strong', 'mark', 'title',
                ])
                for itag in important_tags:
                    important_text = itag.get_text()
                    important_tokens.update(tokenize(important_text, n=1)[0])
                    important_text = "" # possibly free up memory

                # extract links
                #
                # store them as a list of adjacent edges
                # these are storred as defragged URLs
                #
                # these are used to determine the static quality score (hits or pagerank)
                doclinks = set()
                for link in soup.find_all('a', href=True):
                    link = urljoin(url.url, link['href'])
                    defragged_link = urldefrag(link).url
                    doclinks.add(defragged_link)

                # free up memory from soup
                soup.decompose()


                ### Detect duplicate pages (SIMILAR) ###
                ###
                ### Note: Similarity is placed here so that we can
                ### use the word counts (token_counts)

                # similar hashing
                # if content is close to one of the hashes,
                # then skip the document
                is_sim = False
                content_similar_hash = similar_hash(word_count(tokens)) # this does not include n-grams if tokenize n=3
                for hash in similar_hashes:
                    if is_similar(content_similar_hash, hash):
                        is_sim = True
                        break
                if is_sim:
                    pruned_docs += 1
                    continue # similar to one of the indexed pages/docs

                # add similar hash if no similars iff there are few similar hashes
                similar_hashes.append(content_similar_hash)
                if len(similar_hashes) > max_similar_hashes:
                    similar_hashes.popleft() # remove oldest sim hash if too many

                ### Populate postings and documents
                ### if and only if the page is not a duplicate (exact, similar)


                # manipulate tokens
                extend_tokens_from_ngrams(tokens, ngrams_col)
                stem_tokens(tokens)

                token_counts = word_count(tokens)
                total_tokens = len(token_counts.items())


                # Iterate over each token and its count and add a Posting to the inverted index
                for token, count in token_counts.items():
                    # tf = term frequency of each individual token
                    posting = Posting(
                        docid=docid,
                        tf=count,
                        important=token in important_tokens,
                    )
                    inverted_index[token].append(posting)

                # append doc to docinfo
                # (docid, total_tokens, url)
                docs.append(Document(
                    docid=docid,
                    url=url.url,
                    total_tokens=total_tokens,
                    links=doclinks,
                ))


    # Final write for any remaining documents
    if inverted_index:
        write_partial(inverted_index, docs, partfh, docfh, doclinksfh)
        print(f"final flush @ docID: {docid} ; pruned={pruned_docs}", flush=True)
    mark_partial(partfh)

    end_time = time.time()  # Capture the end time of the indexing process
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Elapsed time of indexing: {elapsed_time:.2f} seconds")

    # close temp file pointers from this function
    docfh.close()


def make_final(partfh):
    """Merges the partial index from `partfh` into buckets
    based on the first char of the tokens.
    """
    start_time = time.time()  # Capture the start time of the merging process
    partfh.seek(0, 0)  # Move the file pointer to the beginning of the file
    try:
        merge_partial(partfh, MERGEINFO_NAME, BUCKETS_DIR)
    except Exception as e:
        raise e
        print(f"An error occurred during merging: {e}")
        sys.exit(1)
    end_time = time.time()  # Capture the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f"Elapsed time of merging: {elapsed_time:.2f} seconds")


def main(dir, keep_partial):
    """Makes the index from a collection of cached pages
    recursively from the directory (dir).

    :param dir str: The directory
    :param keep_partial bool: Whether partial file should be kept

    """
    # setup necessary directories
    setup_dir()

    # setup partial index
    partok = True
    partdoc = 0
    partfh = None

    if not os.path.isfile(PART_NAME):
        partfh = open(PART_NAME, "w+b")
        partok = False
        clean_index_metainfo() # clean up metainfo
        print("Missing partial index file. Indexing the pages.", flush=True)
    else:
        partfh = open(PART_NAME, "r+b")
        chk_p_status, partheader = check_partial(partfh)
        partok = (chk_p_status == CHK_P_OK)
        if chk_p_status == CHK_P_VER_MISMATCH:
            clean_index_metainfo() # clean up metainfo
            print("Partial index is outdated. Indexing the pages from scratch.", flush=True)
        elif chk_p_status == CHK_P_INCOMPLETE:
            partdoc, _ = partheader
            print(f"Partial index is incomplete. Continuing from doc ID {partdoc + 1}.", flush=True)

    # reset partial cursor in case it moved
    partfh.seek(0, 0)

    # if partial index file is not ready, index the pages
    if not partok:
        make_partial(dir, partfh, partdoc)

    # Merge the partial index files
    print("Merging partial index files...", flush=True)
    make_final(partfh)

    partfh.close()
    if not keep_partial:
        os.remove(PART_NAME)  # Delete the temporary partial index file



if __name__ == "__main__":
    argc = len(sys.argv)
    if argc <= 1:
        print(USAGE_MSG)
        sys.exit(1)

    dir = None
    keep_partial = False
    dirarg = 1

    # optional arg: keep partial
    if sys.argv[dirarg] == "--keep-partial" or sys.argv[dirarg] == "-p":
        # keep partial file
        keep_partial = True
        dirarg += 1

    try:
        dir = sys.argv[dirarg]
        assert os.path.isdir(dir), USAGE_MSG
    except Exception as e:
        print(USAGE_MSG)
        sys.exit(1)

    main(dir, keep_partial)

