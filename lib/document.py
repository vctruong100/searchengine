# lib/document.py
#
# document class

from lib.structs import *

class Document:
    def __init__(
        self,
        docid=None,
        url=None,
        total_tokens=None,
        quality=0.0,
        links=None,
    ):
        self.docid = docid
        self.url = url
        self.total_tokens = total_tokens
        self.quality = quality
        self.links = links # not included in struct document

def sdocument_rd(fh):
    """read struct document
    """
    docid, _ = u64_rd(fh)
    total_tokens, _ = u32_rd(fh)
    quality, _ = f32_rd(fh)
    url, url_rdsize = sstr_rd(fh)
    return Document(
        docid=docid,
        url=url,
        total_tokens=total_tokens,
        quality=quality
    ), 16 + url_rdsize


def sdocument_repr(obj):
    """byte repr of struct document
    """
    docid = obj.docid
    url = obj.url
    total_tokens = obj.total_tokens
    quality = obj.quality

    seq = bytearray()

    seq.extend(u64_repr(docid))
    seq.extend(u32_repr(total_tokens))
    seq.extend(f32_repr(quality))
    seq.extend(sstr_repr(url))

    return bytes(seq)

