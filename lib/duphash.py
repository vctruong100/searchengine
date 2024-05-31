# lib/duphash.py
#
# exact / similar hashing
# implemented from scratch

### CRC 32 implementation (FROM SCRATCH)
### used for quick exact hashes

_CRC32_POLY = 0xedb88320 # reversed (LSB first; little endian)
_CRC32_LOOKUP = [0] * 256 # allocate 256 entries

# pre-compute byte lookup table (CRC-32)
for i in range(0x00, 0x100):
    val = i
    for _ in range(8):
        if 1 == (val & 1):
            # LSB set
            val >>= 1
            val ^= _CRC32_POLY
        else:
            val >>= 1
    _CRC32_LOOKUP[i] = val


def _crc32(bytes):
    """Computes a cyclic redundancy check of 32 bits.
    Returns the hash value as an unsigned 32-bit integer.

    :param bytes: A bytes or bytearray object
    :return: A crc32 remainder (a 32 bit integer)
    :rtype: int
    """
    crc = 0xFFFFFFFF
    for b in bytes:
        crc ^= b
        i = crc & 0xFF
        # after dividing, the first 8 bits are zeroed
        crc = (crc >> 8) ^ _CRC32_LOOKUP[i]
    return crc ^ 0xFFFFFFFF


### CRC 64 implementation (FROM SCRATCH)
### used in similar hashing as a hash for the words

_CRC64_POLY = 0xc96c5795d7870f42 # reversed (LSB first; little endian)
_CRC64_LOOKUP = [0] * 256 # allocate 256 entries

# pre-compute byte lookup table (CRC-64)
for i in range(0x00, 0x100):
    val = i
    for _ in range(8):
        if 1 == (val & 1):
            # LSB set
            val >>= 1
            val ^= _CRC64_POLY
        else:
            val >>= 1
    _CRC64_LOOKUP[i] = val


def _crc64(bytes):
    """Computes a cyclic redundancy check of 64 bits.
    Returns the hash value as an unsigned 64-bit integer.

    :param bytes: A bytes or bytearray object
    :return: A crc64 remainder (a 64 bit integer)
    :rtype: int
    """
    crc = 0xFFFFFFFFFFFFFFFF
    for b in bytes:
        crc ^= b
        i = crc & 0xFF
        # after dividing, the first 8 bits are zeroed
        crc = (crc >> 8) ^ _CRC64_LOOKUP[i]
    return crc ^ 0xFFFFFFFFFFFFFFFF


### EXACT HASHING (FROM SCRATCH)

def exact_hash(content):
    """Exact hashing using crc-32 (implemented from SCRATCH)
    and a discriminator (length in bytes). The discriminator
    is more of a safeguard against possible (but rare) collisions.

    :param content: The content as text or bytes
    :return: The hash from exact hashing

    """
    if type(content) == str:
        content = content.encode('utf-8') # encode str to utf-8
    crc_hash = _crc32(content)
    return crc_hash.to_bytes(4, 'little') + len(content).to_bytes(4, 'little')


### SIMILAR HASHING (FROM SCRATCH)

def _hamming_distance(hash1, hash2):
    """Computes the hamming distance between two hashes.
    This means the number of bits that are different between the two hashes.
    """
    distance = 0
    for i in range(len(hash1)):
        if hash1[i] != hash2[i]:
            distance += 1
    return distance


def similar_hash(wordcnts):
    """Similar hashing using the simhash algorithm as specified in the course notes.
    The words are hashed using crc64 (implemented from SCRATCH), which means
    the max hash size is 64. Here, we set the hash size to 32.

    :param wordcnts: The word counts
    :return: The fingerprint from similar hashing

    """
    # Size of the hash vector
    hash_size = 32 # MAX: 64 because of crc64
    v = [0] * hash_size

    for word, cnt in wordcnts.items():
        # Create binary hash of the word
        word_hash = crc64(word.encode("utf-8")) % (2 ** hash_size)
        binary_hash = format(word_hash, f'0{hash_size}b')

        # Update the simhash fingerprint
        for i in range(hash_size):
            bit_value = 1 if binary_hash[i] == '1' else -1
            v[i] += bit_value * cnt # update the vector with the word count multiplied by the bit value (1/0)

    # Form simhash fingerprint by converting the vector to a binary string
    fingerprint = ''.join(['1' if i > 0 else '0' for i in v]) # append 1 if positive or 0 otherwise

    return fingerprint


def is_similar(hash1, hash2):
    """Determines similarity by hamming distance.
    Threshold is set to at most 3.
    """
    return _hamming_distance(hash1, hash2) <= 3

