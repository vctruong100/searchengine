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
        links=None,
        empty=False,
        pr_quality=1.0,
        hub_quality=1.0,
        auth_quality=1.0,
    ):
        self.docid = docid
        self.url = url
        self.total_tokens = total_tokens
        self.links = links # not included in struct document
        self.empty = empty # not included in struct document
        self.pr_quality = pr_quality
        self.hub_quality = hub_quality
        self.auth_quality = auth_quality


def sdocument_rd(fh):
    """read struct document
    """
    docid, _ = u64_rd(fh)
    total_tokens, _ = u32_rd(fh)
    pr_quality, _ = f32_rd(fh)
    hub_quality, _ = f32_rd(fh)
    auth_quality, _ = f32_rd(fh)
    url, url_rdsize = sstr_rd(fh)
    return Document(
        docid=docid,
        url=url,
        total_tokens=total_tokens,
        pr_quality=pr_quality,
        hub_quality=hub_quality,
        auth_quality=auth_quality,
    ), 24 + url_rdsize


def sdocument_repr(obj):
    """byte repr of struct document
    """
    docid = obj.docid
    url = obj.url
    total_tokens = obj.total_tokens
    pr_quality = obj.pr_quality
    hub_quality = obj.hub_quality
    auth_quality = obj.auth_quality

    seq = bytearray()

    seq.extend(u64_repr(docid))
    seq.extend(u32_repr(total_tokens))
    seq.extend(f32_repr(pr_quality))
    seq.extend(f32_repr(hub_quality))
    seq.extend(f32_repr(auth_quality))
    seq.extend(sstr_repr(url))

    return bytes(seq)

