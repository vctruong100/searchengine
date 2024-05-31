# Spec
This spec describes the various file formats used in the inverted index. While 
the formats are implemented in `lib/reader.py` and `lib/writer.py`, the spec 
exists to document the file format in an accessible form.

## Standard structs
These are standard structs that are shared throughout the file formats:
- `struct str` shows how strings are stored in the files
- `struct posting` / `Posting` is the implementation defined in `lib/posting.py`
- `struct document` / `Document` is the implementation defined in `lib/document.py`

Below are the struct definitions:

```c
struct str {
    u32 len;
    char *buf;
}; /* utf-8 encoded */

typedef struct posting {
    u64 docid;
    u32 tf;             // term frequency
    u32 fields_bits;    // fields as a bitfield (array of booleans)
} Posting;

typedef struct document {
    u64 docid;
    u32 total_tokens;
    struct str url;
} Document;

```

## Partial
This is a container file that consists of partial indices. Each partition sorts 
its token pairs by token. Below are the struct definitions that define the 
entire format:

```c
struct tp_pair;
struct partial_header;
struct partition;

struct partial {
    struct partial_header header;
    struct partition *partitions;
}; /* this is the actual format */

struct partial_header {
    u8 version;
    u8 is_complete;             // whether partial is complete
    u64 docid;                  // last docid
    u32 partcnt;                // number of partitions
};

struct partition {
    u64 pairs_size;             // how many bytes "pairs" consumes
    struct tp_pair *pairs;
};

struct tp_pair {
    struct str token;
    u32 num_postings;
    Posting *postings;
};

```

## Docinfo
This is a file that conists of only a sequence of documents. Below are the 
struct definitions that define the entire format:

```c
struct docinfo {
    Document *documents;
}; /* this is the actual format */

```

## Mergeinfo
This is a file that contains details about the merging of the partial container. 
Below are the struct definitions that define the entire format:

```c
struct mergeinfo {
    u8 version;
    u8 reserved_00[3];      // RESERVED: 3 bytes
    u64 docid;              // last docid
    u32 tokencnt;           // number of tokens in the entire index
    u8 reserved_01[16];     // RESERVED: 16 bytes
}; /* this is the actual format */

```

## Buckets
Buckets are stored as 2 separate files: the data and its seek file.

- The data file stores sequences of postings lists, where each correspond to the 
second component of `struct tp_pair` in the partial container.

- The seek file stores sequences of tokens paired with their data file offsets 
which point to their corresponding postings list. This corresponds to the first 
component of `struct tp_pair` in the partial container.

Below are the struct definitions that encompass both formats:

### Datafile

```c
struct postings_list;

struct bucket_data {
    struct postings_list *postings_sequence;
}; /* this is the actual format */

struct postings_list {
    u32 num_postings;
    Posting *postings;
};

```

### Seekfile

```c
struct seeker;

struct bucket_seek {
    struct seeker *seekers;
}; /* this is the actual format */

struct seeker {
    struct str token;
    u32 offset;             // the data file offset
};

```

