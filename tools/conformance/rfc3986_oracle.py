"""A strict reference implementation of RFC 3986, used as a test oracle.

* Validation compiles the Appendix A ABNF to regular expressions, extended
  to IRIs by RFC 3987 section 2.2.  Input is never preprocessed, so
  whitespace, backslashes and other characters outside the grammar make it
  invalid.
* An IRI is mapped to a URI by RFC 3987 section 3.1: a non-ASCII host with
  the RFC 5895 mapping and IDNA2008 (RFC 5891), everything else by
  percent-encoding its UTF-8.  Unlike UTS #46, RFC 5895 does not delete
  invisible code points such as U+200B, so a host with one is invalid.
* Resolution follows sections 5.2.2 (strict parser), 5.2.3, 5.2.4 and 5.3.
* Normalization follows section 6.2.2, plus the small scheme-based layer
  of section 6.2.3 (default ports, empty port, empty http path).
"""

import re
import unicodedata
from dataclasses import dataclass, replace

import idna

UNRESERVED = r"A-Za-z0-9\-._~"
SUB_DELIMS = r"!$&'()*+,;="
PCT = r"%[0-9A-Fa-f]{2}"
SCHEME = r"[A-Za-z][A-Za-z0-9+\-.]*"
DEC_OCTET = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])"
IPV4 = rf"{DEC_OCTET}\.{DEC_OCTET}\.{DEC_OCTET}\.{DEC_OCTET}"
H16 = r"[0-9A-Fa-f]{1,4}"
LS32 = rf"(?:{H16}:{H16}|{IPV4})"
IPV6 = (
    "(?:"
    rf"(?:{H16}:){{6}}{LS32}"
    rf"|::(?:{H16}:){{5}}{LS32}"
    rf"|(?:{H16})?::(?:{H16}:){{4}}{LS32}"
    rf"|(?:(?:{H16}:){{0,1}}{H16})?::(?:{H16}:){{3}}{LS32}"
    rf"|(?:(?:{H16}:){{0,2}}{H16})?::(?:{H16}:){{2}}{LS32}"
    rf"|(?:(?:{H16}:){{0,3}}{H16})?::{H16}:{LS32}"
    rf"|(?:(?:{H16}:){{0,4}}{H16})?::{LS32}"
    rf"|(?:(?:{H16}:){{0,5}}{H16})?::{H16}"
    rf"|(?:(?:{H16}:){{0,6}}{H16})?::"
    ")"
)
IPVFUTURE = rf"v[0-9A-Fa-f]+\.[{UNRESERVED}{SUB_DELIMS}:]+"
IP_LITERAL = rf"\[(?:{IPV6}|{IPVFUTURE})\]"


def _ranges(*pairs: tuple[int, int]) -> str:
    return "".join(f"{chr(first)}-{chr(last)}" for first, last in pairs)


# RFC 3987 section 2.2.
UCSCHAR = _ranges(
    (0xA0, 0xD7FF),
    (0xF900, 0xFDCF),
    (0xFDF0, 0xFFEF),
    *((plane << 16, (plane << 16) + 0xFFFD) for plane in range(1, 14)),
    (0xE1000, 0xEFFFD),
)
IPRIVATE = _ranges((0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD))
# RFC 3987 section 4.1: LRM, RLM, LRE, RLE, PDF, LRO and RLO.
BIDI_FORMATTING = frozenset("\u200e\u200f\u202a\u202b\u202c\u202d\u202e")


def _compile(unreserved: str, private: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """Compile the URI grammar, or the IRI one with the extra characters."""
    pchar = rf"(?:[{unreserved}{SUB_DELIMS}:@]|{PCT})"
    userinfo = rf"(?:[{unreserved}{SUB_DELIMS}:]|{PCT})*"
    reg_name = rf"(?:[{unreserved}{SUB_DELIMS}]|{PCT})*"
    host = rf"(?:{IP_LITERAL}|{IPV4}|{reg_name})"
    authority = rf"(?:{userinfo}@)?{host}(?::[0-9]*)?"
    segment = rf"{pchar}*"
    segment_nz = rf"{pchar}+"
    segment_nz_nc = rf"(?:[{unreserved}{SUB_DELIMS}@]|{PCT})+"
    path_abempty = rf"(?:/{segment})*"
    path_absolute = rf"/(?:{segment_nz}(?:/{segment})*)?"
    path_noscheme = rf"{segment_nz_nc}(?:/{segment})*"
    path_rootless = rf"{segment_nz}(?:/{segment})*"
    query = rf"(?:{pchar}|[/?{private}])*"
    fragment = rf"(?:{pchar}|[/?])*"
    hier_part = rf"(?://{authority}{path_abempty}|{path_absolute}|{path_rootless}|)"
    relative_part = rf"(?://{authority}{path_abempty}|{path_absolute}|{path_noscheme}|)"
    return (
        re.compile(rf"{SCHEME}:{hier_part}(?:\?{query})?(?:#{fragment})?"),
        re.compile(rf"{relative_part}(?:\?{query})?(?:#{fragment})?"),
    )


RE_URI, RE_RELATIVE_REF = _compile(UNRESERVED, "")
RE_IRI, RE_IRELATIVE_REF = _compile(UNRESERVED + UCSCHAR, IPRIVATE)
RE_IPV4 = re.compile(IPV4)

# Appendix B.
RE_SPLIT = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")


@dataclass
class Parts:
    scheme: str | None
    authority: str | None
    path: str
    query: str | None
    fragment: str | None

    def recompose(self) -> str:
        """Section 5.3."""
        out = []
        if self.scheme is not None:
            out.append(f"{self.scheme}:")
        if self.authority is not None:
            out.append(f"//{self.authority}")
        out.append(self.path)
        if self.query is not None:
            out.append(f"?{self.query}")
        if self.fragment is not None:
            out.append(f"#{self.fragment}")
        return "".join(out)


def split(value: str) -> Parts:
    match = RE_SPLIT.match(value)
    assert match is not None
    return Parts(*match.group(2, 4, 5, 7, 9))


def is_uri(value: str) -> bool:
    return RE_URI.fullmatch(value) is not None


def is_uri_reference(value: str) -> bool:
    return is_uri(value) or RE_RELATIVE_REF.fullmatch(value) is not None


def is_iri_reference(value: str) -> bool:
    """RFC 3987 sections 2.2 and 4.1."""
    if not BIDI_FORMATTING.isdisjoint(value):
        return False
    return (
        RE_IRI.fullmatch(value) is not None
        or RE_IRELATIVE_REF.fullmatch(value) is not None
    )


def _pct_encode(value: str) -> str:
    return "".join(
        c if c.isascii() else "".join(f"%{b:02X}" for b in c.encode()) for c in value
    )


# RFC 5895 section 2, step 4.
_IDEOGRAPHIC_FULL_STOPS = str.maketrans("\u3002\uff0e\uff61", "...")


def _width(char: str) -> str:
    decomposition = unicodedata.decomposition(char).split()
    if decomposition[:1] in (["<wide>"], ["<narrow>"]):
        return "".join(chr(int(code, 16)) for code in decomposition[1:])
    return char


def idna_host(host: str) -> str | None:
    """Encode a non-ASCII host with RFC 5895 and IDNA2008, or return None."""
    host = "".join(map(_width, host.lower()))
    host = unicodedata.normalize("NFC", host).translate(_IDEOGRAPHIC_FULL_STOPS)
    try:
        return idna.encode(host).decode("ascii")
    except idna.IDNAError:
        return None


def to_uri(value: str) -> str | None:
    """Map an IRI reference to a URI reference, RFC 3987 section 3.1.

    Return None when the value is not an IRI reference, or when its
    non-ASCII host is not a valid IDNA2008 name.
    """
    if not is_iri_reference(value):
        return None
    if value.isascii():
        return value
    parts = split(value)
    if parts.authority is not None and not parts.authority.isascii():
        # An IP-literal is ASCII, so the host is a reg-name, without ":".
        userinfo, at, hostport = parts.authority.rpartition("@")
        host, colon, port = hostport.partition(":")
        if not host.isascii() and (host := idna_host(host)) is None:
            return None
        parts.authority = f"{userinfo}{at}{host}{colon}{port}"
    return _pct_encode(parts.recompose())


def remove_dot_segments(path: str) -> str:
    """Section 5.2.4."""
    out: list[str] = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith(("./", "/./")):
            path = path[2:]
        elif path == "/.":
            path = "/"
        elif path.startswith("/../") or path == "/..":
            path = "/" + path[4:]
            if out:
                out.pop()
        elif path in (".", ".."):
            path = ""
        else:
            end = path.find("/", 1)
            end = len(path) if end == -1 else end
            out.append(path[:end])
            path = path[end:]
    return "".join(out)


def resolve(base: str, reference: str) -> str:
    """Section 5.2.2, strict parser."""
    b = split(base)
    r = split(reference)
    if r.scheme is not None:
        return replace(r, path=remove_dot_segments(r.path)).recompose()
    if r.authority is not None:
        target = replace(r, scheme=b.scheme, path=remove_dot_segments(r.path))
        return target.recompose()
    if not r.path:
        query = r.query if r.query is not None else b.query
        return Parts(b.scheme, b.authority, b.path, query, r.fragment).recompose()
    if r.path.startswith("/"):
        path = r.path
    elif b.authority is not None and not b.path:
        path = f"/{r.path}"
    else:
        path = b.path[: b.path.rfind("/") + 1] + r.path
    return Parts(
        b.scheme, b.authority, remove_dot_segments(path), r.query, r.fragment
    ).recompose()


def outcome(reference: str, base: str | None) -> str | None:
    """Return the target URI, or None when RFC 3986 gives no result.

    The reference and the base may be IRIs, mapped to URIs first.
    """
    uri = to_uri(reference)
    if uri is None:
        return None
    if is_uri(uri):
        parts = split(uri)
        return replace(parts, path=remove_dot_segments(parts.path)).recompose()
    base_uri = None if base is None else to_uri(base)
    if base_uri is None or not is_uri(base_uri):
        return None
    return resolve(base_uri, uri)


_PCT_RE = re.compile(r"%([0-9A-Fa-f]{2})")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
DEFAULT_PORTS = {"http": "80", "https": "443", "ws": "80", "wss": "443", "ftp": "21"}


def _normalize_pct(value: str) -> str:
    def sub(match: re.Match[str]) -> str:
        char = chr(int(match.group(1), 16))
        return char if char in _UNRESERVED else f"%{match.group(1).upper()}"

    return _PCT_RE.sub(sub, value)


def normalize(uri: str, scheme_based: bool = False) -> str:
    """Section 6.2.2, plus section 6.2.3 when scheme_based is set.

    Works best-effort on strings outside the grammar too, so outputs of
    other parsers can be compared.
    """
    p = split(uri)
    if p.scheme is not None:
        p.scheme = p.scheme.lower()
    if p.authority is not None:
        userinfo, sep, hostport = p.authority.rpartition("@")
        host, port = hostport, None
        if hostport.startswith("[") and "]" in hostport:
            end = hostport.index("]") + 1
            if hostport[end:].startswith(":"):
                host, port = hostport[:end], hostport[end + 1 :]
        elif ":" in hostport:
            host, _, port = hostport.rpartition(":")
        host = _normalize_pct(host.lower())
        if scheme_based:
            if port is not None and port.isdigit():
                port = str(int(port))
            if port == "" or port == DEFAULT_PORTS.get(p.scheme or ""):
                port = None
            if p.scheme in DEFAULT_PORTS and not p.path:
                p.path = "/"
        p.authority = (
            (f"{_normalize_pct(userinfo)}@" if sep else "")
            + host
            + (f":{port}" if port is not None else "")
        )
    p.path = _normalize_pct(p.path)
    if p.scheme is not None and (p.authority is not None or p.path.startswith("/")):
        p.path = remove_dot_segments(p.path)
    if p.query is not None:
        p.query = _normalize_pct(p.query)
    if p.fragment is not None:
        p.fragment = _normalize_pct(p.fragment)
    return p.recompose()
