import math
import sys
import warnings
from collections.abc import Mapping, Sequence
from contextlib import suppress
from functools import _CacheInfo, lru_cache
from ipaddress import ip_address
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    overload,
)
from urllib.parse import SplitResult, parse_qsl, quote, urljoin, urlsplit, urlunsplit

import idna
from multidict import MultiDict, MultiDictProxy

from ._helpers import cached_property
from ._quoting import _Quoter, _Unquoter

DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443}

sentinel = object()

_SimpleQuery = Union[str, int, float]
_QueryVariable = Union[_SimpleQuery, "Sequence[_SimpleQuery]"]
_Query = Union[
    None, str, "Mapping[str, _QueryVariable]", "Sequence[Tuple[str, _QueryVariable]]"
]
_T = TypeVar("_T")

if sys.version_info >= (3, 11):
    from typing import Self
else:
    Self = Any


class CacheInfo(TypedDict):
    """Host encoding cache."""

    idna_encode: _CacheInfo
    idna_decode: _CacheInfo
    ip_address: _CacheInfo


def rewrite_module(obj: _T) -> _T:
    obj.__module__ = "yarl"
    return obj


def _normalize_path_segments(segments: "Sequence[str]") -> List[str]:
    """Drop '.' and '..' from a sequence of str segments"""

    resolved_path: List[str] = []

    for seg in segments:
        if seg == "..":
            # ignore any .. segments that would otherwise cause an
            # IndexError when popped from resolved_path if
            # resolving for rfc3986
            with suppress(IndexError):
                resolved_path.pop()
        elif seg != ".":
            resolved_path.append(seg)

    if segments and segments[-1] in (".", ".."):
        # do some post-processing here.
        # if the last segment was a relative dir,
        # then we need to append the trailing '/'
        resolved_path.append("")

    return resolved_path


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
    __slots__ = ("_cache", "_val")

    _QUOTER = _Quoter(requote=False)
    _REQUOTER = _Quoter()
    _PATH_QUOTER = _Quoter(safe="@:", protected="/+", requote=False)
    _PATH_REQUOTER = _Quoter(safe="@:", protected="/+")
    _QUERY_QUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True, requote=False)
    _QUERY_REQUOTER = _Quoter(safe="?/:@", protected="=+&;", qs=True)
    _QUERY_PART_QUOTER = _Quoter(safe="?/:@", qs=True, requote=False)
    _FRAGMENT_QUOTER = _Quoter(safe="?/:@", requote=False)
    _FRAGMENT_REQUOTER = _Quoter(safe="?/:@")

    _UNQUOTER = _Unquoter()
    _PATH_UNQUOTER = _Unquoter(ignore="/", unsafe="+")
    _QS_UNQUOTER = _Unquoter(qs=True)

    _val: SplitResult

    def __new__(
        cls,
        val: Union[str, SplitResult, "URL"] = "",
        *,
        encoded: bool = False,
        strict: Optional[bool] = None,
    ) -> Self:
        if strict is not None:  # pragma: no cover
            warnings.warn("strict parameter is ignored")
        if type(val) is cls:
            return val
        if type(val) is str:
            val = urlsplit(val)
        elif type(val) is SplitResult:
            if not encoded:
                raise ValueError("Cannot apply decoding to SplitResult")
        elif isinstance(val, str):
            val = urlsplit(str(val))
        else:
            raise TypeError("Constructor parameter should be str")

        if not encoded:
            host: Optional[str]
            if not val[1]:  # netloc
                netloc = ""
                host = ""
            else:
                host = val.hostname
                if host is None:
                    raise ValueError("Invalid URL: host is required for absolute urls")

                try:
                    port = val.port
                except ValueError as e:
                    raise ValueError(
                        "Invalid URL: port can't be converted to integer"
                    ) from e

                netloc = cls._make_netloc(
                    val.username, val.password, host, port, encode=True, requote=True
                )
            path = cls._PATH_REQUOTER(val[2])
            if netloc:
                path = cls._normalize_path(path)

            cls._validate_authority_uri_abs_path(host=host, path=path)
            query = cls._QUERY_REQUOTER(val[3])
            fragment = cls._FRAGMENT_REQUOTER(val[4])
            val = SplitResult(val[0], netloc, path, query, fragment)

        self = object.__new__(cls)
        self._val = val
        self._cache = {}
        return self

    @classmethod
    def build(
        cls,
        *,
        scheme: str = "",
        authority: str = "",
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str = "",
        port: Optional[int] = None,
        path: str = "",
        query: Optional[_Query] = None,
        query_string: str = "",
        fragment: str = "",
        encoded: bool = False,
    ) -> "URL":
        """Creates and returns a new URL"""

        if authority and (user or password or host or port):
            raise ValueError(
                'Can\'t mix "authority" with "user", "password", "host" or "port".'
            )
        if not isinstance(port, (int, type(None))):
            raise TypeError("The port is required to be int.")
        if port and not host:
            raise ValueError('Can\'t build URL with "port" but without "host".')
        if query and query_string:
            raise ValueError('Only one of "query" or "query_string" should be passed')
        if (
            scheme is None
            or authority is None
            or host is None
            or path is None
            or query_string is None
            or fragment is None
        ):
            raise TypeError(
                'NoneType is illegal for "scheme", "authority", "host", "path", '
                '"query_string", and "fragment" args, use empty string instead.'
            )

        if authority:
            if encoded:
                netloc = authority
            else:
                tmp = SplitResult("", authority, "", "", "")
                netloc = cls._make_netloc(
                    tmp.username, tmp.password, tmp.hostname, tmp.port, encode=True
                )
        elif not user and not password and not host and not port:
            netloc = ""
        else:
            netloc = cls._make_netloc(
                user, password, host, port, encode=not encoded, encode_host=not encoded
            )
        if not encoded:
            path = cls._PATH_QUOTER(path)
            if netloc:
                path = cls._normalize_path(path)

            cls._validate_authority_uri_abs_path(host=host, path=path)
            query_string = cls._QUERY_QUOTER(query_string)
            fragment = cls._FRAGMENT_QUOTER(fragment)

        url = cls(
            SplitResult(scheme, netloc, path, query_string, fragment), encoded=True
        )

        if query:
            return url.with_query(query)
        else:
            return url

    def __init_subclass__(cls):
        raise TypeError(f"Inheriting a class {cls!r} from URL is forbidden")

    def __str__(self) -> str:
        val = self._val
        if not val.path and self.is_absolute() and (val.query or val.fragment):
            val = val._replace(path="/")
        if (port := self._port_not_default) is None:
            # port normalization - using None for default ports to remove from rendering
            # https://datatracker.ietf.org/doc/html/rfc3986.html#section-6.2.3
            val = val._replace(
                netloc=self._make_netloc(
                    self.raw_user,
                    self.raw_password,
                    self.raw_host,
                    port,
                    encode_host=False,
                )
            )
        return urlunsplit(val)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{str(self)}')"

    def __bytes__(self) -> bytes:
        return str(self).encode("ascii")

    def __eq__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented

        val1 = self._val
        if not val1.path and self.is_absolute():
            val1 = val1._replace(path="/")

        val2 = other._val
        if not val2.path and other.is_absolute():
            val2 = val2._replace(path="/")

        return val1 == val2

    def __hash__(self) -> int:
        ret = self._cache.get("hash")
        if ret is None:
            val = self._val
            if not val.path and self.is_absolute():
                val = val._replace(path="/")
            ret = self._cache["hash"] = hash(val)
        return ret

    def __le__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return self._val <= other._val

    def __lt__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return self._val < other._val

    def __ge__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return self._val >= other._val

    def __gt__(self, other: object) -> bool:
        if type(other) is not URL:
            return NotImplemented
        return self._val > other._val

    def __truediv__(self, name: str) -> "URL":
        if not isinstance(name, str):
            return NotImplemented
        return self._make_child((str(name),))

    def __mod__(self, query: _Query) -> "URL":
        return self.update_query(query)

    def __bool__(self) -> bool:
        return bool(
            self._val.netloc or self._val.path or self._val.query or self._val.fragment
        )

    def __getstate__(self) -> Tuple[SplitResult]:
        return (self._val,)

    def __setstate__(self, state):
        if state[0] is None and isinstance(state[1], dict):
            # default style pickle
            self._val = state[1]["_val"]
        else:
            self._val, *unused = state
        self._cache = {}

    def is_absolute(self) -> bool:
        """A check for absolute URLs.

        Return True for absolute ones (having scheme or starting
        with //), False otherwise.

        """
        return self.raw_host is not None

    def is_default_port(self) -> bool:
        """A check for default port.

        Return True if port is default for specified scheme,
        e.g. 'http://python.org' or 'http://python.org:80', False
        otherwise.

        Return False for relative URLs.

        """
        if self.explicit_port is None:
            # A relative URL does not have an implicit port / default port
            return self.port is not None
        default = self._default_port
        if default is None:
            return False
        return self.port == default

    def origin(self) -> "URL":
        """Return an URL with scheme, host and port parts only.

        user, password, path, query and fragment are removed.

        """
        # TODO: add a keyword-only option for keeping user/pass maybe?
        if not self.is_absolute():
            raise ValueError("URL should be absolute")
        if not self._val.scheme:
            raise ValueError("URL should have scheme")
        v = self._val
        netloc = self._make_netloc(None, None, v.hostname, v.port)
        val = v._replace(netloc=netloc, path="", query="", fragment="")
        return URL(val, encoded=True)

    def relative(self) -> "URL":
        """Return a relative part of the URL.

        scheme, user, password, host and port are removed.

        """
        if not self.is_absolute():
            raise ValueError("URL should be absolute")
        val = self._val._replace(scheme="", netloc="")
        return URL(val, encoded=True)

    @cached_property
    def scheme(self) -> str:
        """Scheme for absolute URLs.

        Empty string for relative URLs or URLs starting with //

        """
        return self._val.scheme

    @property
    def raw_authority(self) -> str:
        """Encoded authority part of URL.

        Empty string for relative URLs.

        """
        return self._val.netloc

    @cached_property
    def _default_port(self) -> Union[int, None]:
        """Default port for the scheme or None if not known."""
        scheme = self.scheme
        if not scheme:
            return None
        return DEFAULT_PORTS.get(scheme)

    @cached_property
    def _port_not_default(self) -> Union[int, None]:
        """The port part of URL normalized to None if its the default port."""
        port = self.port
        if self._default_port == port:
            return None
        return port

    @cached_property
    def authority(self) -> str:
        """Decoded authority part of URL.

        Empty string for relative URLs.

        """
        return self._make_netloc(
            self.user, self.password, self.host, self.port, encode_host=False
        )

    @property
    def raw_user(self) -> Optional[str]:
        """Encoded user part of URL.

        None if user is missing.

        """
        # not .username
        return self._val.username or None

    @cached_property
    def user(self) -> Optional[str]:
        """Decoded user part of URL.

        None if user is missing.

        """
        raw_user = self.raw_user
        if raw_user is None:
            return None
        return self._UNQUOTER(raw_user)

    @property
    def raw_password(self) -> Optional[str]:
        """Encoded password part of URL.

        None if password is missing.

        """
        return self._val.password

    @cached_property
    def password(self) -> Optional[str]:
        """Decoded password part of URL.

        None if password is missing.

        """
        raw_password = self.raw_password
        if raw_password is None:
            return None
        return self._UNQUOTER(raw_password)

    @cached_property
    def raw_host(self) -> Optional[str]:
        """Encoded host part of URL.

        None for relative URLs.

        """
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        return self._val.hostname

    @cached_property
    def host(self) -> Optional[str]:
        """Decoded host part of URL.

        None for relative URLs.

        """
        raw = self.raw_host
        if raw is None:
            return None
        if "%" in raw:
            # Hack for scoped IPv6 addresses like
            # fe80::2%Перевірка
            # presence of '%' sign means only IPv6 address, so idna is useless.
            return raw
        return _idna_decode(raw)

    @cached_property
    def port(self) -> Optional[int]:
        """Port part of URL, with scheme-based fallback.

        None for relative URLs or URLs without explicit port and
        scheme without default port substitution.

        """
        return self.explicit_port or self._default_port

    @cached_property
    def explicit_port(self) -> Optional[int]:
        """Port part of URL, without scheme-based fallback.

        None for relative URLs or URLs without explicit port.

        """
        return self._val.port

    @property
    def raw_path(self) -> str:
        """Encoded path of URL.

        / for absolute URLs without path part.

        """
        ret = self._val.path
        if not ret and self.is_absolute():
            ret = "/"
        return ret

    @cached_property
    def path(self) -> str:
        """Decoded path of URL.

        / for absolute URLs without path part.

        """
        return self._PATH_UNQUOTER(self.raw_path)

    @cached_property
    def query(self) -> MultiDictProxy[str]:
        """A MultiDictProxy representing parsed query parameters in decoded
        representation.

        Empty value if URL has no query part.

        """
        ret = MultiDict(parse_qsl(self.raw_query_string, keep_blank_values=True))
        return MultiDictProxy(ret)

    @property
    def raw_query_string(self) -> str:
        """Encoded query part of URL.

        Empty string if query is missing.

        """
        return self._val.query

    @cached_property
    def query_string(self) -> str:
        """Decoded query part of URL.

        Empty string if query is missing.

        """
        return self._QS_UNQUOTER(self.raw_query_string)

    @cached_property
    def path_qs(self) -> str:
        """Decoded path of URL with query."""
        if not self.query_string:
            return self.path
        return f"{self.path}?{self.query_string}"

    @cached_property
    def raw_path_qs(self) -> str:
        """Encoded path of URL with query."""
        if not self.raw_query_string:
            return self.raw_path
        return f"{self.raw_path}?{self.raw_query_string}"

    @property
    def raw_fragment(self) -> str:
        """Encoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return self._val.fragment

    @cached_property
    def fragment(self) -> str:
        """Decoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return self._UNQUOTER(self.raw_fragment)

    @cached_property
    def raw_parts(self) -> Tuple[str, ...]:
        """A tuple containing encoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
        path = self._val.path
        if self.is_absolute():
            if not path:
                parts = ["/"]
            else:
                parts = ["/"] + path[1:].split("/")
        else:
            if path.startswith("/"):
                parts = ["/"] + path[1:].split("/")
            else:
                parts = path.split("/")
        return tuple(parts)

    @cached_property
    def parts(self) -> Tuple[str, ...]:
        """A tuple containing decoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
        return tuple(self._UNQUOTER(part) for part in self.raw_parts)

    @cached_property
    def parent(self) -> "URL":
        """A new URL with last part of path removed and cleaned up query and
        fragment.

        """
        path = self.raw_path
        if not path or path == "/":
            if self.raw_fragment or self.raw_query_string:
                return URL(self._val._replace(query="", fragment=""), encoded=True)
            return self
        parts = path.split("/")
        val = self._val._replace(path="/".join(parts[:-1]), query="", fragment="")
        return URL(val, encoded=True)

    @cached_property
    def raw_name(self) -> str:
        """The last part of raw_parts."""
        parts = self.raw_parts
        if self.is_absolute():
            parts = parts[1:]
            if not parts:
                return ""
            else:
                return parts[-1]
        else:
            return parts[-1]

    @cached_property
    def name(self) -> str:
        """The last part of parts."""
        return self._UNQUOTER(self.raw_name)

    @cached_property
    def raw_suffix(self) -> str:
        name = self.raw_name
        i = name.rfind(".")
        if 0 < i < len(name) - 1:
            return name[i:]
        else:
            return ""

    @cached_property
    def suffix(self) -> str:
        return self._UNQUOTER(self.raw_suffix)

    @cached_property
    def raw_suffixes(self) -> Tuple[str, ...]:
        name = self.raw_name
        if name.endswith("."):
            return ()
        name = name.lstrip(".")
        return tuple("." + suffix for suffix in name.split(".")[1:])

    @cached_property
    def suffixes(self) -> Tuple[str, ...]:
        return tuple(self._UNQUOTER(suffix) for suffix in self.raw_suffixes)

    @staticmethod
    def _validate_authority_uri_abs_path(host: str, path: str) -> None:
        """Ensure that path in URL with authority starts with a leading slash.

        Raise ValueError if not.
        """
        if len(host) > 0 and len(path) > 0 and not path.startswith("/"):
            raise ValueError(
                "Path in a URL with authority should start with a slash ('/') if set"
            )

    def _make_child(self, paths: "Sequence[str]", encoded: bool = False) -> "URL":
        """
        add paths to self._val.path, accounting for absolute vs relative paths,
        keep existing, but do not create new, empty segments
        """
        parsed = []
        for idx, path in enumerate(reversed(paths)):
            # empty segment of last is not removed
            last = idx == 0
            if path and path[0] == "/":
                raise ValueError(
                    f"Appending path {path!r} starting from slash is forbidden"
                )
            path = path if encoded else self._PATH_QUOTER(path)
            segments = [
                segment for segment in reversed(path.split("/")) if segment != "."
            ]
            if not segments:
                continue
            # remove trailing empty segment for all but the last path
            segment_slice_start = int(not last and segments[0] == "")
            parsed += segments[segment_slice_start:]
        parsed.reverse()

        if self._val.path and (old_path_segments := self._val.path.split("/")):
            old_path_cutoff = -1 if old_path_segments[-1] == "" else None
            parsed = [*old_path_segments[:old_path_cutoff], *parsed]

        if self.is_absolute():
            parsed = _normalize_path_segments(parsed)
            if parsed and parsed[0] != "":
                # inject a leading slash when adding a path to an absolute URL
                # where there was none before
                parsed = ["", *parsed]
        new_path = "/".join(parsed)
        return URL(
            self._val._replace(path=new_path, query="", fragment=""), encoded=True
        )

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        # Drop '.' and '..' from str path

        prefix = ""
        if path.startswith("/"):
            # preserve the "/" root element of absolute paths, copying it to the
            # normalised output as per sections 5.2.4 and 6.2.2.3 of rfc3986.
            prefix = "/"
            path = path[1:]

        segments = path.split("/")
        return prefix + "/".join(_normalize_path_segments(segments))

    @classmethod
    def _encode_host(cls, host: str, human: bool = False) -> str:
        raw_ip, sep, zone = host.partition("%")
        # IP parsing is slow, so its wrapped in an LRU
        try:
            ip_compressed_version = _ip_compressed_version(raw_ip)
        except ValueError:
            host = host.lower()
            # IDNA encoding is slow,
            # skip it for ASCII-only strings
            # Don't move the check into _idna_encode() helper
            # to reduce the cache size
            if human or host.isascii():
                return host
            return _idna_encode(host)

        # These checks should not happen in the
        # LRU to keep the cache size small
        host, version = ip_compressed_version
        if sep:
            host += "%" + zone
        if version == 6:
            return f"[{host}]"
        return host

    @classmethod
    def _make_netloc(
        cls,
        user: Optional[str],
        password: Optional[str],
        host: Optional[str],
        port: Optional[int],
        encode: bool = False,
        encode_host: bool = True,
        requote: bool = False,
    ) -> str:
        if host is None:
            return ""
        quoter = cls._REQUOTER if requote else cls._QUOTER
        if encode_host:
            ret = cls._encode_host(host)
        else:
            ret = host
        if port is not None:
            ret = f"{ret}:{port}"
        if password is not None:
            if not user:
                user = ""
            else:
                if encode:
                    user = quoter(user)
            if encode:
                password = quoter(password)
            user = user + ":" + password
        elif user and encode:
            user = quoter(user)
        if user:
            ret = user + "@" + ret
        return ret

    def with_scheme(self, scheme: str) -> "URL":
        """Return a new URL with scheme replaced."""
        # N.B. doesn't cleanup query/fragment
        if not isinstance(scheme, str):
            raise TypeError("Invalid scheme type")
        if not self.is_absolute():
            raise ValueError("scheme replacement is not allowed for relative URLs")
        return URL(self._val._replace(scheme=scheme.lower()), encoded=True)

    def with_user(self, user: Optional[str]) -> "URL":
        """Return a new URL with user replaced.

        Autoencode user if needed.

        Clear user/password if user is None.

        """
        # N.B. doesn't cleanup query/fragment
        val = self._val
        if user is None:
            password = None
        elif isinstance(user, str):
            user = self._QUOTER(user)
            password = val.password
        else:
            raise TypeError("Invalid user type")
        if not self.is_absolute():
            raise ValueError("user replacement is not allowed for relative URLs")
        return URL(
            self._val._replace(
                netloc=self._make_netloc(user, password, val.hostname, val.port)
            ),
            encoded=True,
        )

    def with_password(self, password: Optional[str]) -> "URL":
        """Return a new URL with password replaced.

        Autoencode password if needed.

        Clear password if argument is None.

        """
        # N.B. doesn't cleanup query/fragment
        if password is None:
            pass
        elif isinstance(password, str):
            password = self._QUOTER(password)
        else:
            raise TypeError("Invalid password type")
        if not self.is_absolute():
            raise ValueError("password replacement is not allowed for relative URLs")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(val.username, password, val.hostname, val.port)
            ),
            encoded=True,
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
        if not self.is_absolute():
            raise ValueError("host replacement is not allowed for relative URLs")
        if not host:
            raise ValueError("host removing is not allowed")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(val.username, val.password, host, val.port)
            ),
            encoded=True,
        )

    def with_port(self, port: Optional[int]) -> "URL":
        """Return a new URL with port replaced.

        Clear port to default if None is passed.

        """
        # N.B. doesn't cleanup query/fragment
        if port is not None:
            if isinstance(port, bool) or not isinstance(port, int):
                raise TypeError(f"port should be int or None, got {type(port)}")
            if port < 0 or port > 65535:
                raise ValueError(f"port must be between 0 and 65535, got {port}")
        if not self.is_absolute():
            raise ValueError("port replacement is not allowed for relative URLs")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(val.username, val.password, val.hostname, port)
            ),
            encoded=True,
        )

    def with_path(self, path: str, *, encoded: bool = False) -> "URL":
        """Return a new URL with path replaced."""
        if not encoded:
            path = self._PATH_QUOTER(path)
            if self.is_absolute():
                path = self._normalize_path(path)
        if len(path) > 0 and path[0] != "/":
            path = "/" + path
        return URL(self._val._replace(path=path, query="", fragment=""), encoded=True)

    @classmethod
    def _query_seq_pairs(
        cls, quoter: Callable[[str], str], pairs: Iterable[Tuple[str, _QueryVariable]]
    ) -> Iterator[str]:
        for key, val in pairs:
            if isinstance(val, (list, tuple)):
                for v in val:
                    yield quoter(key) + "=" + quoter(cls._query_var(v))
            else:
                yield quoter(key) + "=" + quoter(cls._query_var(val))

    @staticmethod
    def _query_var(v: _QueryVariable) -> str:
        cls = type(v)
        if issubclass(cls, str):
            if TYPE_CHECKING:
                assert isinstance(v, str)
            return v
        if issubclass(cls, float):
            if TYPE_CHECKING:
                assert isinstance(v, float)
            if math.isinf(v):
                raise ValueError("float('inf') is not supported")
            if math.isnan(v):
                raise ValueError("float('nan') is not supported")
            return str(float(v))
        if issubclass(cls, int) and cls is not bool:
            if TYPE_CHECKING:
                assert isinstance(v, int)
            return str(int(v))
        raise TypeError(
            "Invalid variable type: value "
            "should be str, int or float, got {!r} "
            "of type {}".format(v, cls)
        )

    def _get_str_query(self, *args: Any, **kwargs: Any) -> Optional[str]:
        query: Optional[Union[str, Mapping[str, _QueryVariable]]]
        if kwargs:
            if len(args) > 0:
                raise ValueError(
                    "Either kwargs or single query parameter must be present"
                )
            query = kwargs
        elif len(args) == 1:
            query = args[0]
        else:
            raise ValueError("Either kwargs or single query parameter must be present")

        if query is None:
            query = None
        elif isinstance(query, Mapping):
            quoter = self._QUERY_PART_QUOTER
            query = "&".join(self._query_seq_pairs(quoter, query.items()))
        elif isinstance(query, str):
            query = self._QUERY_QUOTER(query)
        elif isinstance(query, (bytes, bytearray, memoryview)):
            raise TypeError(
                "Invalid query type: bytes, bytearray and memoryview are forbidden"
            )
        elif isinstance(query, Sequence):
            quoter = self._QUERY_PART_QUOTER
            # We don't expect sequence values if we're given a list of pairs
            # already; only mappings like builtin `dict` which can't have the
            # same key pointing to multiple values are allowed to use
            # `_query_seq_pairs`.
            query = "&".join(
                quoter(k) + "=" + quoter(self._query_var(v)) for k, v in query
            )
        else:
            raise TypeError(
                "Invalid query type: only str, mapping or "
                "sequence of (key, value) pairs is allowed"
            )

        return query

    @overload
    def with_query(self, query: _Query) -> "URL": ...

    @overload
    def with_query(self, **kwargs: _QueryVariable) -> "URL": ...

    def with_query(self, *args: Any, **kwargs: Any) -> "URL":
        """Return a new URL with query part replaced.

        Accepts any Mapping (e.g. dict, multidict.MultiDict instances)
        or str, autoencode the argument if needed.

        A sequence of (key, value) pairs is supported as well.

        It also can take an arbitrary number of keyword arguments.

        Clear query if None is passed.

        """
        # N.B. doesn't cleanup query/fragment

        new_query = self._get_str_query(*args, **kwargs) or ""
        return URL(
            self._val._replace(path=self._val.path, query=new_query), encoded=True
        )

    @overload
    def update_query(self, query: _Query) -> "URL": ...

    @overload
    def update_query(self, **kwargs: _QueryVariable) -> "URL": ...

    def update_query(self, *args: Any, **kwargs: Any) -> "URL":
        """Return a new URL with query part updated."""
        s = self._get_str_query(*args, **kwargs)
        query = None
        if s is not None:
            new_query = MultiDict(parse_qsl(s, keep_blank_values=True))
            query = MultiDict(self.query)
            query.update(new_query)

        return URL(
            self._val._replace(query=self._get_str_query(query) or ""), encoded=True
        )

    def with_fragment(self, fragment: Optional[str]) -> "URL":
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
            raw_fragment = self._FRAGMENT_QUOTER(fragment)
        if self.raw_fragment == raw_fragment:
            return self
        return URL(self._val._replace(fragment=raw_fragment), encoded=True)

    def with_name(self, name: str) -> "URL":
        """Return a new URL with name (last part of path) replaced.

        Query and fragment parts are cleaned up.

        Name is encoded if needed.

        """
        # N.B. DOES cleanup query/fragment
        if not isinstance(name, str):
            raise TypeError("Invalid name type")
        if "/" in name:
            raise ValueError("Slash in name is not allowed")
        name = self._PATH_QUOTER(name)
        if name in (".", ".."):
            raise ValueError(". and .. values are forbidden")
        parts = list(self.raw_parts)
        if self.is_absolute():
            if len(parts) == 1:
                parts.append(name)
            else:
                parts[-1] = name
            parts[0] = ""  # replace leading '/'
        else:
            parts[-1] = name
            if parts[0] == "/":
                parts[0] = ""  # replace leading '/'
        return URL(
            self._val._replace(path="/".join(parts), query="", fragment=""),
            encoded=True,
        )

    def with_suffix(self, suffix: str) -> "URL":
        """Return a new URL with suffix (file extension of name) replaced.

        Query and fragment parts are cleaned up.

        suffix is encoded if needed.
        """
        if not isinstance(suffix, str):
            raise TypeError("Invalid suffix type")
        if suffix and not suffix.startswith(".") or suffix == ".":
            raise ValueError(f"Invalid suffix {suffix!r}")
        name = self.raw_name
        if not name:
            raise ValueError(f"{self!r} has an empty name")
        old_suffix = self.raw_suffix
        if not old_suffix:
            name = name + suffix
        else:
            name = name[: -len(old_suffix)] + suffix
        return self.with_name(name)

    def join(self, url: "URL") -> "URL":
        """Join URLs

        Construct a full (“absolute”) URL by combining a “base URL”
        (self) with another URL (url).

        Informally, this uses components of the base URL, in
        particular the addressing scheme, the network location and
        (part of) the path, to provide missing components in the
        relative URL.

        """
        # See docs for urllib.parse.urljoin
        if not isinstance(url, URL):
            raise TypeError("url should be URL")
        return URL(urljoin(str(self), str(url)), encoded=True)

    def joinpath(self, *other: str, encoded: bool = False) -> "URL":
        """Return a new URL with the elements in other appended to the path."""
        return self._make_child(other, encoded=encoded)

    def human_repr(self) -> str:
        """Return decoded human readable string for URL representation."""
        user = _human_quote(self.user, "#/:?@[]")
        password = _human_quote(self.password, "#/:?@[]")
        host = self.host
        if host:
            host = self._encode_host(host, human=True)
        path = _human_quote(self.path, "#?")
        if TYPE_CHECKING:
            assert path is not None
        query_string = "&".join(
            "{}={}".format(_human_quote(k, "#&+;="), _human_quote(v, "#&+;="))
            for k, v in self.query.items()
        )
        fragment = _human_quote(self.fragment, "")
        if TYPE_CHECKING:
            assert fragment is not None
        netloc = self._make_netloc(
            user, password, host, self.explicit_port, encode_host=False
        )
        val = SplitResult(self.scheme, netloc, path, query_string, fragment)
        return urlunsplit(val)


def _human_quote(s: Optional[str], unsafe: str) -> Optional[str]:
    if not s:
        return s
    for c in "%" + unsafe:
        if c in s:
            s = s.replace(c, f"%{ord(c):02X}")
    if s.isprintable():
        return s
    return "".join(c if c.isprintable() else quote(c) for c in s)


_MAXCACHE = 256


@lru_cache(_MAXCACHE)
def _idna_decode(raw: str) -> str:
    try:
        return idna.decode(raw.encode("ascii"))
    except UnicodeError:  # e.g. '::1'
        return raw.encode("ascii").decode("idna")


@lru_cache(_MAXCACHE)
def _idna_encode(host: str) -> str:
    try:
        return idna.encode(host, uts46=True).decode("ascii")
    except UnicodeError:
        return host.encode("idna").decode("ascii")


@lru_cache(_MAXCACHE)
def _ip_compressed_version(raw_ip: str) -> Tuple[str, int]:
    """Return compressed version of IP address and its version."""
    ip = ip_address(raw_ip)
    return ip.compressed, ip.version


@rewrite_module
def cache_clear() -> None:
    """Clear all LRU caches."""
    _idna_decode.cache_clear()
    _idna_encode.cache_clear()
    _ip_compressed_version.cache_clear()


@rewrite_module
def cache_info() -> CacheInfo:
    """Report cache statistics."""
    return {
        "idna_encode": _idna_encode.cache_info(),
        "idna_decode": _idna_decode.cache_info(),
        "ip_address": _ip_compressed_version.cache_info(),
    }


@rewrite_module
def cache_configure(
    *,
    idna_encode_size: Optional[int] = _MAXCACHE,
    idna_decode_size: Optional[int] = _MAXCACHE,
    ip_address_size: Optional[int] = _MAXCACHE,
) -> None:
    """Configure LRU cache sizes."""
    global _idna_decode, _idna_encode, _ip_compressed_version

    _idna_encode = lru_cache(idna_encode_size)(_idna_encode.__wrapped__)
    _idna_decode = lru_cache(idna_decode_size)(_idna_decode.__wrapped__)
    _ip_compressed_version = lru_cache(ip_address_size)(
        _ip_compressed_version.__wrapped__
    )
