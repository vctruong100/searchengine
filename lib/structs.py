# lib/structs.py
#
# helpers for reading/writing structs in binary files

def sstr_rd(fh):
    """read struct str
    """
    utf8_len = int.from_bytes(fh.read(4), byteorder='little', signed=False)
    return fh.read(utf8_len).decode('utf-8'), 4 + utf8_len


def sstr_repr(obj):
    """byte repr of struct str
    """
    utf8_enc = obj.encode('utf-8')
    utf8_len = len(utf8_enc)
    return utf8_len.to_bytes(4, byteorder='little', signed=False) + utf8_enc


def u8_rd(fh):
    """read u8
    """
    return int.from_bytes(fh.read(1), byteorder='little', signed=False), 1


def u8_repr(obj):
    """byte repr of u8
    """
    return obj.to_bytes(1, byteorder='little', signed=False)


def u32_rd(fh):
    """read u32
    """
    return int.from_bytes(fh.read(4), byteorder='little', signed=False), 4


def u32_repr(obj):
    """byte repr of u32
    """
    return obj.to_bytes(4, byteorder='little', signed=False)


def u64_rd(fh):
    """read u64
    """
    return int.from_bytes(fh.read(8), byteorder='little', signed=False), 8


def u64_repr(obj):
    """byte repr of u64
    """
    return obj.to_bytes(8, byteorder='little', signed=False)

