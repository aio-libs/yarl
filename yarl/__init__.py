from collections.abc import Mapping
from urllib.parse import (SplitResult, SplitResultBytes, parse_qsl, quote,
                          unquote, urlencode, urlsplit, urlunsplit)

from multidict import MultiDict, MultiDictProxy

__version__ = '0.0.1'

# Why not furl?
# Because I pretty sure URL class should be immutable
# but furl is a mutable class.


DEFAULT_PORTS = {
    'http': 80,
    'https': 443,
    'ws': 80,
    'wss': 443,
}


class URL:
    # don't derive from str
    # follow pathlib.Path design
    # probably URL will not suffer from pathlib problems:
    # it's intended for libraries like aiohttp,
    # not to be passed into standard library functions like os.open etc.

    __slots__ = ('_val', '_path', '_query', '_hash')

    def __init__(self, val):
        if isinstance(val, str):
            self._val = urlsplit(val)
        elif isinstance(val, SplitResult):
            self._val = val
        else:
            raise TypeError("Constructor parameter should be "
                            "either URL or str")
        self._path = None
        self._query = None
        self._hash = None

    @classmethod
    def from_bytes(cls, bval):
        if isinstance(bval, memoryview):
            bval = bytes(bval)
        if not isinstance(bval, (bytes, bytearray)):
            raise TypeError("Parameter should be byte-ish")
        bval = urlsplit(bval)
        val = SplitResult(scheme=bval.scheme.decode('ascii'),
                          netloc=cls._decode_netloc(bval),
                          path=cls._decode_path(bval),
                          query=cls._decode_query(bval),
                          fragment=cls._decode_fragment(bval))
        return URL(val)

    @classmethod
    def _decode_netloc(cls, bval):
        ret = bval.hostname.decode('idna')
        if bval.port:
            ret += ":%d" % bval.port
        if bval.username:
            user = unquote(bval.username.decode('ascii'))
            if bval.password:
                user += ':' + unquote(bval.password.decode('ascii'))
            ret = user + '@' + ret
        return ret

    @classmethod
    def _decode_path(cls, bval):
        return unquote(bval.path.decode('ascii'))  # add a check for %2F

    @classmethod
    def _decode_query(cls, bval):
        # add a check for %26 and %3d
        lst = parse_qsl(bval.query.decode('ascii'))
        return '&'.join('{}={}'.format(k, v) for k, v in lst)

    @classmethod
    def _decode_fragment(cls, bval):
        return unquote(bval.fragment.decode('ascii'))

    @classmethod
    def _encode_netloc(cls, val):
        ret = val.hostname.encode('idna')
        if val.port:
            ret += ':{}'.format(val.port).encode('ascii')
        if val.username:
            buser = quote(val.username).encode('ascii')
            if val.password:
                buser += b':' + quote(val.password).encode('ascii')
            ret = buser + b'@' + ret
        return ret

    @classmethod
    def _encode_path(cls, val):
        return quote(val.path).encode('ascii')

    @classmethod
    def _encode_query(cls, query):
        return urlencode(query).encode('ascii')

    @classmethod
    def _encode_fragment(cls, val):
        return quote(val.fragment).encode('ascii')

    def __str__(self):
        val = self._val
        if not val.path and (val.query or val.fragment):
            val = val._replace(path='/')
        return urlunsplit(val)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, str(self))

    def __eq__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self._val == other._val

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self._val)
        return self._hash

    def __le__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self._val <= other._val

    def __lt__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self._val < other._val

    def __ge__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self._val >= other._val

    def __gt__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self._val > other._val

    def __truediv__(self, name):
        path = self._val.path
        if path == '/':
            new_path = '/' + name
        else:
            parts = path.split('/')
            parts.append(name)
            new_path = '/'.join(parts)
        return URL(self._val._replace(path=new_path, query='', fragment=''))

    def __bytes__(self):
        val = self._val
        return urlunsplit(SplitResultBytes(
            self.scheme.encode('ascii'),
            self._encode_netloc(val),
            self._encode_path(val),
            self._encode_query(self.query),
            self._encode_fragment(val),
            ))

    def canonical(self):
        return bytes(self).decode('ascii')

    @property
    def scheme(self):
        return self._val.scheme

    @property
    def user(self):
        # not .username
        return self._val.username

    @property
    def password(self):
        return self._val.password

    @property
    def host(self):
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        return self._val.hostname

    @property
    def port(self):
        return self._val.port or DEFAULT_PORTS.get(self._val.scheme)

    @property
    def path(self):
        if self._path is None:
            self._path = tuple(self._val.path.split('/'))
        return self._path

    @property
    def path_string(self):
        return self._val.path

    @property
    def query(self):
        if self._query is None:
            self._query = MultiDict(parse_qsl(self._val.query))
        return MultiDictProxy(self._query)

    @property
    def query_string(self):
        return self._val.query

    @property
    def fragment(self):
        return self._val.fragment

    @property
    def parent(self):
        path = self.path_string
        if path == '/':
            if self.fragment or self.query:
                return URL(self._val._replace(query='', fragment=''))
            return self
        parts = path.split('/')
        val = self._val._replace(path='/'.join(parts[:-1]),
                                 query='', fragment='')
        return URL(val)

    @property
    def name(self):
        path = self.path_string
        if path == '/':
            return ''
        else:
            parts = path.split('/')
            return parts[-1]

    @classmethod
    def _make_netloc(cls, user, password, host, port):
        ret = host
        if port:
            ret = ret + ':' + str(port)
        if password:
            if not user:
                raise ValueError("Non-empty password requires non-empty user")
            user = user + ':' + password
        if user:
            ret = user + '@' + ret
        return ret

    def with_scheme(self, scheme):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(scheme, str):
            raise TypeError("Invalid scheme type")
        return URL(self._val._replace(scheme=scheme))

    def with_user(self, user):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(user, str):
            raise TypeError("Invalid user type")
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(user,
                                                               val.password,
                                                               val.hostname,
                                                               val.port)))

    def with_password(self, password):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(password, str):
            raise TypeError("Invalid password type")
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(val.username,
                                                               password,
                                                               val.hostname,
                                                               val.port)))

    def with_host(self, host):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(host, str):
            raise TypeError("Invalid host type")
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(val.username,
                                                               val.password,
                                                               host,
                                                               val.port)))

    def with_port(self, port):
        # N.B. doesn't cleanup query/fragment
        if port is not None and not isinstance(port, int):
            raise TypeError(
                "port should be int or None, got {}".format(type(port)))
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(val.username,
                                                               val.password,
                                                               val.hostname,
                                                               port)))

    def with_path(self, path):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(path, str):
            raise TypeError("Invalid path type")
        return URL(self._val._replace(path=path))

    def with_query(self, query):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(query, Mapping):
            raise TypeError("Invalid query type")
        return URL(self._val._replace(
            query='&'.join(str(k)+'='+str(v)
                           for k, v in query.items())))

    def with_fragment(self, fragment):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(fragment, str):
            raise TypeError("Invalid fragment type")
        return URL(self._val._replace(fragment=fragment))
