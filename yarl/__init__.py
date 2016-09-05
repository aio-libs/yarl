from collections.abc import Mapping
from functools import partial
from ipaddress import ip_address
from urllib.parse import (SplitResult, parse_qsl,
                          urljoin, urlsplit, urlunsplit)

from multidict import MultiDict, MultiDictProxy


from .quoting import quote, unquote

__version__ = '0.0.1'

# Why not furl?
# Because I pretty sure URL class should be immutable
# but furl is a mutable class.


# is_leaf()
# path normalization


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

    __slots__ = ('_val', '_parts', '_query', '_hash')

    def __new__(cls, val='', *, encoded=False):
        if isinstance(val, URL):
            return val
        else:
            return super(URL, cls).__new__(cls)

    def __init__(self, val='', *, encoded=False):
        if isinstance(val, URL):
            return
        if isinstance(val, str):
            val = urlsplit(val)
        elif isinstance(val, SplitResult):
            if not encoded:
                raise ValueError("Cannot apply decoding to SplitResult")
        else:
            raise TypeError("Constructor parameter should be str")

        if not encoded:
            val = self._encode(val)

        self._val = val
        self._parts = None
        self._query = None
        self._hash = None

    @classmethod
    def _encode(cls, val):
        return val._replace(netloc=cls._encode_netloc(val),
                            path=cls._encode_path(val),
                            query=cls._encode_query(val),
                            fragment=cls._encode_fragment(val))

    @classmethod
    def _encode_netloc(cls, val):
        if not val.netloc:
            return ''
        ret = val.hostname
        try:
            ret.encode('ascii')
        except UnicodeEncodeError:
            ret = ret.encode('idna').decode('ascii')
        else:
            try:
                ip = ip_address(ret)
            except:
                pass
            else:
                if ip.version == 6:
                    ret = '['+ret+']'
        if val.port:
            ret += ':{}'.format(val.port)
        if val.username:
            user = quote(val.username)
            if val.password:
                user += ':' + quote(val.password)
            ret = user + '@' + ret
        return ret

    @classmethod
    def _encode_path(cls, val):
        return quote(val.path, safe='/')

    @classmethod
    def _encode_query(cls, val):
        return quote(val.query, safe='=+&', plus=True)

    @classmethod
    def _encode_fragment(cls, val):
        return quote(val.fragment)

    def __str__(self):
        val = self._val
        if not val.path and self.is_absolute() and (val.query or val.fragment):
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
        name = quote(name, safe='/')
        path = self._val.path
        if path == '/':
            new_path = '/' + name
        elif not path and not self.is_absolute():
            new_path = name
        else:
            parts = path.split('/')
            parts.append(name)
            new_path = '/'.join(parts)
        return URL(self._val._replace(path=new_path, query='', fragment=''),
                   encoded=True)

    def is_absolute(self):
        return self.raw_host is not None

    def origin(self):
        if not self.is_absolute():
            raise ValueError("URL should be absolute")
        if not self._val.scheme:
            raise ValueError("URL should have scheme")
        v = self._val
        netloc = self._make_netloc(None, None, v.hostname, v.port)
        val = v._replace(netloc=netloc, path='', query='', fragment='')
        return URL(val, encoded=True)

    @property
    def scheme(self):
        return self._val.scheme

    @property
    def raw_user(self):
        # not .username
        return self._val.username

    @property
    def user(self):
        return unquote(self.raw_user)

    @property
    def raw_password(self):
        return self._val.password

    @property
    def password(self):
        return unquote(self.raw_password)

    @property
    def raw_host(self):
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        return self._val.hostname

    @property
    def host(self):
        return self.raw_host.encode('ascii').decode('idna')

    @property
    def port(self):
        return self._val.port or DEFAULT_PORTS.get(self._val.scheme)

    @property
    def raw_path(self):
        ret = self._val.path
        if not ret and self.is_absolute():
            ret = '/'
        return ret

    @property
    def path(self):
        return unquote(self.raw_path)

    @property
    def query(self):
        if self._query is None:
            self._query = MultiDict(parse_qsl(self.query_string))
        return MultiDictProxy(self._query)

    @property
    def raw_query_string(self):
        return self._val.query

    @property
    def query_string(self):
        return unquote(self.raw_query_string)  # , safe='?&=+')

    @property
    def raw_fragment(self):
        return self._val.fragment

    @property
    def fragment(self):
        return unquote(self.raw_fragment)

    @property
    def raw_parts(self):
        if self._parts is None:
            path = self._val.path
            if self.is_absolute():
                if not path:
                    parts = ['/']
                else:
                    parts = ['/'] + path[1:].split('/')
            else:
                if path.startswith('/'):
                    parts = ['/'] + path[1:].split('/')
                else:
                    parts = path.split('/')
            self._parts = tuple(parts)
        return self._parts

    @property
    def parts(self):
        return tuple(unquote(part) for part in self.raw_parts)

    @property
    def parent(self):
        path = self.raw_path
        if not path or path == '/':
            if self.raw_fragment or self.raw_query_string:
                return URL(self._val._replace(query='', fragment=''),
                           encoded=True)
            return self
        parts = path.split('/')
        val = self._val._replace(path='/'.join(parts[:-1]),
                                 query='', fragment='')
        return URL(val, encoded=True)

    @property
    def raw_name(self):
        parts = self.raw_parts
        if self.is_absolute():
            parts = parts[1:]
            if not parts:
                return ''
            else:
                return parts[-1]
        else:
            return parts[-1]

    @property
    def name(self):
        return unquote(self.raw_name)

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
        if not self.is_absolute():
            raise ValueError("scheme replacement is not allowed "
                             "for relative URLs")
        return URL(self._val._replace(scheme=scheme.lower()),
                   encoded=True)

    def with_user(self, user):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(user, str):
            raise TypeError("Invalid user type")
        if not self.is_absolute():
            raise ValueError("user replacement is not allowed "
                             "for relative URLs")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(quote(user),
                                         val.password,
                                         val.hostname,
                                         val.port)),
            encoded=True)

    def with_password(self, password):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(password, str):
            raise TypeError("Invalid password type")
        if not self.is_absolute():
            raise ValueError("password replacement is not allowed "
                             "for relative URLs")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(val.username,
                                         quote(password),
                                         val.hostname,
                                         val.port)),
            encoded=True)

    def with_host(self, host):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(host, str):
            raise TypeError("Invalid host type")
        if not self.is_absolute():
            raise ValueError("host replacement is not allowed "
                             "for relative URLs")
        try:
            ip = ip_address(host)
        except:
            host = host.encode('idna').decode('ascii')
        else:
            if ip.version == 6:
                host = '['+host+']'
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(val.username,
                                                               val.password,
                                                               host,
                                                               val.port)),
                   encoded=True)

    def with_port(self, port):
        # N.B. doesn't cleanup query/fragment
        if port is not None and not isinstance(port, int):
            raise TypeError(
                "port should be int or None, got {}".format(type(port)))
        if not self.is_absolute():
            raise ValueError("port replacement is not allowed "
                             "for relative URLs")
        val = self._val
        return URL(self._val._replace(netloc=self._make_netloc(val.username,
                                                               val.password,
                                                               val.hostname,
                                                               port)),
                   encoded=True)

    def with_query(self, query):
        # N.B. doesn't cleanup query/fragment
        if isinstance(query, Mapping):
            quoter = partial(quote, safe='', plus=True)
            query = '&'.join(quoter(k)+'='+quoter(v)
                             for k, v in query.items())
        elif isinstance(query, str):
            query = quote(query, safe='=+&', plus=True)
        else:
            raise TypeError("Invalid query type")
        return URL(self._val._replace(query=query),
                   encoded=True)

    def with_fragment(self, fragment):
        # N.B. doesn't cleanup query/fragment
        if not isinstance(fragment, str):
            raise TypeError("Invalid fragment type")
        return URL(self._val._replace(fragment=quote(fragment)),
                   encoded=True)

    def with_name(self, name):
        # N.B. DOES cleanup query/fragment
        if not isinstance(name, str):
            raise TypeError("Invalid name type")
        if '/' in name:
            raise ValueError("Slash in name is not allowed")
        name = quote(name, safe='/')
        parts = list(self.raw_parts)
        if self.is_absolute():
            if len(parts) == 1:
                parts.append(name)
            else:
                parts[-1] = name
            parts[0] = ''  # replace leading '/'
        else:
            parts[-1] = name
            if parts[0] == '/':
                parts[0] = ''  # replace leading '/'
        return URL(self._val._replace(path='/'.join(parts),
                                      query='', fragment=''), encoded=True)

    def join(self, url):
        # See docs for urllib.parse.urljoin
        if not isinstance(url, URL):
            raise TypeError("url should be URL")
        return URL(urljoin(str(self), str(url)), encoded=True)

    def human(self):
        return
