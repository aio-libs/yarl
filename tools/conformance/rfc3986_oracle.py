"""A strict reference implementation of RFC 3986, used as a test oracle.

* Validation compiles the Appendix A ABNF to regular expressions.  Input
  is never preprocessed, so whitespace, backslashes, non-ASCII and other
  characters outside the grammar make it invalid.
* Resolution follows sections 5.2.2 (strict parser), 5.2.3, 5.2.4 and 5.3.
* Normalization follows section 6.2.2, plus the small scheme-based layer
  of section 6.2.3 (default ports, empty port, empty http path).
"""

import re
from dataclasses import dataclass, replace

UNRESERVED = r"A-Za-z0-9\-._~"
SUB_DELIMS = r"!$&'()*+,;="
PCT = r"%[0-9A-Fa-f]{2}"
PCHAR = rf"(?:[{UNRESERVED}{SUB_DELIMS}:@]|{PCT})"
SCHEME = r"[A-Za-z][A-Za-z0-9+\-.]*"
USERINFO = rf"(?:[{UNRESERVED}{SUB_DELIMS}:]|{PCT})*"
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
REG_NAME = rf"(?:[{UNRESERVED}{SUB_DELIMS}]|{PCT})*"
HOST = rf"(?:{IP_LITERAL}|{IPV4}|{REG_NAME})"
AUTHORITY = rf"(?:{USERINFO}@)?{HOST}(?::[0-9]*)?"
SEGMENT = rf"{PCHAR}*"
SEGMENT_NZ = rf"{PCHAR}+"
SEGMENT_NZ_NC = rf"(?:[{UNRESERVED}{SUB_DELIMS}@]|{PCT})+"
PATH_ABEMPTY = rf"(?:/{SEGMENT})*"
PATH_ABSOLUTE = rf"/(?:{SEGMENT_NZ}(?:/{SEGMENT})*)?"
PATH_NOSCHEME = rf"{SEGMENT_NZ_NC}(?:/{SEGMENT})*"
PATH_ROOTLESS = rf"{SEGMENT_NZ}(?:/{SEGMENT})*"
QUERY = rf"(?:{PCHAR}|[/?])*"
HIER_PART = rf"(?://{AUTHORITY}{PATH_ABEMPTY}|{PATH_ABSOLUTE}|{PATH_ROOTLESS}|)"
RELATIVE_PART = rf"(?://{AUTHORITY}{PATH_ABEMPTY}|{PATH_ABSOLUTE}|{PATH_NOSCHEME}|)"

RE_URI = re.compile(rf"{SCHEME}:{HIER_PART}(?:\?{QUERY})?(?:#{QUERY})?")
RE_RELATIVE_REF = re.compile(rf"{RELATIVE_PART}(?:\?{QUERY})?(?:#{QUERY})?")
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
    """Return the target URI, or None when RFC 3986 gives no result."""
    if not is_uri_reference(reference):
        return None
    if is_uri(reference):
        parts = split(reference)
        return replace(parts, path=remove_dot_segments(parts.path)).recompose()
    if base is None or not is_uri(base):
        return None
    return resolve(base, reference)


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
