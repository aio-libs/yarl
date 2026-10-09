"""URL parsing utilities."""

import codecs
import re
import unicodedata
from functools import lru_cache
from urllib.parse import parse_qsl, scheme_chars

from ._quoters import QUOTER, UNQUOTER_PLUS

# Leading and trailing C0 control and space to be stripped per WHATWG spec.
# == "".join([chr(i) for i in range(0, 0x20 + 1)])
WHATWG_C0_CONTROL_OR_SPACE = (
    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10"
    "\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f "
)

# Unsafe bytes to be removed per WHATWG spec
UNSAFE_URL_BYTES_TO_REMOVE = ["\t", "\r", "\n"]
# The WHATWG "special" schemes: their URLs always have an authority, so in
# WHATWG mode "//" is written out even when the authority is missing.
SPECIAL_SCHEMES = frozenset({"http", "https", "ws", "wss", "ftp", "file"})

# IPvFuture = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" ), RFC 3986
# section 3.2.2; the "v" is case-insensitive.
IP_FUTURE_RE = re.compile(r"[vV][0-9A-Fa-f]+\.[A-Za-z0-9\-._~!$&'()*+,;=:]+")

# Bits of the "empty" mask: the component is present but empty, as in
# "sc://", "http://h/?" or "http://h/#". An absent and an empty component
# are different per RFC 3986 section 5.3, but both are stored as "".
EMPTY_AUTHORITY = 1
EMPTY_QUERY = 2
EMPTY_FRAGMENT = 4

SplitURLType = tuple[str, str, str, str, str]

# The ZoneID of RFC 6874; in a URL it follows the address as "%25" <ZoneID>.
# RFC 6874 requires at least one character, yarl also accepts an empty zone
# identifier (#998).
ZONE_ID_RE = re.compile(r"(?:[0-9A-Za-z._~-]|%[0-9A-Fa-f]{2})*")


def check_zone_id(ip_literal: str) -> None:
    """Reject an IPv6 zone identifier not written as RFC 6874 says.

    The zone identifier follows the address as "%25" and the ZoneID, whose
    characters other than unreserved ones are percent-encoded. A bare "%",
    as in "fe80::1%eth0" (the user interface form of RFC 9844), or another
    percent-encoded octet, as in "::%31", is not URI syntax.
    """
    pct = ip_literal.index("%")
    if ip_literal[pct : pct + 3] != "%25" or not ZONE_ID_RE.fullmatch(
        ip_literal, pct + 3
    ):
        raise ValueError(f"Invalid IPv6 zone identifier in {ip_literal!r}")


def split_url(url: str) -> tuple[str, str, str, str, str, int]:
    """Split URL into parts and the mask of present but empty parts."""
    # Adapted from urllib.parse.urlsplit
    # Strip leading and trailing C0 control or space in both modes, as the
    # WHATWG basic URL parser does; RFC 3986 appendix C asks the same of
    # software that accepts user-typed URIs.
    url = url.strip(WHATWG_C0_CONTROL_OR_SPACE)
    for b in UNSAFE_URL_BYTES_TO_REMOVE:
        if b in url:
            url = url.replace(b, "")

    scheme = netloc = query = fragment = ""
    empty = 0
    i = url.find(":")
    if i > 0 and url[0] in scheme_chars:
        for c in url[1:i]:
            if c not in scheme_chars:
                break
        else:
            scheme, url = url[:i].lower(), url[i + 1 :]
    has_hash = "#" in url
    has_question_mark = "?" in url
    if url[:2] == "//":
        empty = EMPTY_AUTHORITY
        delim = len(url)  # position of end of domain part of url, default is end
        if has_hash and has_question_mark:
            delim_chars = "/?#"
        elif has_question_mark:
            delim_chars = "/?"
        elif has_hash:
            delim_chars = "/#"
        else:
            delim_chars = "/"
        for c in delim_chars:  # look for delimiters; the order is NOT important
            wdelim = url.find(c, 2)  # find first of this delim
            if wdelim >= 0 and wdelim < delim:  # if found
                delim = wdelim  # use earliest delim position
        netloc = url[2:delim]
        url = url[delim:]
        # Backslash is not valid in the authority component per RFC 3986.
        # WHATWG parsers treat \ as a path separator for special schemes, so
        # accepting it in the authority can cause host parsing ambiguity.
        if "\\" in netloc:
            raise ValueError(
                "Invalid URL: backslash ('\\') is not allowed in the authority "
                "component per RFC 3986."
            )
        has_left_bracket = "[" in netloc
        has_right_bracket = "]" in netloc
        if (has_left_bracket and not has_right_bracket) or (
            has_right_bracket and not has_left_bracket
        ):
            raise ValueError("Invalid IPv6 URL")
        if has_left_bracket:
            # Per RFC 3986, brackets are only valid at the START of the host
            # for IP-literal addresses. Text before '[' (e.g. '127.0.0.1[::1]')
            # is invalid and must be rejected to prevent SSRF bypasses. The
            # count checks reject URLs with more than one bracket pair in the
            # host subcomponent (e.g. 'http://[:localhost[]].google:80'),
            # which would otherwise resolve to an unintended host.
            hostinfo = netloc.rpartition("@")[2]
            if (
                not hostinfo
                or hostinfo[0] != "["
                or hostinfo.count("[") > 1
                or hostinfo.count("]") > 1
            ):
                raise ValueError("Invalid IPv6 URL")
            bracketed_host, _, after_bracket = hostinfo[1:].partition("]")
            # Per RFC 3986 §3.2.2, after the closing ']' of an IP-literal
            # only ":" <port> or end-of-authority is valid. Any other text
            # (e.g. '[::1]allowed.example:1') must be rejected to prevent
            # host-confusion where the suffix is silently dropped.
            if after_bracket and after_bracket[0] != ":":
                raise ValueError("Invalid IPv6 URL")
            # Valid bracketed hosts are defined in
            # https://www.rfc-editor.org/rfc/rfc3986#page-49
            # https://url.spec.whatwg.org/
            if bracketed_host and bracketed_host[0] in "vV":
                if not IP_FUTURE_RE.fullmatch(bracketed_host):
                    raise ValueError("IPvFuture address is invalid")
            elif ":" not in bracketed_host:
                raise ValueError("The IPv6 content between brackets is not valid")
            elif "%" in bracketed_host:
                check_zone_id(bracketed_host)
    if has_hash:
        url, _, fragment = url.partition("#")
        empty |= EMPTY_FRAGMENT
    if has_question_mark and "?" in url:
        url, _, query = url.partition("?")
        empty |= EMPTY_QUERY
    if netloc:
        if not netloc.isascii():
            _check_netloc(netloc)
        empty &= ~EMPTY_AUTHORITY
    if query:
        empty &= ~EMPTY_QUERY
    if fragment:
        empty &= ~EMPTY_FRAGMENT
    return scheme, netloc, url, query, fragment, empty


def _check_netloc(netloc: str) -> None:
    # Adapted from urllib.parse._checknetloc
    # looking for characters like \u2100 that expand to 'a/c'
    # IDNA uses NFKC equivalence, so normalize for this check

    # ignore characters already included
    # but not the surrounding text
    n = netloc.replace("@", "").replace(":", "").replace("#", "").replace("?", "")
    normalized_netloc = unicodedata.normalize("NFKC", n)
    if n == normalized_netloc:
        return
    # Note that there are no unicode decompositions for the character '@' so
    # its currently impossible to have test coverage for this branch, however if the
    # one should be added in the future we want to make sure its still checked.
    for c in "/?#@:%":  # pragma: no branch
        if c in normalized_netloc:
            raise ValueError(
                f"netloc '{netloc}' contains invalid "
                "characters under NFKC normalization"
            )


@lru_cache  # match the same size as urlsplit
def split_netloc(
    netloc: str,
) -> tuple[str | None, str | None, str | None, int | None]:
    """Split netloc into username, password, host and port.

    An empty username is None, see split_netloc_rfc() for RFC 3986 mode.
    """
    if "@" not in netloc:
        username: str | None = None
        password: str | None = None
        hostinfo = netloc
    else:
        userinfo, _, hostinfo = netloc.rpartition("@")
        username, have_password, password = userinfo.partition(":")
        if not have_password:
            password = None

    if "[" in hostinfo:
        if hostinfo[0] != "[" or hostinfo.count("[") > 1 or hostinfo.count("]") > 1:
            raise ValueError("Invalid IPv6 URL")
        _, _, bracketed = hostinfo.partition("[")
        hostname, _, port_str = bracketed.partition("]")
        # Defense-in-depth: after ']' only ':port' or empty is valid.
        # split_url() should have already rejected invalid suffixes,
        # but guard here too for callers that use split_netloc() directly.
        if port_str and port_str[0] != ":":
            raise ValueError("Invalid IPv6 URL")
        _, _, port_str = port_str.partition(":")
        if hostname[:1] in ("v", "V"):
            # An IPvFuture address keeps its brackets: without them it would
            # read as a reg-name. IPv6 addresses never start with "v".
            hostname = f"[{hostname}]"
    else:
        hostname, _, port_str = hostinfo.partition(":")

    if not port_str:
        return username or None, password, hostname or None, None

    # RFC 3986 section 3.2.3 defines the port as *DIGIT, i.e. ASCII digits
    # only. int() is more permissive and would accept a leading '+',
    # surrounding whitespace, underscore digit separators and non-ASCII
    # decimal digits, so reject those before converting.
    if not (port_str.isascii() and port_str.isdigit()):
        raise ValueError("Invalid URL: port can't be converted to integer")
    port = int(port_str)
    if not (0 <= port <= 65535):
        raise ValueError("Port out of range 0-65535")
    return username or None, password, hostname or None, port


@lru_cache
def split_netloc_rfc(
    netloc: str,
) -> tuple[str | None, str | None, str | None, int | None]:
    """Split netloc into username, password, host and port in RFC 3986 mode.

    As split_netloc(), but an empty username is "" when the netloc has
    userinfo, as RFC 3986 keeps an empty userinfo: "@h" and ":p@h" have the
    username "". A separate cache keeps the single string key, which a mode
    argument would turn into a tuple.
    """
    username, password, host, port = split_netloc(netloc)
    if username is None and "@" in netloc:
        username = ""
    return username, password, host, port


# "//" behind any number of "/." segments, see needs_dot_prefix().
_DOT_PREFIXED_AUTHORITY_RE = re.compile(r"(?:/\.)*//")


def needs_dot_prefix(path: str) -> bool:
    """Tell if an authority-less path needs "/." in front when written out.

    A path starting with "//" would read as an authority, so str() writes
    "/." before it and the parsers drop that "/." again. To keep a literal
    "/." segment in such a place, a path that is "//..." behind any number
    of "/." segments gets the prefix too, e.g. "/.//a" is written "/././/a".
    """
    return _DOT_PREFIXED_AUTHORITY_RE.match(path) is not None


def has_dot_prefix(path: str) -> bool:
    """Tell if an authority-less path starts with the "/." str() adds."""
    return path[:3] == "/./" and _DOT_PREFIXED_AUTHORITY_RE.match(path, 2) is not None


def unsplit_result(
    scheme: str, netloc: str, url: str, query: str, fragment: str
) -> str:
    """Unsplit a URL without any normalization."""
    if netloc:
        if url and url[:1] != "/":
            url = f"{scheme}://{netloc}/{url}" if scheme else f"{scheme}:{url}"
        else:
            url = f"{scheme}://{netloc}{url}" if scheme else f"//{netloc}{url}"
    else:
        if url[:2] == "//" or (url[:3] == "/./" and needs_dot_prefix(url)):
            # Without an authority a path cannot start with "//", which
            # would read as one; "/." keeps it a path, as WHATWG does.
            url = f"/.{url}"
        if scheme:
            url = f"{scheme}:{url}"
    if query:
        url = f"{url}?{query}"
    return f"{url}#{fragment}" if fragment else url


def unsplit_result_empty(
    scheme: str, netloc: str, url: str, query: str, fragment: str, empty: int
) -> str:
    """Unsplit a URL that has present but empty components.

    *empty* is a mask of EMPTY_AUTHORITY, EMPTY_QUERY and EMPTY_FRAGMENT
    telling which empty components are present.
    """
    if netloc or empty & EMPTY_AUTHORITY:
        if url and url[:1] != "/":
            url = f"{scheme}://{netloc}/{url}" if scheme else f"{scheme}:{url}"
        else:
            url = f"{scheme}://{netloc}{url}" if scheme else f"//{netloc}{url}"
    else:
        if url[:2] == "//" or (url[:3] == "/./" and needs_dot_prefix(url)):
            url = f"/.{url}"
        if scheme:
            url = f"{scheme}:{url}"
    if query or empty & EMPTY_QUERY:
        url = f"{url}?{query}"
    return f"{url}#{fragment}" if fragment or empty & EMPTY_FRAGMENT else url


@lru_cache  # match the same size as urlsplit
def make_netloc(
    user: str | None,
    password: str | None,
    host: str | None,
    port: int | None,
    encode: bool = False,
) -> str:
    """Make netloc from parts.

    The user and password are encoded if encode is True. A user that is
    not None is written with "@" even when it is empty, as RFC 3986 mode
    keeps an empty userinfo; WHATWG mode passes None for an empty user.

    The host must already be encoded with _encode_host.
    """
    if host is None:
        return ""
    ret = host
    if port is not None:
        ret = f"{ret}:{port}"
    if user is None and password is None:
        return ret
    if password is not None:
        if not user:
            user = ""
        elif encode:
            user = QUOTER(user)
        if encode:
            password = QUOTER(password)
        user = f"{user}:{password}"
    elif user and encode:
        user = QUOTER(user)
    return f"{user}@{ret}"


def query_to_pairs(
    query_string: str, *, max_fields: int | None = None, encoding: str = "utf-8"
) -> list[tuple[str, str]]:
    """Parse a query string into a list of decoded name, value pairs.

    The result is the same as
    ``urllib.parse.parse_qsl(query_string, keep_blank_values=True,
    encoding=encoding, max_num_fields=max_fields)``.

    Raises :exc:`ValueError` if *max_fields* is not ``None`` and the
    query string has more than *max_fields* fields. An empty query string
    returns an empty list on every Python version, even when *max_fields*
    is ``0``, where ``parse_qsl`` on Python 3.10 raises instead.
    """
    if not query_string:
        return []
    if max_fields is not None and query_string.count("&") >= max_fields:
        raise ValueError("Max number of fields exceeded")
    pairs: list[tuple[str, str]] = []
    if "%" not in query_string:
        # Nothing to decode except '+', which is the same in every encoding
        for name_value in query_string.replace("+", " ").split("&"):
            if name_value:
                name, _, value = name_value.partition("=")
                pairs.append((name, value))
        return pairs
    if encoding != "utf-8" and codecs.lookup(encoding).name != "utf-8":
        return parse_qsl(query_string, keep_blank_values=True, encoding=encoding)
    for name_value in query_string.split("&"):
        if name_value:
            name, _, value = name_value.partition("=")
            pairs.append((UNQUOTER_PLUS(name), UNQUOTER_PLUS(value)))
    return pairs
