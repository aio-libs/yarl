from collections.abc import Mapping, Sequence
from functools import partial
from ipaddress import ip_address
from urllib.parse import (SplitResult, parse_qsl,
                          urljoin, urlsplit, urlunsplit)

from multidict import MultiDict, MultiDictProxy


from .quoting import quote, unquote

__version__ = '0.5.3'

__all__ = ['URL', 'quote', 'unquote']


# is_leaf()
# path normalization


DEFAULT_PORTS = {
    'http': 80,
    'https': 443,
    'ws': 80,
    'wss': 443,
}


sentinel = object()


class cached_property:
    """Use as a class method decorator.  It operates almost exactly like
    the Python `@property` decorator, but it puts the result of the
    method it decorates into the instance dict after the first call,
    effectively replacing the function it decorates with an instance
    variable.  It is, in Python parlance, a data descriptor.

    """

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except:  # pragma: no cover
            self.__doc__ = ""
        self.name = wrapped.__name__

    def __get__(self, inst, owner, _sentinel=sentinel):
        if inst is None:
            return self
        val = inst._cache.get(self.name, _sentinel)
        if val is not _sentinel:
            return val
        val = self.wrapped(inst)
        inst._cache[self.name] = val
        return val

    def __set__(self, inst, value):
        raise AttributeError("cached property is read-only")


class URL:
    # don't derive from str
    # follow pathlib.Path design
    # probably URL will not suffer from pathlib problems:
    # it's intended for libraries like aiohttp,
    # not to be passed into standard library functions like os.open etc.

    __slots__ = ('_cache', '_val')

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
            if not val[1]:  # netloc
                netloc = ''
            else:
                netloc = val.hostname
                if netloc is None:
                    raise ValueError(
                        "Invalid URL: host is required for abolute urls.")
                try:
                    netloc.encode('ascii')
                except UnicodeEncodeError:
                    netloc = netloc.encode('idna').decode('ascii')
                else:
                    try:
                        ip = ip_address(netloc)
                    except:
                        pass
                    else:
                        if ip.version == 6:
                            netloc = '['+netloc+']'
                if val.port:
                    netloc += ':{}'.format(val.port)
                if val.username:
                    user = quote(val.username)
                    if val.password:
                        user += ':' + quote(val.password)
                    netloc = user + '@' + netloc

            val = SplitResult(val[0],  # scheme
                              netloc,
                              quote(val[2], safe='/'),
                              query=quote(val[3], safe='=+&', plus=True),
                              fragment=quote(val[4]))

        self._val = val
        self._cache = {}

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
        ret = self._cache.get('hash')
        if ret is None:
            ret = self._cache['hash'] = hash(self._val)
        return ret

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
        if name.startswith('/'):
            raise ValueError("Appending path "
                             "starting from slash is forbidden")
        path = self._val.path
        if path == '/':
            new_path = '/' + name
        elif not path and not self.is_absolute():
            new_path = name
        else:
            parts = path.rstrip('/').split('/')
            parts.append(name)
            new_path = '/'.join(parts)
        return URL(self._val._replace(path=new_path, query='', fragment=''),
                   encoded=True)

    def is_absolute(self):
        """A check for absolute URLs.

        Return True for absolute ones (having scheme or starting
        with //), False otherwise.

        """
        return self.raw_host is not None

    def is_default_port(self):
        """A check for default port.

        Return True if port is default for specified scheme,
        e.g. 'http://python.org' or 'http://python.org:80', False
        otherwise.

        """
        if self.port is None:
            return False
        default = DEFAULT_PORTS.get(self.scheme)
        if default is None:
            return False
        return self.port == default

    def origin(self):
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
        val = v._replace(netloc=netloc, path='', query='', fragment='')
        return URL(val, encoded=True)

    def relative(self):
        """Return a relative part of the URL.

        scheme, user, password, host and port are removed.

        """
        if not self.is_absolute():
            raise ValueError("URL should be absolute")
        val = self._val._replace(scheme='', netloc='')
        return URL(val, encoded=True)

    @cached_property
    def scheme(self):
        """Scheme for absolute URLs.

        Empty string for relative URLs or URLs starting with //

        """
        return self._val.scheme

    @cached_property
    def raw_user(self):
        """Encoded user part of URL.

        None if user is missing.

        """
        # not .username
        return self._val.username

    @cached_property
    def user(self):
        """Decoded user part of URL.

        None if user is missing.

        """
        return unquote(self.raw_user)

    @cached_property
    def raw_password(self):
        """Encoded password part of URL.

        None if password is missing.

        """
        return self._val.password

    @cached_property
    def password(self):
        """Decoded password part of URL.

        None if password is missing.

        """
        return unquote(self.raw_password)

    @cached_property
    def raw_host(self):
        """Encoded host part of URL.

        None for relative URLs.

        """
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        return self._val.hostname

    @cached_property
    def host(self):
        """Decoded host part of URL.

        None for relative URLs.

        """
        raw = self.raw_host
        if raw is None:
            return None
        return raw.encode('ascii').decode('idna')

    @cached_property
    def port(self):
        """Port part of URL.

        None for relative URLs or URLs without explicit port and
        scheme without default port substitution.

        """
        return self._val.port or DEFAULT_PORTS.get(self._val.scheme)

    @cached_property
    def raw_path(self):
        """Encoded path of URL.

        / for absolute URLs without path part.

        """
        ret = self._val.path
        if not ret and self.is_absolute():
            ret = '/'
        return ret

    @cached_property
    def path(self):
        """Decoded path of URL.

        / for absolute URLs without path part.

        """
        return unquote(self.raw_path)

    @cached_property
    def query(self):
        """A MultiDictProxy representing parsed query parameters in decoded
        representation.

        Empty value if URL has no query part.

        """
        ret = MultiDict(parse_qsl(self.query_string, keep_blank_values=True))
        return MultiDictProxy(ret)

    @cached_property
    def raw_query_string(self):
        """Encoded query part of URL.

        Empty string if query is missing.

        """
        return self._val.query

    @cached_property
    def query_string(self):
        """Decoded query part of URL.

        Empty string if query is missing.

        """
        return unquote(self.raw_query_string, unsafe='?&=+')

    @cached_property
    def raw_fragment(self):
        """Encoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return self._val.fragment

    @cached_property
    def fragment(self):
        """Decoded fragment part of URL.

        Empty string if fragment is missing.

        """
        return unquote(self.raw_fragment)

    @cached_property
    def raw_parts(self):
        """A tuple containing encoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
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
        return tuple(parts)

    @cached_property
    def parts(self):
        """A tuple containing decoded *path* parts.

        ('/',) for absolute URLs if *path* is missing.

        """
        return tuple(unquote(part) for part in self.raw_parts)

    @cached_property
    def parent(self):
        """A new URL with last part of path removed and cleaned up query and
        fragment.

        """
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

    @cached_property
    def raw_name(self):
        """The last part of raw_parts."""
        parts = self.raw_parts
        if self.is_absolute():
            parts = parts[1:]
            if not parts:
                return ''
            else:
                return parts[-1]
        else:
            return parts[-1]

    @cached_property
    def name(self):
        """The last part of parts."""
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
        """Return a new URL with scheme replaced."""
        # N.B. doesn't cleanup query/fragment
        if not isinstance(scheme, str):
            raise TypeError("Invalid scheme type")
        if not self.is_absolute():
            raise ValueError("scheme replacement is not allowed "
                             "for relative URLs")
        return URL(self._val._replace(scheme=scheme.lower()),
                   encoded=True)

    def with_user(self, user):
        """Return a new URL with user replaced.

        Autoencode user if needed.

        Clear user/password if user is None.

        """
        # N.B. doesn't cleanup query/fragment
        val = self._val
        if user is None:
            password = None
        elif isinstance(user, str):
            user = quote(user)
            password = val.password
        else:
            raise TypeError("Invalid user type")
        if not self.is_absolute():
            raise ValueError("user replacement is not allowed "
                             "for relative URLs")
        return URL(
            self._val._replace(
                netloc=self._make_netloc(user,
                                         password,
                                         val.hostname,
                                         val.port)),
            encoded=True)

    def with_password(self, password):
        """Return a new URL with password replaced.

        Autoencode password if needed.

        Clear password if argument is None.

        """
        # N.B. doesn't cleanup query/fragment
        if password is None:
            pass
        elif isinstance(password, str):
            password = quote(password)
        else:
            raise TypeError("Invalid password type")
        if not self.is_absolute():
            raise ValueError("password replacement is not allowed "
                             "for relative URLs")
        val = self._val
        return URL(
            self._val._replace(
                netloc=self._make_netloc(val.username,
                                         password,
                                         val.hostname,
                                         val.port)),
            encoded=True)

    def with_host(self, host):
        """Return a new URL with host replaced.

        Autoencode host if needed.

        Changing host for relative URLs is not allowed, use .join()
        instead.

        """
        # N.B. doesn't cleanup query/fragment
        if not isinstance(host, str):
            raise TypeError("Invalid host type")
        if not self.is_absolute():
            raise ValueError("host replacement is not allowed "
                             "for relative URLs")
        if not host:
            raise ValueError("host removing is not allowed")
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
        """Return a new URL with port replaced.

        Clear port to default if None is passed.

        """
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

    def with_query(self, *args, **kwargs):
        """Return a new URL with query part replaced.

        Accepts any Mapping (e.g. dict, multidict.MultiDict instances)
        or str, autoencode the argument if needed.

        It also can take an arbitrary number of keyword arguments.

        Clear query if None is passed.

        """
        # N.B. doesn't cleanup query/fragment

        if kwargs:
            if len(args) > 0:
                raise ValueError("Either kwargs or single query parameter "
                                 "must be present")
            query = kwargs
            for _, value in kwargs.items():
                if not isinstance(value, str):
                    raise TypeError("Invalid variable type")
        elif len(args) == 1:
            query = args[0]
        else:
            raise ValueError("Either kwargs or single query parameter "
                             "must be present")

        if query is None:
            query = ''
        elif isinstance(query, Mapping):
            quoter = partial(quote, safe='', plus=True)
            query = '&'.join(quoter(k)+'='+quoter(v)
                             for k, v in query.items())
        elif isinstance(query, str):
            query = quote(query, safe='=+&', plus=True)
        elif isinstance(query, (bytes, bytearray, memoryview)):
            raise TypeError("Invalid query type")
        elif isinstance(query, Sequence):
            quoter = partial(quote, safe='', plus=True)
            query = '&'.join(quoter(k)+'='+quoter(v)
                             for k, v in query)
        else:
            raise TypeError("Invalid query type")
        return URL(self._val._replace(query=query),
                   encoded=True)

    def with_fragment(self, fragment):
        """Return a new URL with fragment replaced.

        Autoencode fragment if needed.

        Clear fragment to default if None is passed.

        """
        # N.B. doesn't cleanup query/fragment
        if fragment is None:
            fragment = ''
        elif not isinstance(fragment, str):
            raise TypeError("Invalid fragment type")
        return URL(self._val._replace(fragment=quote(fragment)),
                   encoded=True)

    def with_name(self, name):
        """Return a new URL with name (last part of path) replaced.

        Query and fragment parts are cleaned up.

        Name is encoded if needed.

        """
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

    def human_repr(self):
        """Return decoded human readable string for URL representation."""

        return urlunsplit(SplitResult(self.scheme,
                                      self._make_netloc(self.user,
                                                        self.password,
                                                        self.host,
                                                        self._val.port),
                                      self.path,
                                      self.query_string,
                                      self.fragment))
