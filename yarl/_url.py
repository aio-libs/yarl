import re
import sys
import warnings
from collections.abc import Mapping, Sequence
from enum import Enum
from functools import _CacheInfo, lru_cache
from importlib.util import find_spec
from ipaddress import ip_address
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NoReturn,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)
from urllib.parse import SplitResult, scheme_chars, unquote_to_bytes, uses_relative

import idna
from multidict import MultiDict, MultiDictProxy, istr
from propcache.api import under_cached_property as cached_property

from ._parse import (
    EMPTY_AUTHORITY,
    EMPTY_FRAGMENT,
    EMPTY_QUERY,
    SPECIAL_SCHEMES,
    SplitURLType,
    has_dot_prefix,
    make_netloc,
    query_to_pairs,
    split_netloc,
    split_url,
    unsplit_result,
    unsplit_result_empty,
)
from ._path import normalize_path, normalize_path_segments
from ._query import (
    Query,
    QueryVariable,
    SimpleQuery,
    get_str_query,
    get_str_query_from_iterable,
    get_str_query_from_sequence_iterable,
)
from ._quoters import (
    FRAGMENT_QUOTER,
    FRAGMENT_REQUOTER,
    PATH_QUOTER,
    PATH_REQUOTER,
    PATH_SAFE_UNQUOTER,
    QS_UNQUOTER,
    QUERY_QUOTER,
    QUERY_REQUOTER,
    QUOTER,
    REQUOTER,
    UNQUOTER,
    human_quote,
)

# Avoid Pydantic import if not used (increases yarl's import time by 3-7x).
HAS_PYDANTIC = find_spec("pydantic_core") is not None
if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema


DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443, "ftp": 21}
USES_RELATIVE = frozenset(uses_relative)
_SCHEME_CHARS = frozenset(scheme_chars)

# Special schemes https://url.spec.whatwg.org/#special-scheme
# are not allowed to have an empty host https://url.spec.whatwg.org/#url-representation
SCHEME_REQUIRES_HOST = frozenset(("http", "https", "ws", "wss", "ftp"))


# reg-name: unreserved / pct-encoded / sub-delims
# this pattern matches anything that is *not* in those classes. and is only used
# on lower-cased ASCII values.
NOT_REG_NAME = re.compile(
    r"""
        # any character not in the unreserved or sub-delims sets, plus %
        # (validated with the additional check for pct-encoded sequences below)
        [^a-z0-9\-._~!$&'()*+,;=%]
    |
        # % only allowed if it is part of a pct-encoded
        # sequence of 2 hex digits.
        %(?![0-9a-f]{2})
    """,
    re.VERBOSE,
)

# Invisible default-ignorable / format code points that must not appear in a
# host (soft hyphen, zero-width space, word joiner, bidi controls, variation
# selectors, ...). Depending on the code point IDNA either silently deletes it
# (so ``e<ZWSP>vil.com`` encodes to ``evil.com``) or folds it into a different
# punycode host; either way the parsed host differs from the string an
# application validated. The set is the union of two authoritative sources,
# matching the two encoders _idna_encode dispatches to:
#
# 1. Unicode Default_Ignorable_Code_Point (uts46=True path via the ``idna``
#    package). Ranges taken from the DerivedCoreProperties data file:
#    https://www.unicode.org/Public/UCD/latest/ucd/DerivedCoreProperties.txt
#    (the E0000..E0FFF block is contiguous under this property).
# 2. RFC 3454 (Stringprep) Table B.1 "commonly mapped to nothing", used by the
#    stdlib ``str.encode("idna")`` / IDNA2003 nameprep fallback:
#    https://www.rfc-editor.org/rfc/rfc3454#appendix-B.1
#    This is the source of U+1806, which is not Default_Ignorable.
#
# Coverage is pinned to the installed ``idna``/Unicode data by a sweep test
# (test_default_ignorable_covers_idna_stripped in tests/test_url.py) that
# brute-forces every code point through _idna_encode and fails if any point it
# silently deletes is not matched here.
_DEFAULT_IGNORABLE_RE = re.compile(
    "["
    "\u00ad"  # SOFT HYPHEN
    "\u034f"  # COMBINING GRAPHEME JOINER
    "\u061c"  # ARABIC LETTER MARK
    "\u115f-\u1160"  # HANGUL CHOSEONG/JUNGSEONG FILLER
    "\u17b4-\u17b5"  # KHMER VOWEL INHERENT AQ/AA
    "\u1806"  # MONGOLIAN TODO SOFT HYPHEN (nameprep maps to nothing)
    "\u180b-\u180f"  # MONGOLIAN FVS ONE..FOUR and VOWEL SEPARATOR
    "\u200b-\u200f"  # ZERO WIDTH SPACE..RIGHT-TO-LEFT MARK
    "\u202a-\u202e"  # bidi embedding/override controls
    "\u2060-\u206f"  # WORD JOINER..NOMINAL DIGIT SHAPES
    "\u3164"  # HANGUL FILLER
    "\ufe00-\ufe0f"  # VARIATION SELECTOR-1..16
    "\ufeff"  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\uffa0"  # HALFWIDTH HANGUL FILLER
    "\ufff0-\ufff8"  # reserved default-ignorables
    "\U0001bca0-\U0001bca3"  # SHORTHAND FORMAT controls
    "\U0001d173-\U0001d17a"  # MUSICAL SYMBOL begin/end controls
    "\U000e0000-\U000e0fff"  # tags and VARIATION SELECTOR SUPPLEMENT
    "]"
)

# Zone IDs are OS-specific text strings with no format defined by the RFCs:
# https://datatracker.ietf.org/doc/html/rfc4007#section-11.2
# RFC 9844 §6.3 recommends rejecting characters inappropriate for the
# environment; for yarl we reject ASCII control characters (CTL):
# https://datatracker.ietf.org/doc/html/rfc9844#section-6-3
_ZONE_ID_UNSAFE_RE = re.compile(r"[\x00-\x1f\x7f]")

_T = TypeVar("_T")

if sys.version_info >= (3, 11):
    from enum import StrEnum
    from typing import Self
else:
    Self = Any

    class StrEnum(str, Enum):
        """Backport of :class:`enum.StrEnum` for Python 3.10."""

        __str__ = str.__str__


class UndefinedType(Enum):
    """Singleton type for use with not set sentinel values."""

    _singleton = 0


UNDEFINED = UndefinedType._singleton


class Mode(StrEnum):
    """URL standard a :class:`URL` follows."""

    RFC = "rfc"
    WHATWG = "whatwg"


Mode.__module__ = "yarl"
_WHATWG = Mode.WHATWG
# Members hash and compare as their values, so this maps both the members and
# the plain strings; much faster than calling ``Mode(value)``.
_MODE_BY_VALUE: dict[str, Mode] = {c.value: c for c in Mode}

ModeType = Mode | Literal["rfc", "whatwg"]


def _to_mode(value: ModeType) -> Mode:
    """Normalize a compatibility argument, rejecting unknown values."""
    try:
        mode = _MODE_BY_VALUE.get(value)
    except TypeError:  # unhashable, e.g. a list
        mode = None
    if mode is None:
        raise ValueError(f"{value!r} is not a valid Mode")
    return mode


class CacheInfo(TypedDict):
    """Host encoding cache."""

    idna_encode: _CacheInfo
    idna_decode: _CacheInfo
    ip_address: _CacheInfo
    host_validate: _CacheInfo
    encode_host: _CacheInfo


class _InternalURLCache(TypedDict, total=False):
    _val: SplitURLType
    _join_path: str
    _origin: "URL"
    absolute: bool
    hash: int
    scheme: str
    raw_authority: str
    authority: str
    raw_user: str | None
    user: str | None
    raw_password: str | None
    password: str | None
    raw_host: str | None
    host: str | None
    host_subcomponent: str | None
    host_port_subcomponent: str | None
    port: int | None
    explicit_port: int | None
    raw_path: str
    path: str
    _parsed_query: list[tuple[str, str]]
    query: "MultiDictProxy[str]"
    raw_query_string: str
    query_string: str
    path_qs: str
    raw_path_qs: str
    raw_fragment: str
    fragment: str
    raw_parts: tuple[str, ...]
    parts: tuple[str, ...]
    parent: "URL"
    raw_name: str
    name: str
    raw_suffix: str
    suffix: str
    raw_suffixes: tuple[str, ...]
    suffixes: tuple[str, ...]


def rewrite_module(obj: _T) -> _T:
    obj.__module__ = "yarl"
    return obj


def _encode_relative_scheme_colon(path: str) -> str:
    """Re-encode a scheme-shaped leading ``:`` in a relative path to ``%3A``."""
    colon_pos = path.find(":")
    if colon_pos <= 0:
        return path
    for c in path[:colon_pos]:
        if c not in _SCHEME_CHARS:
            return path
    return path[:colon_pos] + "%3A" + path[colon_pos + 1 :]


def _check_missing_host(scheme: str, mode: Mode) -> None:
    """Reject an authority that has userinfo or a port but no host.

    Schemes that need a host always reject it. RFC 3986 allows an empty
    host otherwise, WHATWG rejects it for every scheme.
    """
    if scheme in SCHEME_REQUIRES_HOST:
        raise ValueError(
            f"Invalid URL: host is required for absolute urls with the {scheme} scheme"
        )
    if mode is Mode.WHATWG:
        raise ValueError("Invalid URL: host is required with userinfo or a port")


def _idna2003_host_error(host: str) -> str:
    """Explain why RFC 3986 mode rejected a non-ASCII host.

    RFC 3987 converts an internationalized host with IDNA, now IDNA2008
    (RFC 5891), which disallows code points such as emoji. WHATWG mode keeps
    the IDNA2003 fallback of _idna_encode(), as UTS #46 accepts them.
    """
    return f"Host {host!r} is not a valid IDNA2008 name"


# The RFC 3986 mode check below is guarded with ``mode is not _WHATWG`` at
# the call sites, so that the default mode does not pay for a call on the
# URL.build() hot path (CodSpeed).
def _check_rfc_authority(authority: str) -> None:
    """Reject "@" in the userinfo in RFC 3986 mode.

    RFC 3986 userinfo cannot contain "@", so "sc://a@b@c/" has no valid
    parse; WHATWG splits at the last "@" and percent-encodes the others.
    """
    if authority.count("@") > 1:
        raise ValueError(f"Invalid URL: userinfo cannot contain '@' in {authority!r}")


def _special_authority_url(
    scheme: str, path: str, query: str, fragment: str, empty: int, encoded: bool
) -> "URL":
    """Parse "http:host/p" or "http:///host/p" in WHATWG mode.

    The WHATWG URL Standard skips any slashes after the scheme of a special
    URL and reads an authority, so "http:/example.com/" and
    "http:///example.com/" are "http://example.com/". Against a base with the
    same scheme, an input without "//" is the relative reference
    "/example.com/" instead; its path is kept for join().
    """
    url_str = f"{scheme}://{path.lstrip('/')}"
    if query or empty & EMPTY_QUERY:
        url_str = f"{url_str}?{query}"
    if fragment or empty & EMPTY_FRAGMENT:
        url_str = f"{url_str}#{fragment}"
    if encoded:
        url = _pre_encoded_url(url_str, _WHATWG)
    else:
        url = _encode_url(url_str, _WHATWG)
        path = PATH_REQUOTER(path)
    if not empty & EMPTY_AUTHORITY:
        url._cache["_join_path"] = path
    return url


def _is_special_authority_path(scheme: str, path: str, mode: Mode) -> bool:
    """Tell if the path of a URL without a host is its authority in WHATWG mode.

    Only a path with text after the leading slashes is, so "http:", "http:/"
    and "http:///" stay as they are: against a base with the same scheme the
    WHATWG parser reads the first two as references to the base, and alone
    it rejects all of them.
    """
    return mode is _WHATWG and scheme in SCHEME_REQUIRES_HOST and path.lstrip("/") != ""


def _encode_url(url_str: str, mode: Mode) -> "URL":
    """Parse unencoded URL."""
    cache: _InternalURLCache = {}
    host: str | None
    scheme, netloc, path, query, fragment, empty = split_url(url_str)
    if not netloc and _is_special_authority_path(scheme, path, mode):
        return _special_authority_url(scheme, path, query, fragment, empty, False)
    if not netloc:  # netloc
        host = ""
    else:
        if ":" in netloc or "@" in netloc or "[" in netloc:
            # Complex netloc
            if mode is not _WHATWG:
                _check_rfc_authority(netloc)
            username, password, host, port = split_netloc(netloc)
        else:
            username = password = port = None
            host = netloc
        if host is None:
            # The authority is not empty, so it has userinfo or a port.
            _check_missing_host(scheme, mode)
            host = ""
        # The parser historically encoded without validation, which let
        # control characters (NUL/C0) and IDNA-normalized delimiters into
        # the host, producing a ``str(url)`` that yarl cannot re-parse
        # (#1829). Validate like the builder APIs do, but keep accepting an
        # empty IPv6 zone identifier, which parsing has always allowed (#998).
        encoded, whatwg_host, idna2003 = _encode_host(
            host, validate_host=True, reject_empty_zone=False
        )
        if idna2003 and mode is not _WHATWG:
            raise ValueError(_idna2003_host_error(host))
        host = encoded
        if whatwg_host is not host and mode is _WHATWG and scheme in SPECIAL_SCHEMES:
            host = _whatwg_special_host(host, whatwg_host)
        # Remove brackets as host encoder adds back brackets for IPv6 addresses.
        # An empty host (RFC mode, e.g. "sc://user@:8080") is None, as for
        # built and pre-encoded URLs.
        cache["raw_host"] = (host[1:-1] if "[" in host else host) or None
        cache["explicit_port"] = port
        if password is None and username is None:
            # Fast path for URLs without user, password
            netloc = host if port is None else f"{host}:{port}"
            cache["raw_user"] = None
            cache["raw_password"] = None
        else:
            raw_user = REQUOTER(username) if username else username
            raw_password = REQUOTER(password) if password else password
            netloc = make_netloc(raw_user, raw_password, host, port)
            cache["raw_user"] = raw_user
            cache["raw_password"] = raw_password

    if path:
        path = PATH_REQUOTER(path)
        if netloc and "." in path:
            path = normalize_path(path)
        elif not scheme and not netloc:
            path = _encode_relative_scheme_colon(path)
        if not netloc and has_dot_prefix(path) and not empty & EMPTY_AUTHORITY:
            # Undo the "/." that str() puts in front of a path starting
            # with "//" when there is no authority.
            path = path[2:]
    if query:
        query = QUERY_REQUOTER(query)
    if fragment:
        fragment = FRAGMENT_REQUOTER(fragment)

    cache["scheme"] = scheme
    cache["raw_path"] = "/" if not path and netloc else path
    cache["raw_query_string"] = query
    cache["raw_fragment"] = fragment

    self = object.__new__(URL)
    self._scheme = scheme
    self._netloc = netloc
    self._path = path
    self._query = query
    self._fragment = fragment
    self._empty = empty
    self._cache = cache
    self._mode = mode
    return self


def _pre_encoded_url(url_str: str, mode: Mode) -> "URL":
    """Parse pre-encoded URL."""
    val = split_url(url_str)
    scheme, netloc, path, query, fragment, empty = val
    if not netloc and _is_special_authority_path(scheme, path, mode):
        return _special_authority_url(scheme, path, query, fragment, empty, True)
    self = object.__new__(URL)
    (
        self._scheme,
        self._netloc,
        self._path,
        self._query,
        self._fragment,
        self._empty,
    ) = val
    if (
        not self._netloc
        and has_dot_prefix(self._path)
        and not self._empty & EMPTY_AUTHORITY
    ):
        # Undo the "/." that str() puts in front of a path starting with
        # "//" when there is no authority, as the unencoded parser does.
        self._path = self._path[2:]
    self._cache = {}
    self._mode = mode
    return self


# One cache per compatibility mode keeps the single ``str`` argument, which
# ``lru_cache`` uses as the key directly instead of building a tuple.
@lru_cache
def encode_url(url_str: str) -> "URL":
    """Parse unencoded URL in WHATWG mode."""
    return _encode_url(url_str, Mode.WHATWG)


@lru_cache
def encode_url_rfc(url_str: str) -> "URL":
    """Parse unencoded URL in RFC 3986 mode."""
    return _encode_url(url_str, Mode.RFC)


@lru_cache
def pre_encoded_url(url_str: str) -> "URL":
    """Parse pre-encoded URL in WHATWG mode."""
    return _pre_encoded_url(url_str, Mode.WHATWG)


@lru_cache
def pre_encoded_url_rfc(url_str: str) -> "URL":
    """Parse pre-encoded URL in RFC 3986 mode."""
    return _pre_encoded_url(url_str, Mode.RFC)


@lru_cache
def build_pre_encoded_url(
    scheme: str,
    authority: str,
    user: str | None,
    password: str | None,
    host: str,
    port: int | None,
    path: str,
    query_string: str,
    fragment: str,
    mode: Mode,
) -> "URL":
    """Build a pre-encoded URL from parts."""
    self = object.__new__(URL)
    self._scheme = scheme
    if authority:
        self._netloc = authority
    elif host:
        if port is not None:
            port = None if port == DEFAULT_PORTS.get(scheme) else port
        if user is None and password is None:
            self._netloc = host if port is None else f"{host}:{port}"
        else:
            self._netloc = make_netloc(user, password, host, port)
    else:
        self._netloc = ""
    if path and not scheme and not self._netloc and ":" in path:
        path = _encode_relative_scheme_colon(path)
    self._path = path
    self._query = query_string
    self._fragment = fragment
    self._empty = 0
    self._cache = {}
    self._mode = mode
    return self


def _kept_empty(keep_query: bool, keep_fragment: bool) -> int:
    """Return the mask of empty components kept by a path replacement."""
    return (
        EMPTY_AUTHORITY
        | (EMPTY_QUERY if keep_query else 0)
        | (EMPTY_FRAGMENT if keep_fragment else 0)
    )


def from_parts_uncached(
    scheme: str,
    netloc: str,
    path: str,
    query: str,
    fragment: str,
    mode: Mode,
    empty: int = 0,
) -> "URL":
    """Create a new URL from parts.

    *empty* marks which empty components are present, see split_url(); it
    must not have bits for components that are not empty.
    """
    self = object.__new__(URL)
    self._scheme = scheme
    self._netloc = netloc
    if path and not scheme and not netloc and ":" in path:
        path = _encode_relative_scheme_colon(path)
    self._path = path
    self._query = query
    self._fragment = fragment
    self._empty = empty
    self._cache = {}
    self._mode = mode
    return self


from_parts = lru_cache(from_parts_uncached)


@rewrite_module
class URL:
    # Don't derive from str
    # follow pathlib.Path design
    # probably URL will not suffer from pathlib problems:
    # it's intended for libraries like aiohttp,
    # not to be passed into standard library functions like os.open etc.

    # URL grammar (RFC 3986)
    # pct-encoded = "%" HEXDIG HEXDIG
    # reserved    = gen-delims / sub-delims
    # gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    # sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
    #             / "*" / "+" / "," / ";" / "="
    # unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # URI         = scheme ":" hier-part [ "?" query ] [ "#" fragment ]
    # hier-part   = "//" authority path-abempty
    #             / path-absolute
    #             / path-rootless
    #             / path-empty
    # scheme      = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
    # authority   = [ userinfo "@" ] host [ ":" port ]
    # userinfo    = *( unreserved / pct-encoded / sub-delims / ":" )
    # host        = IP-literal / IPv4address / reg-name
    # IP-literal = "[" ( IPv6address / IPvFuture  ) "]"
    # IPvFuture  = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" )
    # IPv6address =                            6( h16 ":" ) ls32
    #             /                       "::" 5( h16 ":" ) ls32
    #             / [               h16 ] "::" 4( h16 ":" ) ls32
    #             / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
    #             / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
    #             / [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
    #             / [ *4( h16 ":" ) h16 ] "::"              ls32
    #             / [ *5( h16 ":" ) h16 ] "::"              h16
    #             / [ *6( h16 ":" ) h16 ] "::"
    # ls32        = ( h16 ":" h16 ) / IPv4address
    #             ; least-significant 32 bits of address
    # h16         = 1*4HEXDIG
    #             ; 16 bits of address represented in hexadecimal
    # IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet
    # dec-octet   = DIGIT                 ; 0-9
    #             / %x31-39 DIGIT         ; 10-99
    #             / "1" 2DIGIT            ; 100-199
    #             / "2" %x30-34 DIGIT     ; 200-249
    #             / "25" %x30-35          ; 250-255
    # reg-name    = *( unreserved / pct-encoded / sub-delims )
    # port        = *DIGIT
    # path          = path-abempty    ; begins with "/" or is empty
    #               / path-absolute   ; begins with "/" but not "//"
    #               / path-noscheme   ; begins with a non-colon segment
    #               / path-rootless   ; begins with a segment
    #               / path-empty      ; zero characters
    # path-abempty  = *( "/" segment )
    # path-absolute = "/" [ segment-nz *( "/" segment ) ]
    # path-noscheme = segment-nz-nc *( "/" segment )
    # path-rootless = segment-nz *( "/" segment )
    # path-empty    = 0<pchar>
    # segment       = *pchar
    # segment-nz    = 1*pchar
    # segment-nz-nc = 1*( unreserved / pct-encoded / sub-delims / "@" )
    #               ; non-zero-length segment without any colon ":"
    # pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
    # query       = *( pchar / "/" / "?" )
    # fragment    = *( pchar / "/" / "?" )
    # URI-reference = URI / relative-ref
    # relative-ref  = relative-part [ "?" query ] [ "#" fragment ]
    # relative-part = "//" authority path-abempty
    #               / path-absolute
    #               / path-noscheme
    #               / path-empty
    # absolute-URI  = scheme ":" hier-part [ "?" query ]
    __slots__ = (
        "_cache",
        "_scheme",
        "_netloc",
        "_path",
        "_query",
        "_fragment",
        "_empty",
        "_mode",
    )

    _cache: _InternalURLCache
    _scheme: str
    _netloc: str
    _path: str
    _query: str
    _fragment: str
    # EMPTY_AUTHORITY, EMPTY_QUERY and EMPTY_FRAGMENT bits for components
    # that are present but empty, e.g. the query of "http://h/?"
    _empty: int
    _mode: Mode

    def __new__(
        cls,
        val: Union[str, SplitResult, "URL", UndefinedType] = UNDEFINED,
        *,
        encoded: bool = False,
        strict: bool | None = None,
        # Internally ``None`` stands for ``Mode.WHATWG``; it is not a
        # documented value. It is the default rather than the enum member
        # because ``mode is None`` compares against a constant, while
        # ``mode is Mode.WHATWG`` (or a module-level alias) needs a
        # global lookup; on the cached ``URL(str)`` hot path that lookup alone
        # was measured at about 3% of the whole call (CodSpeed). The
        # ``== "whatwg"`` test then matches both the string and the enum
        # member without calling ``_to_mode()``.
        mode: ModeType = None,  # type: ignore[assignment]
    ) -> "URL":
        if strict is not None:  # pragma: no cover
            warnings.warn("strict parameter is ignored")
        if type(val) is str:
            if mode is None or mode == "whatwg":  # type: ignore[redundant-expr]
                return pre_encoded_url(val) if encoded else encode_url(val)
            _to_mode(mode)  # reject unknown values; the rest is RFC
            return pre_encoded_url_rfc(val) if encoded else encode_url_rfc(val)
        mode = _WHATWG if mode is None else _to_mode(mode)  # type: ignore[redundant-expr]
        if type(val) is cls:
            if val._mode is mode:
                return val
            scheme, netloc, path, query, fragment = val._val
            netloc = _moved_netloc(val, scheme, mode)
            return from_parts(scheme, netloc, path, query, fragment, mode, val._empty)
        if type(val) is SplitResult:
            if not encoded:
                raise ValueError("Cannot apply decoding to SplitResult")
            return from_parts(*val, mode)
        if isinstance(val, str):
            return URL(str(val), encoded=encoded, mode=mode)
        if val is UNDEFINED:
            # Special case for UNDEFINED since it might be unpickling and we do
            # not want to cache as the `__set_state__` call would mutate the URL
            # object in the `pre_encoded_url` or `encoded_url` caches.
            self = object.__new__(URL)
            self._scheme = self._netloc = self._path = self._query = self._fragment = ""
            self._empty = 0
            self._cache = {}
            self._mode = mode
            return self
        raise TypeError("Constructor parameter should be str")

    @classmethod
    def build(
        cls,
        *,
        scheme: str = "",
        authority: str = "",
        user: str | None = None,
        password: str | None = None,
        host: str = "",
        port: int | None = None,
        path: str = "",
        query: Query | None = None,
        query_string: str = "",
        fragment: str = "",
        encoded: bool = False,
        # Internally ``None`` stands for ``Mode.WHATWG``, as in ``URL()``.
        mode: ModeType = None,  # type: ignore[assignment]
    ) -> "URL":
        """Creates and returns a new URL"""
        mode = _WHATWG if mode is None else _to_mode(mode)  # type: ignore[redundant-expr]

        if authority and (user or password or host or port):
            raise ValueError(
                'Can\'t mix "authority" with "user", "password", "host" or "port".'
            )
        if port is not None and not isinstance(port, int):
            raise TypeError(f"The port is required to be int, got {type(port)!r}.")
        if port and not host:
            raise ValueError('Can\'t build URL with "port" but without "host".')
        if query and query_string:
            raise ValueError('Only one of "query" or "query_string" should be passed')
        if (
            scheme is None  # type: ignore[redundant-expr]
            or authority is None  # type: ignore[redundant-expr]
            or host is None  # type: ignore[redundant-expr]
            or path is None  # type: ignore[redundant-expr]
            or query_string is None  # type: ignore[redundant-expr]
            or fragment is None
        ):
            raise TypeError(
                'NoneType is illegal for "scheme", "authority", "host", "path", '
                '"query_string", and "fragment" args, use empty string instead.'
            )

        if query:
            query_string = get_str_query(query) or ""

        if encoded:
            return build_pre_encoded_url(
                scheme,
                authority,
                user,
                password,
                host,
                port,
                path,
                query_string,
                fragment,
                mode,
            )

        self = object.__new__(URL)
        self._scheme = scheme
        _host: str | None = None
        if authority:
            if mode is not _WHATWG:
                _check_rfc_authority(authority)
            user, password, _host, port = split_netloc(authority)
            if not _host:
                _check_missing_host(scheme, mode)
            if _host:
                encoded_host, whatwg_host, idna2003 = _encode_host(
                    _host, validate_host=False
                )
                if idna2003 and mode is not _WHATWG:
                    raise ValueError(_idna2003_host_error(_host))
                _host = encoded_host
                if (
                    whatwg_host is not _host
                    and mode is _WHATWG
                    and scheme in SPECIAL_SCHEMES
                ):
                    _host = _whatwg_special_host(_host, whatwg_host)
            else:
                _host = ""
        elif host:
            _host, whatwg_host, idna2003 = _encode_host(host, validate_host=True)
            if idna2003 and mode is not _WHATWG:
                raise ValueError(_idna2003_host_error(host))
            if (
                whatwg_host is not _host
                and mode is _WHATWG
                and scheme in SPECIAL_SCHEMES
            ):
                _host = _whatwg_special_host(_host, whatwg_host)
        else:
            self._netloc = ""

        if _host is not None:
            if port is not None:
                port = None if port == DEFAULT_PORTS.get(scheme) else port
            if user is None and password is None:
                self._netloc = _host if port is None else f"{_host}:{port}"
            else:
                self._netloc = make_netloc(user, password, _host, port, True)

        path = PATH_QUOTER(path) if path else path
        if path and self._netloc:
            if "." in path:
                path = normalize_path(path)
            if path[0] != "/":
                msg = (
                    "Path in a URL with authority should "
                    "start with a slash ('/') if set"
                )
                raise ValueError(msg)

        if path and not self._scheme and not self._netloc and ":" in path:
            path = _encode_relative_scheme_colon(path)
        self._path = path
        if not query and query_string:
            query_string = QUERY_QUOTER(query_string)
        self._query = query_string
        self._fragment = FRAGMENT_QUOTER(fragment) if fragment else fragment
        self._empty = 0
        self._cache = {}
        self._mode = mode
        return self

    def __init_subclass__(cls) -> NoReturn:
        raise TypeError(f"Inheriting a class {cls!r} from URL is forbidden")

    def __str__(self) -> str:
        if self._empty or not self._netloc:
            # Rare: empty components, or no authority, which a special
            # scheme in WHATWG mode still prints as "//".
            return self._str_with_empty()
        if not self._path and (self._query or self._fragment):
            path = "/"
        else:
            path = self._path
        if (port := self.explicit_port) is not None and port == DEFAULT_PORTS.get(
            self._scheme
        ):
            # port normalization - using None for default ports to remove from rendering
            # https://datatracker.ietf.org/doc/html/rfc3986.html#section-6.2.3
            host = self.host_subcomponent
            netloc = make_netloc(self.raw_user, self.raw_password, host, None)
        else:
            netloc = self._netloc
        return unsplit_result(self._scheme, netloc, path, self._query, self._fragment)

    def _str_with_empty(self) -> str:
        """Render a URL with empty components or without an authority."""
        if not self._path and self._netloc:
            path = "/"
        else:
            path = self._path
        if (port := self.explicit_port) is not None and port == DEFAULT_PORTS.get(
            self._scheme
        ):
            host = self.host_subcomponent
            netloc = make_netloc(self.raw_user, self.raw_password, host, None)
        else:
            netloc = self._netloc
        empty = self._str_empty if not netloc else self._empty
        if not empty:
            return unsplit_result(
                self._scheme, netloc, path, self._query, self._fragment
            )
        return unsplit_result_empty(
            self._scheme, netloc, path, self._query, self._fragment, empty
        )

    def __repr__(self) -> str:
        if self._mode is Mode.WHATWG:
            return f"{self.__class__.__name__}('{str(self)}')"
        return f"{self.__class__.__name__}('{str(self)}', mode='{self._mode}')"

    def __bytes__(self) -> bytes:
        return str(self).encode("ascii")

    def __eq__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented

        path1 = "/" if not self._path and self._netloc else self._path
        path2 = "/" if not other._path and other._netloc else other._path
        return (
            self._scheme == other._scheme
            and self._netloc == other._netloc
            and path1 == path2
            and self._query == other._query
            and self._fragment == other._fragment
            and (
                self._empty == other._empty
                if self._netloc
                else self._cmp_empty == other._cmp_empty
            )
        )

    def __hash__(self) -> int:
        if (ret := self._cache.get("hash")) is None:
            path = "/" if not self._path and self._netloc else self._path
            if (self._empty or not self._netloc) and (cmp_empty := self._cmp_empty):
                ret = hash(
                    (
                        self._scheme,
                        self._netloc,
                        path,
                        self._query,
                        self._fragment,
                        cmp_empty,
                    )
                )
            else:
                ret = hash(
                    (self._scheme, self._netloc, path, self._query, self._fragment)
                )
            self._cache["hash"] = ret
        return ret

    def __le__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return (self._val, self._cmp_empty) <= (other._val, other._cmp_empty)

    def __lt__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return (self._val, self._cmp_empty) < (other._val, other._cmp_empty)

    def __ge__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return (self._val, self._cmp_empty) >= (other._val, other._cmp_empty)

    def __gt__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return (self._val, self._cmp_empty) > (other._val, other._cmp_empty)

    def __truediv__(self, name: str) -> "URL":
        if not isinstance(name, str):
            return NotImplemented
        return self._make_child((str(name),))

    def __mod__(self, query: Query) -> "URL":
        return self.update_query(query)

    def __bool__(self) -> bool:
        return bool(
            self._netloc or self._path or self._query or self._fragment or self._empty
        )

    def __getstate__(
        self,
    ) -> tuple[SplitURLType, str, int] | tuple[SplitURLType, str, int, str]:
        # Return a plain tuple rather than a ``SplitResult``. Constructing a
        # ``SplitResult`` via ``tuple.__new__`` skips its ``__init__`` and on
        # Python 3.15+ leaves ``_keep_empty`` unset, which breaks pickling: the
        # new ``SplitResult.__getstate__`` indexes a state that ends up as
        # ``None`` (gh-1632). ``__setstate__`` already unpacks both shapes, so
        # pickles produced by older yarl releases (which embed a real
        # ``SplitResult``) still load correctly. The compatibility mode goes
        # second and the mask of empty components third; older releases
        # ignore trailing items of the state. The path that join() uses for
        # "http:g" (see _special_authority_url()) goes last, when there is one.
        if (join_path := self._cache.get("_join_path")) is not None:
            return (self._val, self._mode.value, self._empty, join_path)
        return (self._val, self._mode.value, self._empty)

    def __setstate__(
        self,
        # ``(val,)`` or ``(val, mode)`` from older releases,
        # ``(val, mode, empty)``, ``(val, mode, empty, join_path)``, or the
        # legacy default style
        # ``(None, {"_val": val})``.
        state: tuple[Any, ...],
    ) -> None:
        mode = Mode.WHATWG
        empty = 0
        cache: _InternalURLCache = {}
        if state[0] is None and isinstance(state[1], dict):
            # default style pickle
            val = state[1]["_val"]
        else:
            val, *rest = state
            if rest:
                mode = Mode(rest[0])
                if rest[1:]:
                    empty = rest[1]
                    if rest[2:]:
                        cache["_join_path"] = rest[2]
        self._scheme, self._netloc, self._path, self._query, self._fragment = val
        self._empty = empty
        self._cache = cache
        self._mode = mode

    def _cache_netloc(self) -> None:
        """Cache the netloc parts of the URL."""
        c = self._cache
        split_loc = split_netloc(self._netloc)
        c["raw_user"], c["raw_password"], c["raw_host"], c["explicit_port"] = split_loc

    def is_absolute(self) -> bool:
        """A check for absolute URLs.

        Return True for absolute ones (having scheme or starting
        with //), False otherwise.

        Is is preferred to call the .absolute property instead
        as it is cached.
        """
        return self.absolute

    def is_default_port(self) -> bool:
        """A check for default port.

        Return True if port is default for specified scheme,
        e.g. 'http://python.org' or 'http://python.org:80', False
        otherwise.

        Return False for relative URLs.

        """
        if (explicit := self.explicit_port) is None:
            # If the explicit port is None, then the URL must be
            # using the default port unless its a relative URL
            # which does not have an implicit port / default port
            return self._netloc != ""
        return explicit == DEFAULT_PORTS.get(self._scheme)

    def origin(self) -> "URL":
        """Return an URL with scheme, host and port parts only.

        user, password, path, query and fragment are removed.

        """
        # TODO: add a keyword-only option for keeping user/pass maybe?
        return self._origin

    @property
    def _cmp_empty(self) -> int:
        """The mask of empty components that matters for comparisons.

        It follows what str() writes out: in WHATWG mode a special scheme
        always prints "//", so "file:/p" and "file:///p" are the same URL
        there, while RFC mode prints and compares them differently.
        """
        if (
            not self._netloc
            and self._mode is _WHATWG
            and self._scheme in SPECIAL_SCHEMES
        ):
            return self._empty | EMPTY_AUTHORITY
        return self._empty

    @property
    def _str_empty(self) -> int:
        """The mask of empty components that str() writes out.

        In WHATWG mode a URL with a special scheme always has an authority,
        so "//" is written even when it is missing.
        """
        if self._mode is _WHATWG and self._scheme in SPECIAL_SCHEMES:
            return self._empty | EMPTY_AUTHORITY
        return self._empty

    @cached_property
    def _val(self) -> SplitURLType:
        return (self._scheme, self._netloc, self._path, self._query, self._fragment)

    @cached_property
    def _origin(self) -> "URL":
        """Return an URL with scheme, host and port parts only.

        user, password, path, query and fragment are removed.
        """
        if not (netloc := self._netloc):
            raise ValueError("URL should be absolute")
        if not (scheme := self._scheme):
            raise ValueError("URL should have scheme")
        if "@" in netloc:
            # The host is None for an authority without one ("user@:8080").
            encoded_host = self.host_subcomponent or ""
            netloc = make_netloc(None, None, encoded_host, self.explicit_port)
        elif not self._path and not self._query and not self._fragment:
            if not self._empty:
                return self
        return from_parts(scheme, netloc, "", "", "", self._mode)

    def relative(self) -> "URL":
        """Return a relative part of the URL.

        scheme, user, password, host and port are removed.

        """
        if not self._netloc:
            raise ValueError("URL should be absolute")
        return from_parts(
            "", "", self._path, self._query, self._fragment, self._mode, self._empty
        )

    @cached_property
    def absolute(self) -> bool:
        """A check for absolute URLs.

        Return True for absolute ones (having scheme or starting
        with //), False otherwise.

        """
        # `netloc`` is an empty string for relative URLs
        # Checking `netloc` is faster than checking `hostname`
        # because `hostname` is a property that does some extra work
        # to parse the host from the `netloc`
        return self._netloc != ""

    @cached_property
    def scheme(self) -> str:
        """Scheme for absolute URLs.

        Empty string for relative URLs or URLs starting with //

        """
        return self._scheme

    @cached_property
    def raw_authority(self) -> str:
        """Encoded authority part of URL.

        Empty string for relative URLs.

        """
        return self._netloc

    @cached_property
    def authority(self) -> str:
        """Decoded authority part of URL.

        Empty string for relative URLs.

        """
        if (host := self.host) is None and self._netloc:
            # An authority without a host, e.g. "user@:8080" in RFC mode.
            host = ""
        return make_netloc(self.user, self.password, host, self.port)

    @cached_property
    def raw_user(self) -> str | None:
        """Encoded user part of URL.

        None if user is missing.

        """
        # not .username
        self._cache_netloc()
        return self._cache["raw_user"]

    @cached_property
    def user(self) -> str | None:
        """Decoded user part of URL.

        None if user is missing.

        """
        if (raw_user := self.raw_user) is None:
            return None
        return UNQUOTER(raw_user)

    @cached_property
    def raw_password(self) -> str | None:
        """Encoded password part of URL.

        None if password is missing.

        """
        self._cache_netloc()
        return self._cache["raw_password"]

    @cached_property
    def password(self) -> str | None:
        """Decoded password part of URL.

        None if password is missing.

        """
        if (raw_password := self.raw_password) is None:
            return None
        return UNQUOTER(raw_password)

    @property
    def mode(self) -> Mode:
        """Standard the URL follows: RFC 3986 or the WHATWG URL Standard."""
        return self._mode

    @cached_property
    def raw_host(self) -> str | None:
        """Encoded host part of URL.

        None for relative URLs.

        When working with IPv6 addresses, use the `host_subcomponent` property instead
        as it will return the host subcomponent with brackets.
        """
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        self._cache_netloc()
        return self._cache["raw_host"]

    @cached_property
    def host(self) -> str | None:
        """Decoded host part of URL.

        None for relative URLs.

        For IPv6 hosts that carry an RFC 6874 zone identifier, the
        ``%25`` zone separator is decoded back to ``%``; the encoded
        form is still available via :attr:`raw_host` and
        :attr:`host_subcomponent`.

        """
        if (raw := self.raw_host) is None:
            return None
        if raw and raw[-1].isdigit() or ":" in raw:
            # IP addresses are never IDNA encoded. The replace decodes
            # every %25 in the raw host, i.e. the RFC 6874 zone
            # separator and any %25 that percent-encodes a literal %
            # inside the zone identifier.
            if "%25" in raw:
                return raw.replace("%25", "%")
            return raw
        return _idna_decode(raw)

    @cached_property
    def host_subcomponent(self) -> str | None:
        """Return the host subcomponent part of URL.

        None for relative URLs.

        https://datatracker.ietf.org/doc/html/rfc3986#section-3.2.2

        `IP-literal = "[" ( IPv6address / IPvFuture  ) "]"`

        Examples:
        - `http://example.com:8080` -> `example.com`
        - `http://example.com:80` -> `example.com`
        - `https://127.0.0.1:8443` -> `127.0.0.1`
        - `https://[::1]:8443` -> `[::1]`
        - `http://[::1]` -> `[::1]`

        """
        if (raw := self.raw_host) is None:
            return None
        return f"[{raw}]" if ":" in raw else raw

    @cached_property
    def host_port_subcomponent(self) -> str | None:
        """Return the host and port subcomponent part of URL.

        Trailing dots are removed from the host part.

        This value is suitable for use in the Host header of an HTTP request.

        None for relative URLs.

        https://datatracker.ietf.org/doc/html/rfc3986#section-3.2.2
        `IP-literal = "[" ( IPv6address / IPvFuture  ) "]"`
        https://datatracker.ietf.org/doc/html/rfc3986#section-3.2.3
        port        = *DIGIT

        Examples:
        - `http://example.com:8080` -> `example.com:8080`
        - `http://example.com:80` -> `example.com`
        - `http://example.com.:80` -> `example.com`
        - `https://127.0.0.1:8443` -> `127.0.0.1:8443`
        - `https://[::1]:8443` -> `[::1]:8443`
        - `http://[::1]` -> `[::1]`

        """
        if (raw := self.raw_host) is None:
            return None
        if raw and raw[-1] == ".":
            # Remove all trailing dots from the netloc as while
            # they are valid FQDNs in DNS, TLS validation fails.
            # See https://github.com/aio-libs/aiohttp/issues/3636.
            # To avoid string manipulation we only call rstrip if
            # the last character is a dot.
            raw = raw.rstrip(".")
        port = self.explicit_port
        if port is None or port == DEFAULT_PORTS.get(self._scheme):
            return f"[{raw}]" if ":" in raw else raw
        return f"[{raw}]:{port}" if ":" in raw else f"{raw}:{port}"

    @cached_property
    def port(self) -> int | None:
        """Port part of URL, with scheme-based fallback.

        None for relative URLs or URLs without explicit port and
        scheme without default port substitution.

        """
        if (explicit_port := self.explicit_port) is not None:
            return explicit_port
        return DEFAULT_PORTS.get(self._scheme)

    @cached_property
    def explicit_port(self) -> int | None:
        """Port part of URL, without scheme-based fallback.

        None for relative URLs or URLs without explicit port.

        """
        self._cache_netloc()
        return self._cache["explicit_port"]

    @cached_property
    def raw_path(self) -> str:
        """Encoded path of URL.

        / for absolute URLs without path part.

        """
        return self._path if self._path or not self._netloc else "/"

    @cached_property
    def path(self) -> str:
        """Decoded path of URL.

        / for absolute URLs without path part.

        """
        return UNQUOTER(self._path) if self._path else "/" if self._netloc else ""

    @cached_property
    def path_safe(self) -> str:
        """Decoded path of URL.

        / for absolute URLs without path part.

        / (%2F) and % (%25) are not decoded

        """
        if self._path:
            return PATH_SAFE_UNQUOTER(self._path)
        return "/" if self._netloc else ""

    @cached_property
    def _parsed_query(self) -> list[tuple[str, str]]:
        """Parse query part of URL."""
        return query_to_pairs(self._query)

    @cached_property
    def query(self) -> "MultiDictProxy[str]":
        """A MultiDictProxy representing parsed query parameters in decoded
        representation.

        Empty value if URL has no query part.

        """
        return MultiDictProxy(MultiDict(self._parsed_query))

    @cached_property
    def raw_query_string(self) -> str:
        """Encoded query part of URL.

        Empty string if query is missing.

        """
        return self._query

    @cached_property
    def query_string(self) -> str:
        """Decoded query part of URL.

        Empty string if query is missing.

        """
        return QS_UNQUOTER(self._query) if self._query else ""

    @cached_property
    def path_qs(self) -> str:
        """Decoded path of URL with query."""
        if q := self.query_string:
            return f"{self.path}?{q}"
        if (empty := self._empty) and empty & EMPTY_QUERY:
            return f"{self.path}?"
        return self.path

    @cached_property
    def raw_path_qs(self) -> str:
        """Encoded path of URL with query."""
        if q := self._query:
            return f"{self._path}?{q}" if self._path or not self._netloc else f"/?{q}"
        if (empty := self._empty) and empty & EMPTY_QUERY:
            return f"{self._path}?" if self._path or not self._netloc else "/?"
        return self._path if self._path or not self._netloc else "/"

    @cached_property
    def raw_fragment(self) -> str:
        """Encoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return self._fragment

    @cached_property
    def fragment(self) -> str:
        """Decoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return UNQUOTER(self._fragment) if self._fragment else ""

    @cached_property
    def raw_parts(self) -> tuple[str, ...]:
        """A tuple containing encoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
        path = self._path
        if self._netloc or self._empty & EMPTY_AUTHORITY:
            return ("/", *path[1:].split("/")) if path else ("/",)
        if path and path[0] == "/":
            return ("/", *path[1:].split("/"))
        return tuple(path.split("/"))

    @cached_property
    def parts(self) -> tuple[str, ...]:
        """A tuple containing decoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
        return tuple(UNQUOTER(part) for part in self.raw_parts)

    @cached_property
    def parent(self) -> "URL":
        """A new URL with last part of path removed and cleaned up query and
        fragment.

        """
        path = self._path
        authority_empty = self._empty & EMPTY_AUTHORITY
        if not path or path == "/":
            if self._fragment or self._query or self._empty & ~EMPTY_AUTHORITY:
                return from_parts(
                    self._scheme,
                    self._netloc,
                    path,
                    "",
                    "",
                    self._mode,
                    authority_empty,
                )
            return self
        parts = path.split("/")
        return from_parts(
            self._scheme,
            self._netloc,
            "/".join(parts[:-1]),
            "",
            "",
            self._mode,
            authority_empty,
        )

    @cached_property
    def raw_name(self) -> str:
        """The last part of raw_parts."""
        parts = self.raw_parts
        if not self._netloc:
            return parts[-1]
        parts = parts[1:]
        return parts[-1] if parts else ""

    @cached_property
    def name(self) -> str:
        """The last part of parts."""
        return UNQUOTER(self.raw_name)

    @cached_property
    def raw_suffix(self) -> str:
        name = self.raw_name
        i = name.rfind(".")
        return name[i:] if 0 < i < len(name) - 1 else ""

    @cached_property
    def suffix(self) -> str:
        return UNQUOTER(self.raw_suffix)

    @cached_property
    def raw_suffixes(self) -> tuple[str, ...]:
        name = self.raw_name
        if name.endswith("."):
            return ()
        name = name.lstrip(".")
        return tuple("." + suffix for suffix in name.split(".")[1:])

    @cached_property
    def suffixes(self) -> tuple[str, ...]:
        return tuple(UNQUOTER(suffix) for suffix in self.raw_suffixes)

    def _make_child(self, paths: "Sequence[str]", encoded: bool = False) -> "URL":
        """
        add paths to self._path, accounting for absolute vs relative paths,
        keep existing, but do not create new, empty segments
        """
        parsed: list[str] = []
        needs_normalize: bool = False
        for idx, path in enumerate(reversed(paths)):
            # empty segment of last is not removed
            last = idx == 0
            if path and path[0] == "/":
                raise ValueError(
                    f"Appending path {path!r} starting from slash is forbidden"
                )
            # We need to quote the path if it is not already encoded
            # This cannot be done at the end because the existing
            # path is already quoted and we do not want to double quote
            # the existing path.
            path = path if encoded else PATH_QUOTER(path)
            needs_normalize |= "." in path
            segments = path.split("/")
            segments.reverse()
            # remove trailing empty segment for all but the last path
            parsed += segments[1:] if not last and segments[0] == "" else segments

        if (path := self._path) and (old_segments := path.split("/")):
            # If the old path ends with a slash, the last segment is an empty string
            # and should be removed before adding the new path segments.
            old = old_segments[:-1] if old_segments[-1] == "" else old_segments
            old.reverse()
            parsed += old

        # If the netloc is present, inject a leading slash when adding a
        # path to an absolute URL where there was none before.
        netloc = self._netloc
        authority_empty = self._empty & EMPTY_AUTHORITY
        has_authority = netloc or authority_empty
        if has_authority and parsed and parsed[-1] != "":
            parsed.append("")

        parsed.reverse()
        if not has_authority or not needs_normalize:
            return from_parts(
                self._scheme,
                netloc,
                "/".join(parsed),
                "",
                "",
                self._mode,
                authority_empty,
            )

        path = "/".join(normalize_path_segments(parsed))
        # If normalizing the path segments removed the leading slash, add it back.
        if path and path[0] != "/":
            path = f"/{path}"
        return from_parts(
            self._scheme, netloc, path, "", "", self._mode, authority_empty
        )

    def with_scheme(self, scheme: str) -> "URL":
        """Return a new URL with scheme replaced."""
        # N.B. doesn't cleanup query/fragment
        if not isinstance(scheme, str):
            raise TypeError("Invalid scheme type")
        lower_scheme = scheme.lower()
        netloc = self._netloc
        if not netloc and lower_scheme in SCHEME_REQUIRES_HOST:
            msg = (
                "scheme replacement is not allowed for "
                f"relative URLs for the {lower_scheme} scheme"
            )
            raise ValueError(msg)
        if self._scheme not in SPECIAL_SCHEMES and netloc:
            # A special scheme in WHATWG mode had its host parsed already.
            netloc = _moved_netloc(self, lower_scheme, self._mode)
        return from_parts(
            lower_scheme,
            netloc,
            self._path,
            self._query,
            self._fragment,
            self._mode,
            self._empty,
        )

    def with_user(self, user: str | None) -> "URL":
        """Return a new URL with user replaced.

        Autoencode user if needed.

        Clear user/password if user is None.

        """
        # N.B. doesn't cleanup query/fragment
        if user is None:
            password = None
        elif isinstance(user, str):
            user = QUOTER(user)
            password = self.raw_password
        else:
            raise TypeError("Invalid user type")
        if not (netloc := self._netloc):
            raise ValueError("user replacement is not allowed for relative URLs")
        encoded_host = self.host_subcomponent or ""
        netloc = make_netloc(user, password, encoded_host, self.explicit_port)
        return from_parts(
            self._scheme,
            netloc,
            self._path,
            self._query,
            self._fragment,
            self._mode,
            self._empty,
        )

    def with_password(self, password: str | None) -> "URL":
        """Return a new URL with password replaced.

        Autoencode password if needed.

        Clear password if argument is None.

        """
        # N.B. doesn't cleanup query/fragment
        if password is None:
            pass
        elif isinstance(password, str):
            password = QUOTER(password)
        else:
            raise TypeError("Invalid password type")
        if not (netloc := self._netloc):
            raise ValueError("password replacement is not allowed for relative URLs")
        encoded_host = self.host_subcomponent or ""
        port = self.explicit_port
        netloc = make_netloc(self.raw_user, password, encoded_host, port)
        return from_parts(
            self._scheme,
            netloc,
            self._path,
            self._query,
            self._fragment,
            self._mode,
            self._empty,
        )

    def with_host(self, host: str) -> "URL":
        """Return a new URL with host replaced.

        Autoencode host if needed.

        Changing host for relative URLs is not allowed, use .join()
        instead.

        """
        # N.B. doesn't cleanup query/fragment
        if not isinstance(host, str):
            raise TypeError("Invalid host type")
        if not (netloc := self._netloc):
            raise ValueError("host replacement is not allowed for relative URLs")
        if not host:
            raise ValueError("host removing is not allowed")
        encoded_host, whatwg_host, idna2003 = _encode_host(host, validate_host=True)
        if idna2003 and self._mode is not _WHATWG:
            raise ValueError(_idna2003_host_error(host))
        if (
            whatwg_host is not encoded_host
            and self._mode is _WHATWG
            and self._scheme in SPECIAL_SCHEMES
        ):
            encoded_host = _whatwg_special_host(encoded_host, whatwg_host)
        port = self.explicit_port
        netloc = make_netloc(self.raw_user, self.raw_password, encoded_host, port)
        return from_parts(
            self._scheme,
            netloc,
            self._path,
            self._query,
            self._fragment,
            self._mode,
            self._empty,
        )

    def with_port(self, port: int | None) -> "URL":
        """Return a new URL with port replaced.

        Clear port to default if None is passed.

        """
        # N.B. doesn't cleanup query/fragment
        if port is not None:
            if isinstance(port, bool) or not isinstance(port, int):
                raise TypeError(f"port should be int or None, got {type(port)}")
            if not (0 <= port <= 65535):
                raise ValueError(f"port must be between 0 and 65535, got {port}")
        if not (netloc := self._netloc):
            raise ValueError("port replacement is not allowed for relative URLs")
        encoded_host = self.host_subcomponent or ""
        netloc = make_netloc(self.raw_user, self.raw_password, encoded_host, port)
        return from_parts(
            self._scheme,
            netloc,
            self._path,
            self._query,
            self._fragment,
            self._mode,
            self._empty,
        )

    def with_path(
        self,
        path: str,
        *,
        encoded: bool = False,
        keep_query: bool = False,
        keep_fragment: bool = False,
    ) -> "URL":
        """Return a new URL with path replaced."""
        netloc = self._netloc
        if not encoded:
            path = PATH_QUOTER(path)
            if netloc:
                path = normalize_path(path) if "." in path else path
        if path and path[0] != "/":
            path = f"/{path}"
        query = self._query if keep_query else ""
        fragment = self._fragment if keep_fragment else ""
        if empty := self._empty:
            empty &= _kept_empty(keep_query, keep_fragment)
            return from_parts(
                self._scheme, netloc, path, query, fragment, self._mode, empty
            )
        return from_parts(self._scheme, netloc, path, query, fragment, self._mode)

    @overload
    def with_query(self, query: Query) -> "URL": ...

    @overload
    def with_query(self, **kwargs: QueryVariable) -> "URL": ...

    def with_query(self, *args: Any, **kwargs: Any) -> "URL":
        """Return a new URL with query part replaced.

        Accepts any Mapping (e.g. dict, multidict.MultiDict instances)
        or str, autoencode the argument if needed.

        A sequence of (key, value) pairs is supported as well.

        It also can take an arbitrary number of keyword arguments.

        Clear query if None is passed.

        """
        # N.B. doesn't cleanup query/fragment
        query = get_str_query(*args, **kwargs) or ""
        return from_parts_uncached(
            self._scheme,
            self._netloc,
            self._path,
            query,
            self._fragment,
            self._mode,
            self._empty and self._empty & ~EMPTY_QUERY,
        )

    @overload
    def extend_query(self, query: Query) -> "URL": ...

    @overload
    def extend_query(self, **kwargs: QueryVariable) -> "URL": ...

    def extend_query(self, *args: Any, **kwargs: Any) -> "URL":
        """Return a new URL with query part combined with the existing.

        This method will not remove existing query parameters.

        Example:
        >>> url = URL('http://example.com/?a=1&b=2')
        >>> url.extend_query(a=3, c=4)
        URL('http://example.com/?a=1&b=2&a=3&c=4')
        """
        if not (new_query := get_str_query(*args, **kwargs)):
            return self
        if query := self._query:
            # both strings are already encoded so we can use a simple
            # string join
            query += new_query if query[-1] == "&" else f"&{new_query}"
        else:
            query = new_query
        return from_parts_uncached(
            self._scheme,
            self._netloc,
            self._path,
            query,
            self._fragment,
            self._mode,
            self._empty and self._empty & ~EMPTY_QUERY,
        )

    @overload
    def update_query(self, query: Query) -> "URL": ...

    @overload
    def update_query(self, **kwargs: QueryVariable) -> "URL": ...

    def update_query(self, *args: Any, **kwargs: Any) -> "URL":
        """Return a new URL with query part updated.

        This method will overwrite existing query parameters.

        Example:
        >>> url = URL('http://example.com/?a=1&b=2')
        >>> url.update_query(a=3, c=4)
        URL('http://example.com/?a=3&b=2&c=4')
        """
        in_query: (
            str
            | Mapping[str, QueryVariable]
            | Sequence[tuple[str | istr, SimpleQuery]]
            | None
        )
        if kwargs:
            if args:
                msg = "Either kwargs or single query parameter must be present"
                raise ValueError(msg)
            in_query = kwargs
        elif len(args) == 1:
            in_query = args[0]
        else:
            raise ValueError("Either kwargs or single query parameter must be present")

        if in_query is None:
            query = ""
        elif not in_query:
            query = self._query
        elif isinstance(in_query, Mapping):
            qm: MultiDict[QueryVariable] = MultiDict(self._parsed_query)
            qm.update(in_query)
            query = get_str_query_from_sequence_iterable(qm.items())
        elif isinstance(in_query, str):
            qstr: MultiDict[str] = MultiDict(self._parsed_query)
            qstr.update(query_to_pairs(in_query))
            query = get_str_query_from_iterable(qstr.items())
        elif isinstance(in_query, (bytes, bytearray, memoryview)):
            msg = "Invalid query type: bytes, bytearray and memoryview are forbidden"
            raise TypeError(msg)
        elif isinstance(in_query, Sequence):
            # We don't expect sequence values if we're given a list of pairs
            # already; only mappings like builtin `dict` which can't have the
            # same key pointing to multiple values are allowed to use
            # `_query_seq_pairs`.
            if TYPE_CHECKING:
                in_query = cast(
                    Sequence[tuple[Union[str, istr], SimpleQuery]], in_query
                )
            qs: MultiDict[SimpleQuery] = MultiDict(self._parsed_query)
            qs.update(in_query)
            query = get_str_query_from_iterable(qs.items())
        else:
            raise TypeError(
                "Invalid query type: only str, mapping or "
                "sequence of (key, value) pairs is allowed"
            )
        if not (empty := self._empty):
            return from_parts_uncached(
                self._scheme,
                self._netloc,
                self._path,
                query,
                self._fragment,
                self._mode,
            )
        # An empty query stays when nothing is added, "None" removes it.
        if query or in_query is None:
            empty &= ~EMPTY_QUERY
        return from_parts_uncached(
            self._scheme,
            self._netloc,
            self._path,
            query,
            self._fragment,
            self._mode,
            empty,
        )

    def without_query_params(self, *query_params: str) -> "URL":
        """Remove some keys from query part and return new URL."""
        params_to_remove = set(query_params) & self.query.keys()
        if not params_to_remove:
            return self
        return self.with_query(
            tuple(
                (name, value)
                for name, value in self.query.items()
                if name not in params_to_remove
            )
        )

    def with_fragment(self, fragment: str | None) -> "URL":
        """Return a new URL with fragment replaced.

        Autoencode fragment if needed.

        Clear fragment to default if None is passed.

        """
        # N.B. doesn't cleanup query/fragment
        if fragment is None:
            raw_fragment = ""
        elif not isinstance(fragment, str):
            raise TypeError("Invalid fragment type")
        else:
            raw_fragment = FRAGMENT_QUOTER(fragment)
        if empty := self._empty:
            if self._fragment == raw_fragment and not empty & EMPTY_FRAGMENT:
                return self
            return from_parts(
                self._scheme,
                self._netloc,
                self._path,
                self._query,
                raw_fragment,
                self._mode,
                empty & ~EMPTY_FRAGMENT,
            )
        if self._fragment == raw_fragment:
            return self
        return from_parts(
            self._scheme,
            self._netloc,
            self._path,
            self._query,
            raw_fragment,
            self._mode,
        )

    def with_name(
        self,
        name: str,
        *,
        keep_query: bool = False,
        keep_fragment: bool = False,
    ) -> "URL":
        """Return a new URL with name (last part of path) replaced.

        Query and fragment parts are cleaned up.

        Name is encoded if needed.

        """
        # N.B. DOES cleanup query/fragment
        if not isinstance(name, str):
            raise TypeError("Invalid name type")
        if "/" in name:
            raise ValueError("Slash in name is not allowed")
        name = PATH_QUOTER(name)
        if name in (".", ".."):
            raise ValueError(". and .. values are forbidden")
        parts = list(self.raw_parts)
        netloc = self._netloc
        if netloc or self._empty & EMPTY_AUTHORITY:
            if len(parts) == 1:
                parts.append(name)
            else:
                parts[-1] = name
            parts[0] = ""  # replace leading '/'
        else:
            parts[-1] = name
            if parts[0] == "/":
                parts[0] = ""  # replace leading '/'

        query = self._query if keep_query else ""
        fragment = self._fragment if keep_fragment else ""
        if empty := self._empty:
            empty &= _kept_empty(keep_query, keep_fragment)
            return from_parts(
                self._scheme,
                netloc,
                "/".join(parts),
                query,
                fragment,
                self._mode,
                empty,
            )
        return from_parts(
            self._scheme, netloc, "/".join(parts), query, fragment, self._mode
        )

    def with_suffix(
        self,
        suffix: str,
        *,
        keep_query: bool = False,
        keep_fragment: bool = False,
    ) -> "URL":
        """Return a new URL with suffix (file extension of name) replaced.

        Query and fragment parts are cleaned up.

        suffix is encoded if needed.
        """
        if not isinstance(suffix, str):
            raise TypeError("Invalid suffix type")
        if suffix and not suffix[0] == "." or suffix == "." or "/" in suffix:
            raise ValueError(f"Invalid suffix {suffix!r}")
        name = self.raw_name
        if not name:
            raise ValueError(f"{self!r} has an empty name")
        old_suffix = self.raw_suffix
        suffix = PATH_QUOTER(suffix)
        name = name + suffix if not old_suffix else name[: -len(old_suffix)] + suffix
        if name in (".", ".."):
            raise ValueError(". and .. values are forbidden")
        parts = list(self.raw_parts)
        netloc = self._netloc
        if netloc or self._empty & EMPTY_AUTHORITY:
            if len(parts) == 1:
                parts.append(name)
            else:
                parts[-1] = name
            parts[0] = ""  # replace leading '/'
        else:
            parts[-1] = name
            if parts[0] == "/":
                parts[0] = ""  # replace leading '/'

        query = self._query if keep_query else ""
        fragment = self._fragment if keep_fragment else ""
        if empty := self._empty:
            empty &= _kept_empty(keep_query, keep_fragment)
            return from_parts(
                self._scheme,
                netloc,
                "/".join(parts),
                query,
                fragment,
                self._mode,
                empty,
            )
        return from_parts(
            self._scheme, netloc, "/".join(parts), query, fragment, self._mode
        )

    def join(self, url: "URL") -> "URL":
        """Join URLs

        Construct a full (“absolute”) URL by combining a “base URL”
        (self) with another URL (url).

        Informally, this uses components of the base URL, in
        particular the addressing scheme, the network location and
        (part of) the path, to provide missing components in the
        relative URL.

        """
        if type(url) is not URL:
            raise TypeError("url should be URL")

        scheme = url._scheme or self._scheme
        # A reference with a scheme is used as is (RFC 3986 section 5.2.2),
        # except that "http:g" is still resolved against an http base, the
        # backward-compatible behavior RFC 3986 section 5.4.2 permits.
        if scheme != self._scheme or (url._scheme and scheme not in USES_RELATIVE):
            # The result follows the base URL's compatibility mode.
            return url if url._mode is self._mode else URL(url, mode=self._mode)

        if url._netloc and (join_path := url._cache.get("_join_path")) is not None:
            # "http:g" was parsed in WHATWG mode as "http://g/", but against
            # an http base it is the relative reference "g".
            url = from_parts(
                scheme, "", join_path, url._query, url._fragment, url._mode, url._empty
            )

        if url._empty or self._empty:
            return self._join_with_empty(url, scheme)

        if join_netloc := url._netloc:
            if not url._scheme or url._mode is not _WHATWG:
                # A schemeless or RFC-mode reference had no WHATWG host check.
                join_netloc = _moved_netloc(url, scheme, self._mode)
            return from_parts(
                scheme, join_netloc, url._path, url._query, url._fragment, self._mode
            )

        orig_path = self._path
        if join_path := url._path:
            if join_path[0] == "/":
                path = join_path
            elif not orig_path:
                path = f"/{join_path}" if self._netloc else join_path
            elif orig_path[-1] == "/":
                path = f"{orig_path}{join_path}"
            else:
                # Merge on the encoded base path, dropping its last segment,
                # so percent-encoded delimiters in the base are kept as is.
                path = orig_path[: orig_path.rfind("/") + 1] + join_path
            path = normalize_path(path) if "." in path else path
        else:
            path = orig_path

        return from_parts(
            scheme,
            self._netloc,
            path,
            url._query if join_path or url._query else self._query,
            url._fragment,
            self._mode,
        )

    def _join_with_empty(self, url: "URL", scheme: str) -> "URL":
        """join() for URLs with empty components; the same algorithm as
        join() takes for other URLs, plus the empty component rules."""
        join_empty = url._empty
        # An empty authority in the reference wins only where a URL may have
        # an empty host; for http and friends "///a" keeps the base host.
        if url._netloc or (
            join_empty & EMPTY_AUTHORITY and scheme not in SCHEME_REQUIRES_HOST
        ):
            join_netloc = url._netloc
            if not url._scheme or url._mode is not _WHATWG:
                join_netloc = _moved_netloc(url, scheme, self._mode)
            return from_parts(
                scheme,
                join_netloc,
                url._path,
                url._query,
                url._fragment,
                self._mode,
                join_empty,
            )

        orig_path = self._path
        has_authority = self._netloc or self._empty & EMPTY_AUTHORITY
        if join_path := url._path:
            if join_path[0] == "/":
                path = join_path
            elif not orig_path:
                path = f"/{join_path}" if has_authority else join_path
            elif orig_path[-1] == "/":
                path = f"{orig_path}{join_path}"
            else:
                # Merge on the encoded base path, dropping its last segment,
                # so percent-encoded delimiters in the base are kept as is.
                path = orig_path[: orig_path.rfind("/") + 1] + join_path
            path = normalize_path(path) if "." in path else path
        else:
            path = orig_path

        # The query comes from the reference when it has a path or a query,
        # and the fragment always does, per RFC 3986 section 5.2.2.
        if join_path or url._query or join_empty & EMPTY_QUERY:
            query = url._query
            query_empty = join_empty & EMPTY_QUERY
        else:
            query = self._query
            query_empty = self._empty & EMPTY_QUERY
        return from_parts(
            scheme,
            self._netloc,
            path,
            query,
            url._fragment,
            self._mode,
            self._empty & EMPTY_AUTHORITY | query_empty | join_empty & EMPTY_FRAGMENT,
        )

    def joinpath(self, *other: str, encoded: bool = False) -> "URL":
        """Return a new URL with the elements in other appended to the path."""
        return self._make_child(other, encoded=encoded)

    def human_repr(self) -> str:
        """Return decoded human readable string for URL representation."""
        user = human_quote(self.user, "#/:?@[]\\")
        password = human_quote(self.password, "#/:?@[]\\")
        if (host := self.host) and ":" in host:
            host = f"[{host}]"
        path = human_quote(self.path, "#?")
        if TYPE_CHECKING:
            assert path is not None
        if not self._scheme and not self._netloc:
            path = _encode_relative_scheme_colon(path)
        query_string = "&".join(
            "{}={}".format(human_quote(k, "#&+;="), human_quote(v, "#&+;="))
            for k, v in self.query.items()
        )
        fragment = human_quote(self.fragment, "")
        if TYPE_CHECKING:
            assert fragment is not None
        if host is None and self._netloc:
            host = ""  # an authority without a host, e.g. "user@:8080"
        netloc = make_netloc(user, password, host, self.explicit_port)
        if empty := self._str_empty:
            return unsplit_result_empty(
                self._scheme, netloc, path, query_string, fragment, empty
            )
        return unsplit_result(self._scheme, netloc, path, query_string, fragment)

    if HAS_PYDANTIC:
        # Borrowed from https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types
        @classmethod
        def __get_pydantic_json_schema__(
            cls,
            core_schema: "CoreSchema",
            handler: "GetJsonSchemaHandler",
        ) -> "JsonSchemaValue":
            field_schema: dict[str, Any] = {}
            field_schema.update(type="string", format="uri")
            return field_schema

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: type[Self] | type[str],
            handler: "GetCoreSchemaHandler",
        ) -> "CoreSchema":
            # Lazy import: pulling in pydantic_core at module load time
            # increases yarl's import cost 3-7x for users who don't use
            # pydantic. Keep this import function-scoped.
            from pydantic_core import core_schema  # noqa: PLC0415

            from_str_schema = core_schema.chain_schema(
                [
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(URL),
                ]
            )

            return core_schema.json_or_python_schema(
                json_schema=from_str_schema,
                python_schema=core_schema.union_schema(
                    [
                        # check if it's an instance first before doing any further work
                        core_schema.is_instance_schema(URL),
                        from_str_schema,
                    ]
                ),
                serialization=core_schema.plain_serializer_function_ser_schema(str),
            )


_DEFAULT_IDNA_SIZE = 256
_DEFAULT_ENCODE_SIZE = 512


@lru_cache(_DEFAULT_IDNA_SIZE)
def _idna_decode(raw: str) -> str:
    try:
        return idna.decode(raw.encode("ascii"))
    except UnicodeError:  # e.g. '::1'
        return raw.encode("ascii").decode("idna")


@lru_cache(_DEFAULT_IDNA_SIZE)
def _idna_encode(host: str) -> tuple[str, bool]:
    """Encode a host with IDNA2008 and UTS #46, or else with IDNA2003.

    The flag tells if the IDNA2003 fallback was needed, which RFC 3986 mode
    rejects.
    """
    try:
        return idna.encode(host, uts46=True).decode("ascii"), False
    except UnicodeError:
        return host.encode("idna").decode("ascii"), True


_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
# A host that ends in a number ends in one of these; most hosts do not.
_NUMERIC_HOST_TAIL = frozenset("0123456789abcdefxABCDEFX.")


def _moved_netloc(url: "URL", scheme: str, mode: Mode) -> str:
    """Return the netloc of url moved under scheme and mode.

    with_scheme(), join() and a change of mode can move a host that was
    parsed under another scheme or mode into a special-scheme WHATWG URL,
    where the host is percent-decoded and one that ends in a number is
    parsed as an IPv4 address.
    """
    netloc = url._netloc
    if mode is _WHATWG and scheme in SPECIAL_SCHEMES and (host := url.raw_host):
        # The WHATWG host is cached with the encoding of the host.
        encoded, whatwg_host, _ = _encode_host(host, False)
        if whatwg_host is not encoded:
            host = _whatwg_special_host(encoded, whatwg_host)
            netloc = make_netloc(
                url.raw_user, url.raw_password, host, url.explicit_port
            )
    return netloc


def _whatwg_special_host(host: str, whatwg_host: str | None) -> str:
    """Return the host WHATWG parses a special-scheme host as.

    The WHATWG URL Standard percent-decodes the host and parses a host whose
    last label is a number, like "0x7f.1" or "example.123", as an IPv4
    address. It fails when the decoded host is not a valid domain, a label
    is not a number or a number is out of range. RFC 3986 mode accepts all
    of them as a reg-name.
    """
    if whatwg_host is None:
        if "%" in host:
            raise ValueError(f"Host {host!r} is not a valid host once percent-decoded")
        raise ValueError(f"Host {host!r} ends in a number but is not an IPv4 address")
    return whatwg_host


# A number with more significant digits than this in its base is at least
# 2**32, out of range for any part of an IPv4 address. Checking the length
# first keeps int() away from huge labels, which Python refuses to convert.
_IPV4_MAX_DIGITS = {16: 8, 8: 11, 10: 10}
_IPV4_OUT_OF_RANGE = 2**32


def _ipv4_number(label: str) -> int | None:
    """Parse a WHATWG IPv4 number: decimal, 0x hex or 0 octal."""
    if label[:2] in ("0x", "0X"):
        digits, base = label[2:], 16
        if not all(c in _HEX_DIGITS for c in digits):
            return None
    elif label == "" or not label.isascii() or not label.isdigit():
        return None
    elif label[0] == "0" and len(label) > 1:
        digits, base = label[1:], 8
        if "8" in digits or "9" in digits:
            return None
    else:
        digits, base = label, 10
    digits = digits.lstrip("0")
    if len(digits) > _IPV4_MAX_DIGITS[base]:
        return _IPV4_OUT_OF_RANGE
    return int(digits, base) if digits else 0


def _whatwg_numeric_host(host: str) -> str | None:
    """Return host as WHATWG sees it for a special scheme.

    A host that does not end in a number is returned as is. One that does
    is run through the WHATWG IPv4 parser: the result is the dotted-quad
    serialization, or None when parsing fails. The host must not be
    percent-encoded; see _whatwg_decoded_host.
    """
    if host[-1] not in _NUMERIC_HOST_TAIL:
        return host
    labels = host.split(".")
    if labels[-1] == "" and len(labels) > 1:
        labels.pop()
    last = labels[-1]
    if not (last.isascii() and last.isdigit()) and _ipv4_number(last) is None:
        return host
    if len(labels) > 4:
        return None
    numbers = [_ipv4_number(label) for label in labels]
    *head, tail = numbers
    if tail is None or tail >= 256 ** (5 - len(numbers)):
        return None
    address = tail
    for i, number in enumerate(head):
        if number is None or number > 255:
            return None
        address += number << (8 * (3 - i))
    return ".".join(str(address >> shift & 255) for shift in (24, 16, 8, 0))


def _whatwg_decoded_host(host: str) -> str | None:
    """Return a percent-encoded host as WHATWG sees it for a special scheme.

    The WHATWG host parser percent-decodes the host, decodes the bytes as
    UTF-8 with U+FFFD for invalid sequences and runs domain to ASCII, so
    "%e2%98%83" is "xn--n3h" and "ho%00st" fails. The result goes on to
    the IPv4 parser like any other host. None means WHATWG fails, or gives
    a host that yarl rejects anyway, like one with a default-ignorable code
    point or a character outside the RFC 3986 reg-name.
    """
    decoded = unquote_to_bytes(host).decode("utf-8", "replace")
    if decoded.isascii():
        decoded = decoded.lower()
    elif _DEFAULT_IGNORABLE_RE.search(decoded):
        return None
    else:
        try:
            decoded = _idna_encode(decoded)[0]
        except UnicodeError:
            return None
    if "%" in decoded or NOT_REG_NAME.search(decoded):
        return None
    return _whatwg_numeric_host(decoded)


@lru_cache(_DEFAULT_ENCODE_SIZE)
def _encode_host(
    host: str, validate_host: bool, *, reject_empty_zone: bool = True
) -> tuple[str, str | None, bool]:
    """Encode host part of URL.

    Next to the encoded host, return the host WHATWG sees for a special
    scheme, which is the encoded host itself unless the host is
    percent-encoded (see _whatwg_decoded_host) or ends in a number (see
    _whatwg_numeric_host), and a flag that tells if IDNA2008
    could not encode the host, which RFC 3986 mode rejects. Both are
    computed here so that the checks are cached with the encoding.
    """
    # If the host ends with a digit or contains a colon, its likely
    # an IP address.
    if host and (host[-1].isdigit() or ":" in host):
        # RFC 6874 spells the IPv6 zone separator as the percent-encoded
        # ``%25``; bare ``%`` is still accepted so that hosts constructed
        # programmatically (e.g. ``with_host("fe80::1%1")``) keep working.
        part = "%25" if "%25" in host else "%"
        raw_ip, sep, zone = host.partition(part)
        # If it looks like an IP, we check with _ip_compressed_version
        # and fall-through if its not an IP address. This is a performance
        # optimization to avoid parsing IP addresses as much as possible
        # because it is orders of magnitude slower than almost any other
        # operation this library does.
        # Might be an IP address, check it
        #
        # IP Addresses can look like:
        # https://datatracker.ietf.org/doc/html/rfc3986#section-3.2.2
        # - 127.0.0.1 (last character is a digit)
        # - 2001:db8::ff00:42:8329 (contains a colon)
        # - 2001:db8::ff00:42:8329%eth0 (contains a colon)
        # - [2001:db8::ff00:42:8329] (contains a colon -- brackets should
        #                             have been removed before it gets here)
        # Rare IP Address formats are not supported per:
        # https://datatracker.ietf.org/doc/html/rfc3986#section-7.4
        #
        # IP parsing is slow, so its wrapped in an LRU
        try:
            ip = ip_address(raw_ip)
        except ValueError:
            pass
        else:
            if (
                sep
                and validate_host
                and (
                    (reject_empty_zone and not zone) or _ZONE_ID_UNSAFE_RE.search(zone)
                )
            ):
                raise ValueError("Invalid characters in zone identifier")
            # These checks should not happen in the
            # LRU to keep the cache size small
            host = ip.compressed
            if ip.version == 6:
                host = f"[{host}{sep}{zone}]" if sep else f"[{host}]"
            elif sep:
                # WHATWG has no zone identifiers: "%" after an IPv4 address
                # is percent-encoding in the host.
                host = f"{host}{sep}{zone}"
                return host, _whatwg_decoded_host(host), False
            return host, host, False

    # IDNA encoding is slow, skip it for ASCII-only strings
    if host.isascii():
        # Check for invalid characters explicitly; _idna_encode() does this
        # for non-ascii host names.
        host = host.lower()
        if validate_host and (invalid := NOT_REG_NAME.search(host)):
            value, pos, extra = invalid.group(), invalid.start(), ""
            if value == "@" or (value == ":" and "@" in host[pos:]):
                # this looks like an authority string
                extra = (
                    ", if the value includes a username or password, "
                    "use 'authority' instead of 'host'"
                )
            raise ValueError(
                f"Host {host!r} cannot contain {value!r} (at position {pos}){extra}"
            ) from None
        if "%" in host:
            return host, _whatwg_decoded_host(host), False
        return host, host and _whatwg_numeric_host(host), False

    # IDNA/UTS-46 mapping silently deletes default-ignorable code points, which
    # would turn e.g. ``e<ZWSP>vil.com`` into ``evil.com``, a different host
    # than the string the caller supplied. Reject them on every path (this runs
    # regardless of ``validate_host`` since the plain ``URL(str)`` constructor
    # encodes with ``validate_host=False``) so the parsed host cannot diverge
    # from the input, matching idna/httpx/urllib3.
    if invalid := _DEFAULT_IGNORABLE_RE.search(host):
        raise ValueError(
            f"Host {host!r} cannot contain {invalid.group()!r} "
            f"(at position {invalid.start()})"
        ) from None
    encoded, idna2003 = _idna_encode(host)
    # IDNA uses NFKC equivalence, so normalization can expand a non-ascii
    # character into an ASCII delimiter (e.g. the fullwidth solidus U+FF0F
    # becomes '/'). split_url's _check_netloc screens '/?#@:%' but not '[',
    # ']' or '\\', so a host like ``exa［mple`` (fullwidth '[') slips
    # through the parser and _idna_encode turns it into ``exa[mple``, a netloc
    # that str(url) then renders but yarl itself rejects on re-parse. Run the
    # check on every path (like the default-ignorable check above, which also
    # ignores validate_host) so the parsed host cannot diverge from what the
    # serialized URL means.
    if invalid := NOT_REG_NAME.search(encoded):
        raise ValueError(
            f"Host {host!r} cannot contain {invalid.group()!r} "
            f"after IDNA normalization to {encoded!r}"
        ) from None
    # The host can be percent-encoded next to the non-ASCII code points, or
    # IDNA can map a code point to "%", like the fullwidth percent sign
    # U+FF05, which WHATWG then rejects.
    if "%" in encoded:
        return encoded, _whatwg_decoded_host(host), idna2003
    return encoded, _whatwg_numeric_host(encoded), idna2003


@rewrite_module
def cache_clear() -> None:
    """Clear all LRU caches."""
    _idna_encode.cache_clear()
    _idna_decode.cache_clear()
    _encode_host.cache_clear()


@rewrite_module
def cache_info() -> CacheInfo:
    """Report cache statistics."""
    return {
        "idna_encode": _idna_encode.cache_info(),
        "idna_decode": _idna_decode.cache_info(),
        "ip_address": _encode_host.cache_info(),
        "host_validate": _encode_host.cache_info(),
        "encode_host": _encode_host.cache_info(),
    }


@rewrite_module
def cache_configure(
    *,
    idna_encode_size: int | None = _DEFAULT_IDNA_SIZE,
    idna_decode_size: int | None = _DEFAULT_IDNA_SIZE,
    ip_address_size: int | None | UndefinedType = UNDEFINED,
    host_validate_size: int | None | UndefinedType = UNDEFINED,
    encode_host_size: int | None | UndefinedType = UNDEFINED,
) -> None:
    """Configure LRU cache sizes."""
    global _idna_decode, _idna_encode, _encode_host
    # ip_address_size, host_validate_size are no longer
    # used, but are kept for backwards compatibility.
    if ip_address_size is not UNDEFINED or host_validate_size is not UNDEFINED:
        warnings.warn(
            "cache_configure() no longer accepts the "
            "ip_address_size or host_validate_size arguments, "
            "they are used to set the encode_host_size instead "
            "and will be removed in the future",
            DeprecationWarning,
            stacklevel=2,
        )

    if encode_host_size is not None:
        for size in (ip_address_size, host_validate_size):
            if size is None:
                encode_host_size = None
            elif encode_host_size is UNDEFINED:
                if size is not UNDEFINED:
                    encode_host_size = size
            elif size is not UNDEFINED:
                if TYPE_CHECKING:
                    assert isinstance(size, int)
                    assert isinstance(encode_host_size, int)
                encode_host_size = max(size, encode_host_size)
        if encode_host_size is UNDEFINED:
            encode_host_size = _DEFAULT_ENCODE_SIZE

    _encode_host = lru_cache(encode_host_size)(_encode_host.__wrapped__)
    _idna_decode = lru_cache(idna_decode_size)(_idna_decode.__wrapped__)
    _idna_encode = lru_cache(idna_encode_size)(_idna_encode.__wrapped__)
